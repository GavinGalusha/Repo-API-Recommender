#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uses vector‑DB RAG with internal code. No web search, no ensemble.
"""

import json, argparse, torch, chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM

from utils.helpers import find_similar_apis, parse_rag_response, generate_internal_prompt_blocks
from walker import read_and_check_file, walk_repo

# ── CLI ----------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--repo_path', type=str)
parser.add_argument('--file_path', type=str)
parser.add_argument('--description', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

# ── INPUT API ----------------------------------------------------------------
if args.repo_path:
    summaries = []
    for r in walk_repo(args.repo_path):
        try:
            entry = json.loads(r); summaries.append(entry['endpoints']['api_summary'])
        except Exception:
            pass
    api_summary = '\n'.join(summaries) if summaries else "No REST APIs found"
elif args.file_path:
    result = read_and_check_file(args.file_path)
    api_summary = result['endpoints']['api_summary'] if result else "No REST API found."
elif args.description:
    api_summary = input("Describe an API in plain text: ")
else:
    raise ValueError("Provide --repo_path, --file_path or --description")

# ── Vector DB lookup ----------------------------------------------------------
chroma_client = chromadb.PersistentClient(path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="microservice_descriptions")

rag = find_similar_apis(collection, api_summary)
internal_blocks = generate_internal_prompt_blocks(parse_rag_response(rag))
internal_formatted = "\n".join(internal_blocks) if internal_blocks else "None relevant"

# ── Model --------------------------------------------------------------------
tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16, device_map="auto"
)

# ── Prompt -------------------------------------------------------------------
def make_prompt(api: str, internal: str) -> str:
    return f"""
You are a senior software‑engineering assistant.
Below is an INPUT API description plus **internal code excerpts** retrieved via RAG.
Explain exactly how each excerpt can be leveraged to implement the INPUT API.
If a snippet is irrelevant, say so briefly and move on.

### INPUT API
{api}

### INTERNAL APIS
{internal}

### Guidance
"""

# ── Generate -----------------------------------------------------------------
ids = tok(make_prompt(api_summary, internal_formatted), return_tensors="pt").input_ids.to(model.device)
out = model.generate(ids, max_new_tokens=2048)
ans = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)

with open("output_rag.txt", "w", encoding="utf-8") as f:
    f.write(ans)
print("Saved → output_rag.txt")
