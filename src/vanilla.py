#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Repo-API-Recommender – simplified model-only version
---------------------------------------------------
• Removes web search and RAG components
• Uses a single model to generate responses
• Accepts single or batch inputs
"""

import json
import argparse
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.helpers import generate_text
from walker import read_and_check_file, walk_repo

# -----------------------------------------------------------
# 1. CLI
# -----------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--repo_path", type=str)
parser.add_argument("--file_path", type=str)
parser.add_argument("--list_file", type=str, help="Plain-text file – one API description per line")
parser.add_argument("--description", action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

# Convenience flags
repo_path = args.repo_path
file_path = args.file_path
list_file = args.list_file
description_condition = args.description

# -----------------------------------------------------------
# 2. Gather *all* API summaries we need to process
# -----------------------------------------------------------
api_summaries: list[str] = []

if list_file:
    lines = Path(list_file).read_text(encoding="utf-8").splitlines()
    api_summaries = [ln.strip() for ln in lines if ln.strip()]
    if not api_summaries:
        raise ValueError(f"{list_file} is empty.")
else:
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
# 3. Load model
# -----------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name, torch_dtype=torch.float16, device_map="auto"
)

# -----------------------------------------------------------
# 4. Prompt template
# -----------------------------------------------------------
def create_project_summary_prompt(raw_api_descriptions: str) -> str:
    return f"""
You are a senior software engineer assistant.

Your task is to read a set of REST API descriptions extracted from a software repository and write a high-level technical summary of what the project does *as a whole*. You should explain:
- The **primary goal** or purpose of the system.
- How the different REST endpoints **interact or relate** to each other.
- What major **subsystems or components** are implied by these APIs.
- Any **domain-specific patterns** you can infer (e.g., e-commerce, authentication, metrics, ML inference).

Your response should:
- Be **3–6 sentences** long.
- Avoid quoting or copying individual endpoint descriptions.
- Avoid hallucinating functionality — only use what's implied by the APIs.
- Treat this as an internal technical note for engineers.

### RAW API DESCRIPTIONS
{raw_api_descriptions}

**Final Instructions:**
- Focus on how the APIs fit together into a coherent service.
- Avoid generic phrases like “this project includes various APIs.”
- Do not reference specific file paths or filenames.
- Assume the project is self-contained and the description should reflect what someone reading the APIs alone would understand about the system.
"""

# -----------------------------------------------------------
# 5. Process loop
# -----------------------------------------------------------
with open("output.txt", "w", encoding="utf-8") as fout:
    for idx, summary in enumerate(api_summaries, start=1):
        print(f"\n▶ Processing item {idx}/{len(api_summaries)}…")
        try:
            prompt = create_project_summary_prompt(summary)
            response = generate_text(
                model=model,
                tokenizer=tokenizer,
                input_text=prompt,
                max_new_tokens=1024,
            )
        except Exception as err:
            response = f"ERROR processing item {idx}: {err}"
            print(response)

        fout.write(f"\n\n### Response {idx}\n")
        fout.write(response)

print(f"\nDone. All outputs saved to {Path('output.txt').resolve()}")
