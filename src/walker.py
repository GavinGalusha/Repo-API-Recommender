#!/usr/bin/env python3
import re
import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

# model configuration
bnb_conf = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_type=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
MODEL_NAME = "deepseek-ai/deepseek-coder-6.7b-instruct"
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go'}
OUTPUT_FILE = "api_descriptions_deepseek_coder_6pt7b.json"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, \
                                             device_map="auto", \
                                             quantization_config=bnb_conf, \
                                             torch_dtype=torch.float16)
model.eval()

def is_code_file(filename):
    """Return whether a filename ends with a predefined language extension"""
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

def build_prompt(code_str):
    """Generate prompt with parsed code"""
    messages=[ { 'role': 'user',
    'content': f"""You are a code understanding assistant.

Your job is to read a single source code file and determine if it defines any REST API endpoints.

Instructions:
- If this file explicitly defines one or more REST API endpoints (e.g., using a router, controller, or HTTP method annotation), respond with a JSON object describing the API defined in this file.
- Your response should include:
  - "api_summary": a 3-sentence high-level description of what the API does. This must be a general summary of all endpoints in the file. If there are several endpoints in the file, describe the interplay and general themes of the API endpoints, and how they may be used in relation to the overall system. This summary must be STRICTLY three sentenes, including as much technical and practical details as possible. Describe them in a general way such that knowledge of the project is not needed, and the service can be described in an API catalog.
  - "methods": a list of HTTP methods used (e.g., ["GET", "POST"])
  - "paths": a list of URL paths (e.g., ["/users", "/users/{id}"]). Ensure you include the name of the repository in this path.


Here is the file:
python
{code_str}

- If this file does **not** define any REST API endpoints explicitly (e.g., it only has imports, config, or helpers), respond with exactly:
NO ENDPOINTS

Respond with no other text. Be sure that output for an endpoint finding is in the specified JSON format, if there are defined endpoints in the file.
"""
} ]
    return messages


def run_model(prompt, max_tokens=1024):
    """Run deepseek-family model with generated prompt"""
    inputs = tokenizer.apply_chat_template(prompt, \
                                           add_generation_prompt=True, \
                                           return_tensors="pt") \
                                           .to(model.device)
    with torch.no_grad():
        output = model.generate(
            inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            top_k=50,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_ids = output[0][inputs.shape[-1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

def extract_json_string(s):
    # try to find the first { and last }, and extract what's in between
    match = re.search(r'\{.*\}', s, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in string.")
    return match.group(0)

def has_negative_match(response) -> bool:
    negatives = ['ENDPOINTS', 'There are no REST API endpoints', \
                 'file does not contain REST', 'file does not contain any', \
                 'file does not define any']
    return any((r in response for r in negatives))

def walk_repo(root_dir):
    results = []
    p, n = 0, 0
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not is_code_file(file):
                continue
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                prompt = build_prompt(code)
                response = run_model(prompt)
                negative_match = has_negative_match(response)

                if negative_match:
                    n += 1
                else:
                    try:
                        j = extract_json_string(response)
                        json_obj = json.loads(j)
                        results.append(json.dumps({
                            "file": filepath,
                            "endpoints": json_obj
                        }))
                        p += 1
                        print(f'positives: {p}, negatives: {n}.')
                    except json.JSONDecodeError:
                        print(f"[WARN] Failed to parse JSON for {filepath}")
            except Exception as e:
                print(f"[ERROR] Failed to process {filepath}: {e}")
    return results

def read_and_check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        prompt = build_prompt(code)
        response = run_model(prompt)
        print(response)
        negative_match = has_negative_match(response)
        
        if negative_match:
            n += 1
            print('got a negative')
            return None
        else:
            try:
                print('got a positive')
                j = extract_json_string(response)
                print(j)
                json_obj = json.loads(j)
                print(json_obj)
                return {
                    "file": filepath,
                    "endpoints": json_obj
                }
            except json.JSONDecodeError:
                print(f"[WARN] Failed to parse JSON for {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to process {filepath}: {e}")
