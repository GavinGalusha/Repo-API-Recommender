import os
import json
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go'}
ROOT_DIR = "cloned"
OUTPUT_FILE = "api_descriptions.json"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto", torch_dtype=torch.float16)
model.eval()


def is_code_file(filename):
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

def build_prompt(code_str):
    return f"""<s>[INST] You are a code understanding assistant.

Your job is to read a single source code file and determine if it defines any REST API endpoints.

Instructions:
- If this file explicitly defines one or more REST API endpoints (e.g., using a router, controller, or HTTP method annotation), respond with a JSON object describing the API defined in this file.
- Your response should include:
  - "api_summary": a 3-sentence high-level description of what the API does
  - "methods": a list of HTTP methods used (e.g., ["GET", "POST"])
  - "paths": a list of URL paths (e.g., ["/users", "/users/{id}"])

- If this file does **not** define any REST API endpoints explicitly (e.g., it only has imports, config, or helpers), respond with exactly:
NO ENDPOINTS

Respond with no other text.

Here is the file:
```python
{code_str}
``` [/INST]
"""


def run_model(prompt, max_tokens=1024):
    inputs = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        output = model.generate(
            inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            #temperature=0.0,
            pad_token_id=tokenizer.eos_token_id,
        ) 
    generated_ids = output[0][inputs.shape[-1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

def extract_json_string(s):
    print(s)
    json_start = s.find('{')
    json_end = s.rfind('}') + 1
    print(json_start, json_end)
    if json_start == -1 or json_end == -1:
        raise ValueError("No JSON object found in string.")
    return s[json_start:json_end]

def main():
    with open(OUTPUT_FILE, 'w') as out_file:
        for root, _, files in os.walk(ROOT_DIR):
            for file in files:
                if is_code_file(file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        prompt = build_prompt(code)
                        response = run_model(prompt)
                        trimmed = response#[len(prompt):]

                        if "ENDPOINTS" in trimmed or "There are no REST API endpoints" in trimmed:
                            print('nope')
                            print(trimmed)
                            pass#print(trimmed)
                        else:
                            try:
                                j = extract_json_string(trimmed)
                                print(j)
                                json_obj = json.loads(j)
                                out_file.write(json.dumps({
                                    "file": filepath,
                                    "endpoints": json_obj
                                }) + '\n')
                            except json.JSONDecodeError:
                                print(f"[WARN] Failed to parse JSON for {filepath}")
                    except Exception as e:
                        print(f"[ERROR] Failed to process {filepath}: {e}")


if __name__ == "__main__":
    main()
