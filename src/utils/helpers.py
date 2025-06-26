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

def generate_text(model, tokenizer, input_text, max_new_tokens):
    input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
    output = model.generate(input_ids, max_new_tokens=max_new_tokens)
    return tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
