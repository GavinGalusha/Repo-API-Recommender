import requests
import json
import torch
import torch.nn.functional as F

# Configuration
API_URL = "http://localhost:1234/v1/embeddings"
MODEL_NAME = "text-embedding-nomic-embed-text-v1.5-embedding"  

def get_embedding(text):
    payload = {
        "model": MODEL_NAME,
        "input": text
    }  
    response = requests.post(
        API_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )   
    if response.status_code == 200:
        embedding = response.json()["data"][0]["embedding"]
        print("✅ Embedding (first 10 values):", embedding[:10])
        return embedding
    else:
        print("❌ Error:", response.status_code)
        print(response.text)     
        return None       




def get_embeddings_from_json(json_file):
    embeddings = []
    with open(json_file, 'r') as file:
        data = json.load(file)
        for item in data:
            embedding = get_embedding(item["description"])
            embeddings.append(embedding)
    return embeddings



def find_similar_apis(text, embeddings, descriptions, top_k=5):
    embedding = get_embedding(text)
    if embedding is None:
        return []
    
    embedding_tensor = torch.tensor(embedding).unsqueeze(0)  # Shape: [1, D]
    embeddings_tensor = torch.tensor(embeddings)  # Shape: [N, D]

    scores = F.cosine_similarity(embedding_tensor, embeddings_tensor, dim=1)  # Shape: [N]
    top_scores, top_indices = torch.topk(scores, top_k)

    results = []
    for i in range(top_k):
        results.append({
            "description": descriptions[top_indices[i].item()],
            "score": top_scores[i].item()
        })

    return results






test_embedding = get_embedding("get embeddings for this text")
# Create request payload






