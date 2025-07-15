#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pure 0‑shot implementation guidance.
No RAG, no web search, no ensemble.
"""

import json, argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from walker import read_and_check_file, walk_repo

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--repo_path', type=str)
parser.add_argument('--file_path', type=str)
parser.add_argument('--description', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()

# ── Build INPUT‑API summary ───────────────────────────────────────────────────
if args.repo_path:
    summaries = []
    for r in walk_repo(args.repo_path):
        try:
            entry = json.loads(r)
            summaries.append(entry['endpoints']['api_summary'])
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

# ── Model ──────────────────────────────────────────────────────────────────────
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16, device_map="auto"
)

# ── Prompt builder ────────────────────────────────────────────────────────────
def make_prompt(api: str) -> str:
    return f"""
You are a senior software‑engineering assistant.
A developer provided an API specification (INPUT API) and wants concrete,
implementation‑level guidance.

Give:
- Recommended architecture / data models.
- Key function or class names.
- Example endpoint handlers.
Avoid external repos or sources; rely only on your expertise.

### INPUT API
{api}

### Guidance
"""

# ── Generate ──────────────────────────────────────────────────────────────────
input_ids = tok(make_prompt(api_summary), return_tensors="pt").input_ids.to(model.device)
out = model.generate(input_ids, max_new_tokens=1024)
answer = tok.decode(out[0][input_ids.shape[1]:], skip_special_tokens=True)

with open("output_zero_shot.txt", "w", encoding="utf-8") as f:
    f.write(answer)
print("Saved → output_zero_shot.txt")
