import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

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
