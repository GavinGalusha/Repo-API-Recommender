#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Uses GitHub/web search context only. No RAG, no ensemble.
"""

import json, argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from utils.web_search import search_for_microservice
from walker import read_and_check_file, walk_repo

# ── CLI ----------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--repo_path', type=str)
parser.add_argument('--file_path', type=str)
parser.add_argument('--description', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

# ── INPUT API ----------------------------------------------------------------
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

# ── External (web) repos ------------------------------------------------------
external_apis = search_for_microservice(api_summary).strip() or "None found"

# ── Model --------------------------------------------------------------------
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16, device_map="auto"
)

# ── Prompt -------------------------------------------------------------------
def make_prompt(api: str, external: str) -> str:
    return f"""
You are a senior software‑engineering assistant.
Below is an INPUT API description plus **open‑source references** found online.
For each external repo, explain how its patterns or code can inspire \
the implementation (do NOT assume direct import).

### INPUT API
{api}

### EXTERNAL REFERENCES
{external}

### Guidance
"""

# ── Generate -----------------------------------------------------------------
ids = tok(make_prompt(api_summary, external_apis), return_tensors="pt").input_ids.to(model.device)
out = model.generate(ids, max_new_tokens=2048)
ans = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)

with open("output_web_search.txt", "w", encoding="utf-8") as f:
    f.write(ans)
print("Saved → output_web_search.txt")
