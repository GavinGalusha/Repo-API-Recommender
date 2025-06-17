import os
import json
import lmstudio as lms
import chromadb

''' #LMS studio method 
SERVER_API_HOST = "localhost:1234"

lms.configure_default_client(SERVER_API_HOST)
model = lms.llm("ibm/granite-3.1-8b")
'''

#access database
chroma_client = chromadb.PersistentClient(path="database.chroma")
collection = chroma_client.get_or_create_collection(name="my_collection")


#transformers method
from transformers import T5Tokenizer, T5ForConditionalGeneration
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")


 
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




prompt = """

The following is a technical description of an API feature (marked as the INPUT API). 
Your task is to examine a list of similar internal API descriptions (RECOMMENDED APIs), 
and for each recommended API, provide:

1. The file path it came from.
2. A brief summary of what that API does.
3. A specific explanation of how the feature described in the INPUT API could be implemented using this recommended API, drawing clear parallels in functionality or design.

⚠️ Do NOT refer to publicly available APIs or services (e.g., Stripe, Twitter). Focus strictly on the private, internal APIs provided.

Use at least **4 descriptive sentences** per recommendation, written for a developer audience.

--- INPUT API ---
{input_api}

--- RECOMMENDED APIs ---
{recommended_apis}
"""

input = input("Input an api description to receive similar api's that could be useful: \n")


rag_response = find_similar_apis(input)
response = parse_rag_response(rag_response)

print("Rag Response", response)
print()

input_text = prompt.format(
    input_api = input,
    recommended_apis = str(response)
)
input_ids = tokenizer(input_text, return_tensors="pt").input_ids

outputs = model.generate(input_ids, max_new_tokens=512)
print("final structured output:")
print("Your input: ", input)
print(tokenizer.decode(outputs[0]))



#LMS way of doing it 
''' 
result = model.respond(input + prompt + str(response))
print("final structured output:")
print("Your input: ", input)
print(result)
'''