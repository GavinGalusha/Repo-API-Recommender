import chromadb
import json

chroma_client = chromadb.PersistentClient(path="database.chroma")
collection1 = chroma_client.get_or_create_collection(name="my_collection")

documents = []
ids = []
metadatas = []

# Open the JSONL-style file (one JSON object per line)
with open("../../sample_data/api_descriptions_deepseek_coder_6pt7b.json", "r") as f:
    for i, line in enumerate(f):
        api = json.loads(line.strip())  # Parse each line as a JSON object

        file = api["file"]
        endpoints = api.get("endpoints", "Empty")
        summary = endpoints.get("api_summary", "Empty")
        methods = str(endpoints.get("methods", "Empty"))
        paths = str(endpoints.get("paths", "Empty"))



        documents.append(summary)
        print()
        ids.append(f"id_{i}")
        metadatas.append({
            "file": file,
            "methods": methods,
            "paths": paths
        })
        print(i)


print("Document Length:", len(documents))
# Upsert into the Chroma collection



#Uncomment when we want to update database
collection1.upsert(
    documents=documents,
    ids=ids,
    metadatas=metadatas
)



print("Database Created")
input = str(input("enter an api, and we will return suggested apis \n"))


def find_similar_apis(text_input, top_k = 4):
    results = collection1.query(
    query_texts=[input],
    n_results=4
    )
    return results
    


print(find_similar_apis())

