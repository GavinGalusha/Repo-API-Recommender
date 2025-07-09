#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Repo-API-Recommender – batch-capable version
-------------------------------------------
• Keeps all previous single-item behaviour
• New flag --list_file <path> (newline-separated descriptions)
• Re-uses loaded models for every item so VRAM stays constant
• Writes every result to output.txt with a clear separator
"""

import json
import argparse
import chromadb
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.web_search import search_for_microservice
from utils.helpers import (
    find_similar_apis,
    parse_rag_response,
    generate_text,
    generate_internal_prompt_blocks,
)
from utils.prompts import (
    create_implementation_prompt,
    create_merger_prompt,
    create_project_summary_prompt,
)
from walker import read_and_check_file, walk_repo

# -----------------------------------------------------------
# 1. CLI
# -----------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--repo_path", type=str)
parser.add_argument("--file_path", type=str)
parser.add_argument("--list_file", type=str, help="Plain-text file – one API description per line")
parser.add_argument("--ensemble", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--description", action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

# Convenience flags
ensemble = args.ensemble
repo_path = args.repo_path
file_path = args.file_path
list_file = args.list_file
description_condition = args.description

# -----------------------------------------------------------
# 2. Gather *all* API summaries we need to process
# -----------------------------------------------------------
api_summaries: list[str] = []

if list_file:  # → batch mode
    lines = Path(list_file).read_text(encoding="utf-8").splitlines()
    api_summaries = [ln.strip() for ln in lines if ln.strip()]
    if not api_summaries:
        raise ValueError(f"{list_file} is empty.")
else:  # → single-item mode (existing pathways)
    if repo_path:
        results = walk_repo(repo_path)
        summaries = []
        for r in results:
            try:
                entry = json.loads(r)
                summaries.append(entry["endpoints"]["api_summary"])
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Skipping entry: {e}")
        joined = "\n".join(summaries) if summaries else "No REST APIs were found in this repo"
        api_summaries.append(joined)

    elif file_path:
        result = read_and_check_file(file_path)
        summary = result["endpoints"]["api_summary"] if result else "No REST API found in this file."
        api_summaries.append(summary)

    elif description_condition:
        api_summaries.append(input("Describe an API in plain text: "))
    else:
        raise ValueError("Provide --repo_path, --file_path, --description, or --list_file.")

# -----------------------------------------------------------
# 3. Shared resources (load once)
# -----------------------------------------------------------
chroma_client = chromadb.PersistentClient(
    path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma"
)
collection = chroma_client.get_or_create_collection(name="microservice_descriptions")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# --- base model (always required)
mistral_tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
mistral_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.float16, device_map="auto"
)

# --- ensemble models (optional)
if ensemble:
    llama_tokenizer = AutoTokenizer.from_pretrained("NousResearch/Hermes-2-Pro-Llama-3-8B")
    llama_model = AutoModelForCausalLM.from_pretrained(
        "NousResearch/Hermes-2-Pro-Llama-3-8B", torch_dtype=torch.float16, device_map="auto"
    )

    merger_tokenizer = AutoTokenizer.from_pretrained("NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO")
    merger_model = AutoModelForCausalLM.from_pretrained(
        "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", torch_dtype=torch.float16, device_map="auto"
    )

# -----------------------------------------------------------
# 4. Helper function: run one summary through the pipeline
# -----------------------------------------------------------
def process_single_summary(summary_text: str) -> str:
    """Return final_response string for one API summary."""
    # 4-a  Summarise & retrieve
    project_prompt = create_project_summary_prompt(summary_text)
    description = generate_text(
        model=mistral_model,
        tokenizer=mistral_tokenizer,
        input_text=project_prompt,
        max_new_tokens=512,
    )

    rag_response = find_similar_apis(collection=collection, text_input=description)
    internal_blocks = generate_internal_prompt_blocks(
        parsed_rag_response=parse_rag_response(rag_response)
    )

    # 4-b  External search
    external_apis = search_for_microservice(summary_text)
    external_formatted = external_apis.strip() if external_apis else "None provided"

    # 4-c  Implementation prompt
    final_input = create_implementation_prompt(
        input_api=summary_text,
        internal_apis="\n".join(internal_blocks),
        external_apis=external_formatted,
    )

    # 4-d  Base generation (Mistral)
    mistral_text = generate_text(
        model=mistral_model,
        tokenizer=mistral_tokenizer,
        input_text=final_input,
        max_new_tokens=2048,
    )

    # 4-e  Ensemble path
    if not ensemble:
        return mistral_text

    llama_text = generate_text(
        model=llama_model,
        tokenizer=llama_tokenizer,
        input_text=final_input,
        max_new_tokens=2048,
    )

    merger_prompt = create_merger_prompt(
        user_input=summary_text, mistral_text=mistral_text, llama_text=llama_text
    )

    merged = generate_text(
        model=merger_model,
        tokenizer=merger_tokenizer,
        input_text=merger_prompt,
        max_new_tokens=3072,
    )
    return merged


# -----------------------------------------------------------
# 5. Main loop – write all outputs
# -----------------------------------------------------------
with open("output.txt", "w", encoding="utf-8") as fout:
    for idx, api_summary in enumerate(api_summaries, start=1):
        print(f"\n▶ Processing item {idx}/{len(api_summaries)}…")
        try:
            response = process_single_summary(api_summary)
        except Exception as err:
            response = f"ERROR processing item {idx}: {err}"
            print(response)

        fout.write(f"\n\n### Response {idx}\n")
        fout.write(response)

print(f"\nDone. All outputs saved to {Path('output.txt').resolve()}")
