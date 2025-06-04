import requests
import json

# Configuration
API_URL = "http://localhost:1234/v1/embeddings"
MODEL_NAME = "text-embedding-nomic-embed-text-v1.5-embedding"  
TEXT_TO_EMBED = "Some text to embed" 

# Create request payload
payload = {
    "model": MODEL_NAME,
    "input": TEXT_TO_EMBED
}

# Make the request
response = requests.post(
    API_URL,
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

# Parse and display result
if response.status_code == 200:
    embedding = response.json()["data"][0]["embedding"]
    print("✅ Embedding (first 10 values):", embedding[:10])
else:
    print("❌ Error:", response.status_code)
    print(response.text)
