import os
import json
import lmstudio as lms
import chromadb


# Configuration
SERVER_API_HOST = "localhost:1234"
# Connect to the LLM server

chroma_client = chromadb.PersistentClient(path="Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="my_collection")


def find_similar_apis(text_input, top_k = 4):
    results = collection.query(
    query_texts=[input],
    n_results=4
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






lms.configure_default_client(SERVER_API_HOST)
model = lms.llm("ibm/granite-3.1-8b")

prompt = """ 

is the input api. You are an api reccomender. Take in the descriptions of an API or multiple APIs, and for each api and file listed below, state the api and the file, and explain how a similar feature could be implemented using the input api. Do not include publically known api's we are talking about specific endpoints that are built in these applications"""

input = input("Input an api description to receive similar api's that could be useful: \n")


rag_response = find_similar_apis(input)
response = parse_rag_response(rag_response)

print("Rag Response", response)
print()
result = model.respond(input + prompt + str(response))
print("final structured output:")
print("Your input: ", input)
print(result)


