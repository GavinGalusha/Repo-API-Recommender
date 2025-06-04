import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
import json
revision = None

model = SentenceTransformer("avsolatorio/GIST-large-Embedding-v0", revision=revision)

texts = [
        "My girlfriend lived in Kerala",
        "Kerala is the city where my girlfriend lived",
        "My dog is named Kevin"
]

# Compute embeddings
embeddings = model.encode(texts, convert_to_tensor=True)

# Compute cosine-similarity for each pair of sentences
scores = F.cosine_similarity(embeddings.unsqueeze(1), embeddings.unsqueeze(0), dim=-1)

print(scores.cpu().numpy())


# Get embedding for a given text
def get_gist_embedding(text):
    return model.encode(text, convert_to_tensor=True)



# Get list of api explanations from json file
def get_list_from_json(json_file):
    api_explanations = []
    with open(json_file, 'r') as file:
        data = json.load(file)
        for item in data:
            api_explanations.append(item["description"])
    return api_explanations


# Find similar apis for a given text
def find_similar_apis(text):
    embeddings = get_gist_embedding(text)
    scores = F.cosine_similarity(embeddings.unsqueeze(1), embeddings.unsqueeze(0), dim=-1)
    return scores.cpu().numpy()
