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
 
def find_similar_apis(text_input, top_k=4):
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

prompt = """
You are an expert API assistant. Given an API feature description (called the INPUT API), and a list of similar internal APIs (called the RECOMMENDED APIs), your task is to analyze and structure useful implementation suggestions.

For **each recommended API**, return output in the following format:

---
Path: <exact file path>
Summary: <1-2 sentence description of the API>
Implementation Guidance: <How this API can be used to implement the INPUT API feature. Use 4+ descriptive sentences. Reference specific methods, endpoints, or concepts.>
---

Important rules:
- DO NOT mention public services (e.g., Stripe, Twitter).
- Focus only on the private, internal APIs listed in the RECOMMENDED APIs section.
- Write clearly for a developer audience.

Now complete the following:

### INPUT API
{input_api}

### RECOMMENDED APIs
{recommended_apis}
"""

user_input = input("Input an api description to receive similar api's that could be useful: \n")
rag_response = find_similar_apis(user_input)
response = parse_rag_response(rag_response)

print("Rag Response", response)

input_text = prompt.format(
    input_api = user_input,
    recommended_apis = str(response)
)
input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
print('generating model output...')
outputs = model.generate(input_ids, max_new_tokens=1024)

print("final structured output:")
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
