# retrieve local APIs
def find_similar_apis(collection, text_input, top_k=3):
    results = collection.query(query_texts=[text_input], n_results=top_k)
    return results

# parse response from vector db
def parse_rag_response(rag_response):
    documents = rag_response['documents'][0]
    metadatas = rag_response['metadatas'][0]
    return [(meta.get('file', 'UNKNOWN FILE'), doc) for doc, meta in zip(documents, metadatas)]

# read code file
def read_code(filename):
    with open(filename, 'r') as f:
        return f.read()
