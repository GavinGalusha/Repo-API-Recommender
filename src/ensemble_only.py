#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model‑ensemble (Mistral + Llama + Mixtral) with NO retrieval.
"""

import json, argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from utils.helpers import generate_text
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

# ── Load models ---------------------------------------------------------------
mistral_tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
mistral = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.float16, device_map="auto")

llama_tok = AutoTokenizer.from_pretrained("NousResearch/Hermes-2-Pro-Llama-3-8B")
llama = AutoModelForCausalLM.from_pretrained(
    "NousResearch/Hermes-2-Pro-Llama-3-8B", torch_dtype=torch.float16, device_map="auto")

mix_tok = AutoTokenizer.from_pretrained("NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO")
mix = AutoModelForCausalLM.from_pretrained(
    "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", torch_dtype=torch.float16, device_map="auto")

# ── Prompt -------------------------------------------------------------------
prompt = f"""
You are a senior software‑engineering assistant.
Provide detailed implementation guidance for the following INPUT API.

### INPUT API
{api_summary}

### Guidance
"""

# ── Generate from individual models ------------------------------------------
mistral_out = generate_text(mistral, mistral_tok, prompt, 2048)
llama_out   = generate_text(llama,   llama_tok,   prompt, 2048)

# Merge with Mixtral acting as arbiter
merge_prompt = f"""
You are an expert reviewer.
Below are two assistant answers. Merge the strongest points, remove duplication,
and output a single high‑quality recommendation.

### Assistant 1
{mistral_out}

### Assistant 2
{llama_out}
"""
final_out = generate_text(mix, mix_tok, merge_prompt, 3072)

with open("output_ensemble.txt", "w", encoding="utf-8") as f:
    f.write(final_out)
print("Saved → output_ensemble.txt")
