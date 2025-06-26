import json
import chromadb


def find_similar_apis(text_input, top_k=4):
    results = collection.query(
    query_texts=[text_input],
    n_results=top_k
    )
    return results

chroma_client = chromadb.PersistentClient(path="database.chroma")
collection = chroma_client.get_or_create_collection(name="woot")

documents = []
ids = []
metadatas = []

# open the JSONL-style file (one JSON object per line)
with open("../api_descriptions_deepseek_coder_6pt7b.json", "r") as f:
    for i, line in enumerate(f):
        api = json.loads(line.strip())

        file_name = api["file"]
        endpoints = api.get("endpoints", "Empty")
        summary = endpoints.get("api_summary", "Empty")
        methods = str(endpoints.get("methods", "Empty"))
        paths = str(endpoints.get("paths", "Empty"))

        documents.append(summary)
        ids.append(f"id_{i}")
        metadatas.append({
            "file": file_name,
            "methods": methods,
            "paths": paths
        })

print("Document Length:", len(documents))

def chunk_data(documents, ids, metadatas, max_lines):
    assert len(documents) == len(ids) == len(metadatas)
    chunked_documents, chunked_ids, chunked_metadatas = [], [], []
    for i in range(0, len(ids), max_lines):
        chunked_documents.append(documents[i:i + max_lines])
        chunked_ids.append(ids[i:i + max_lines])
        chunked_metadatas.append(metadatas[i:i + max_lines])
    return chunked_documents, chunked_ids, chunked_metadatas

chunked_docs, chunked_ids, chunked_metadatas = chunk_data(documents, ids, metadatas, max_lines=5000)

# upsert into the Chroma collection
for (docs_chunk, ids_chunk, metadatas_chunk) in zip(chunked_docs, chunked_ids, chunked_metadatas):
    collection.upsert(
        documents=docs_chunk,
        ids=ids_chunk,
        metadatas=metadatas_chunk
    )

print("Database Created")
text_input = str(input("enter an api, and we will return suggested apis \n"))
print(find_similar_apis(text_input))
