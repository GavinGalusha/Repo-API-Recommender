from sentence_transformers import SentenceTransformer
import torch
import torch.nn.functional as F
from torch import Tensor

# Load GIST model
revision = None
model = SentenceTransformer("avsolatorio/GIST-large-Embedding-v0", revision=revision)

def get_GIST_embedding(text: str) -> Tensor:
    embedding = model.encode(text, convert_to_tensor=True)  # Already normalized
    return embedding  # Shape: [dim]

def find_similar_apis(text, reference_embeddings, description_list, top_k=5):
    query_embedding = get_GIST_embedding(text)  # Shape: [dim]

    # Compute cosine similarity with all reference embeddings
    scores = F.cosine_similarity(query_embedding.unsqueeze(0), reference_embeddings, dim=1)  # Shape: [N]

    # Get top-k most similar indices
    top_k_indices = torch.topk(scores, k=min(top_k, len(scores))).indices

    return [(description_list[i], scores[i].item()) for i in top_k_indices]

# Example usage
passages = [
    "My girlfriend lived in Kerala",
    "Kerala is the city where my girlfriend lived",
    "My dog is named Kevin"
]

# Precompute embeddings
embeddings = model.encode(passages, convert_to_tensor=True)

# Run similarity
most_similar = find_similar_apis("dogs and cats", embeddings, passages)
print(most_similar)
