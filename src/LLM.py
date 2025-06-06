import os
import json
import lmstudio as lms
import chromadb

# Configuration
SERVER_API_HOST = "localhost:1234"
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go'}
ROOT_DIR = "cloned"
OUTPUT_FILE = "api_descriptions.json"

# Connect to the LLM server
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="my_collection")


lms.configure_default_client(SERVER_API_HOST)
model = lms.llm("ibm/granite-3.1-8b")


documents = []
# Check if file is code
def is_code_file(filename):
    return any(filename.endswith(ext) for ext in CODE_EXTENSIONS)

# Construct prompt for the LLM
def build_prompt(code_str):
    return f"""<s>[INST] You are a code understanding assistant.

Your job is to read a single source code file and determine if it defines any REST API endpoints.

Instructions:
- If this file explicitly defines one or more REST API endpoints (e.g., using a router, controller, or HTTP method annotation), respond with a JSON object describing the API defined in this file.
- Your response should include:
  - "api_summary": a 3-sentence high-level description of what the API does
  - "methods": a list of HTTP methods used (e.g., ["GET", "POST"])
  - "paths": a list of URL paths (e.g., ["/users", "/users/{{id}}"])

- If this file does **not** define any REST API endpoints explicitly (e.g., it only has imports, config, or helpers), respond with exactly:
NO ENDPOINTS

Respond with no other text.

Here is the file:
```python
{code_str}
``` [/INST]
"""
# Run the model with the generated prompt
def run_model(prompt):
    response = model.respond(prompt)
    text = response.content
    print("Text:" + text)
    return text

# Extract the JSON substring from the model's output
def extract_json_string(response):
    print(response)
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    print(json_start, json_end)
    if json_start == -1 or json_end == -1:
        raise ValueError("No JSON object found in string.")
    return response[json_start:json_end]

def truncate_code(code):
    return code[:9000]
    
# Main execution logic
def main():
    with open(OUTPUT_FILE, 'w') as out_file:
        for root, _, files in os.walk(ROOT_DIR):
            for file in files:
                if is_code_file(file):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    
                    truncated_code = truncate_code(code)
                    prompt = build_prompt(truncated_code)
                    response = run_model(prompt)
                    if "ENDPOINTS" in response or "There are no REST API endpoints" in response:
                        print(f"[SKIP] {filepath} - No endpoints found")
                    else:
                        documents.append(response)
                        

    collection.upsert(
    documents=documents,
    )


    results = collection.query(
    query_texts=["This API endpoint connects with a database"],
    n_results=5
    )

    print(results)
                    

if __name__ == "__main__":
    main()
