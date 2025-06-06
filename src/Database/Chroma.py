import chromadb
import json


chroma_client = chromadb.Client()


with open("../api_descriptions.json", "r") as f:
    api_data = json.load(f)


collection = chroma_client.get_or_create_collection(name="my_collection")


documents = []
ids = []
metadatas = []



i = 0 
for i,api in enumerate(api_data):
    file = api["file"]
    endpoints = api["endpoints"]
    summary = endpoints["api_summary"]
    methods = endpoints["methods"]
    paths = endpoints["paths"]

    documents.append(summary)
    i += 1
    ids.append(f"id_{i}")  # Ensure each document has a unique ID
    metadatas.append({
        "methods": methods,
        "paths": paths
    })

collection.upsert(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)


results = collection.query(
    query_texts=["This API endpoint connects with a database"],
    n_results=2
)

print(results)
