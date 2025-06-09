import os
import json
import re
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

bnb_conf = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_type=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

MODEL_NAME = "codellama/CodeLlama-34b-Instruct-hf"
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go'}
ROOT_DIR = "cloned"
OUTPUT_FILE = "api_descriptions.json"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto", quantization_config=bnb_conf, torch_dtype=torch.float16)
model.eval()


def is_code_file(filename):
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

# check file extension
def is_code_file(filename):
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

# create prompt for llm
def build_prompt(code_str):
    return f"""<s>[INST] You are a code understanding assistant.

Your job is to read a single source code file and determine if it defines any REST API endpoints.

Instructions:
- If this file explicitly defines one or more REST API endpoints (e.g., using a router, controller, or HTTP method annotation), respond with a JSON object describing the API defined in this file.
- Your response should include:
  - "api_summary": a 3-sentence high-level description of what the API does. This must be a general summary of all endpoints in the file. If there are several endpoints in the file, describe the interplay and general themes of the API endpoints, and how they may be used in relation to the overall system. This summary must be STRICTLY three sentenes, including as much technical and practical details as possible. Describe them in a general way such that knowledge of the project is not needed, and the service can be described in an API catalog.
  - "methods": a list of HTTP methods used (e.g., ["GET", "POST"])
  - "paths": a list of URL paths (e.g., ["/users", "/users/{id}"]). Ensure you include the name of the repository in this path.


Here is the file:
```python
{code_str}
``` 
- If this file does **not** define any REST API endpoints explicitly (e.g., it only has imports, config, or helpers), respond with exactly:
NO ENDPOINTS

Respond with no other text. Be sure that output for an endpoint finding is in the specified JSON format, if there are defined endpoints in the file.[/INST]
"""


# run the model with generated prompt
def run_model(prompt, max_tokens=1024):
    inputs = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
    with torch.no_grad():
        output = model.generate(
            inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        ) 
    generated_ids = output[0][inputs.shape[-1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

# extract the json string from an LLM response
def extract_json_string(s):
    print(s)
    json_start = s.find('{')
    json_end = s.rfind('}') + 1
    if json_start == -1 or json_end == -1:
        raise ValueError("No JSON object found in string.")
    return s[json_start:json_end]

def main():
    with open(OUTPUT_FILE, 'w') as out_file:
        p, n = 0, 0
        for root, _, files in os.walk(ROOT_DIR):
            for file in files:
                if is_code_file(file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        prompt = build_prompt(code)
                        response = run_model(prompt)

                        negatives = ['ENDPOINTS', 'There are no REST API endpoints', 'file does not contain REST', 'file does not contain any', 'file does not define any']
                        negative_match = any([x in response for x in negatives])
                        if negative_match:
                            n += 1
                            pass
                        else:
                            try:
                                j = extract_json_string(response)
                                json_obj = json.loads(j)
                                out_file.write(json.dumps({
                                    "file": filepath,
                                    "endpoints": json_obj
                                }) + '\n')
                                out_file.flush()
                                p += 1
                                print(f'positives: {p}, negatives: {n}.')
                            except json.JSONDecodeError:
                                print(f"[WARN] Failed to parse JSON for {filepath}")
                    except Exception as e:
                        print(f"[ERROR] Failed to process {filepath}: {e}")

if __name__ == "__main__":
    main()
