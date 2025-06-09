import chromadb
import json

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="my_collection")

documents = []
ids = []
metadatas = []

# Open the JSONL-style file (one JSON object per line)
with open("../api_descriptions.json", "r") as f:
    for i, line in enumerate(f):
        api = json.loads(line.strip())  # Parse each line as a JSON object

        file = api["file"]
        endpoints = api.get("endpoints", "Empty")
        print(endpoints)
        summary = endpoints.get("api_summary", "Empty")
        methods = str(endpoints.get("methods", "Empty"))
        paths = str(endpoints.get("paths", "Empty"))



        documents.append(summary)
        ids.append(f"id_{i}")
        metadatas.append({
            "file": file,
            "methods": methods,
            "paths": paths
        })


print("Document LEngth:", len(documents))
# Upsert into the Chroma collection
collection.upsert(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)

# Run a test query
results = collection.query(
    query_texts=["This API endpoint connects with a database"],
    n_results=2
)

print(results)
