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



lms.configure_default_client(SERVER_API_HOST)
model = lms.llm("ibm/granite-3.1-8b")

prompt = """ 

is the input api. You are an api reccomender. Take in the descriptions of an API or multiple APIs, and use the information below to reccomend new API's that would complement the input API, using the api's below as in"""

input = input("Input an api description to receive similar api's that could be useful: \n")


response = find_similar_apis(input)


print("Rag Response", response)
print()
result = model.respond(input + prompt + str(response.items()))
print("final structured output:")
print("Your input: ", input)
print(result)


