import os
import json
import lmstudio as lms
import chromadb


# Configuration
SERVER_API_HOST = "localhost:1234"
# Connect to the LLM server

chroma_client = chromadb.PersistentClient(path="database.chroma")
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

Parse the below text to only include the descriptions from documents. List each description from documents whether it is 'Empty' or a description of an api"""

input = input("Input an api description to receive similar api's that could be useful: \n")


response = find_similar_apis(input)

result = model.respond(prompt + str(response.items()))
print("final structured output:")
print("Your input: ", input)
print(result)


