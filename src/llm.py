import chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

#access database
chroma_client = chromadb.PersistentClient(path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="my_collection")
print(collection.count())

#transformers method
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.float16, device_map=device
)
 
def find_similar_apis(text_input, top_k=1):
    results = collection.query(
    query_texts=[text_input],
    n_results=top_k
    )
    return results

def parse_rag_response(rag_response):
    """
    Parses a RAG response and returns a list of tuples with (file, document) in order.
    """
    documents = rag_response['documents'][0]
    metadatas = rag_response['metadatas'][0]

    if len(documents) != len(metadatas):
        raise ValueError("Mismatch between number of documents and metadata entries.")

    result = []
    for doc, meta in zip(documents, metadatas):
        file = meta.get('file', 'UNKNOWN FILE')
        result.append((file, doc))

    return result

def read_code(filename):
    with open(filename, 'r') as f:
        code = f.read()
    return code

prompt = """
You are an expert software assistant. Given a developer's API feature request (called the INPUT API) and a list of RECOMMENDED APIs retrieved from an internal codebase, your job is to analyze the provided source code and suggest specific implementation guidance.

For each recommended API, do the following:
- Identify the FULL **file path**.
- Summarize the **purpose** of the API using the filename and the code contents.
- Explain how **specific code from the file** (methods, classes, endpoint routes, or logic) can be reused or adapted to help implement the INPUT API functionality.

Each response should follow this exact format:

---
**Path:** <exact file path>  
**Summary:** <brief summary of what the code does>  
**Implementation Guidance:** <4+ descriptive sentences showing how specific parts of the code (by name or behavior) can help implement the INPUT API. Use concrete references to the code.>
---

Rules:
- DO NOT reference any public APIs or libraries (e.g., Stripe, Twitter).
- Only use the code and descriptions provided in the recommended list.
- Assume the reader is a software engineer familiar with REST, Python, and API patterns.

Now complete the following:

### INPUT API  
{input_api}

### RECOMMENDED APIs (with code excerpts)  
{recommended_apis}

<END OF CODE>
** Ensure that you include code snippets from the recommended API code excerpts in your response. **
"""

user_input = input("Input an api description to receive similar api's that could be useful: \n")
rag_response = find_similar_apis(user_input)
rag_response = parse_rag_response(rag_response)

response = [] 
for path, summary in rag_response:
    code = read_code(path)
    response.append({
        "path": path,
        "summary": summary,
        "code": code
    })

formatted_apis = ""
for r in response:
    formatted_apis += f"\n---\nPath: {r['path']}\nSummary: {r['summary']}\nCode:\n{r['code'][:1000]}\n"

input_text = prompt.format(
    input_api = user_input,
    recommended_apis = formatted_apis
)
input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
print('generating model output...')
outputs = model.generate(input_ids, max_new_tokens=1024)

print("final structured output:")
structured_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
with open('output.txt', 'w') as f:
    f.write(structured_output)
