import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
import json


def last_token_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

# No need to add instruction for retrieval documents
passages = [
    "My girlfriend is from India",
    "India is where my girlfriend comes from",
    "I have a dog named kevin",
    "My dogs name is kevin"
]

# load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('Salesforce/SFR-Embedding-Mistral')
model = AutoModel.from_pretrained('Salesforce/SFR-Embedding-Mistral')

# get the embeddings
max_length = 4096
batch_dict = tokenizer(passages, max_length=max_length, padding=True, truncation=True, return_tensors="pt")
outputs = model(**batch_dict)
embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

# normalize embeddings
embeddings = F.normalize(embeddings, p=2, dim=1)
scores1 = (embeddings[0] @ embeddings[1].T) * 100
scores2 = (embeddings[0] @ embeddings[2].T) * 100
scores3 = (embeddings[2] @ embeddings[3].T) * 100

print(scores1.tolist())
print(scores2.tolist())
print(scores3.tolist())


def get_sfr_embedding(text: str) -> Tensor:
    # Tokenize input
    encoded_input = tokenizer(
        text,
        max_length=4096,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )
    # Pass through model
    with torch.no_grad():
        model_output = model(**encoded_input)
    # Extract pooled embedding
    pooled_embedding = last_token_pool(model_output.last_hidden_state, encoded_input["attention_mask"])
    # Normalize the embedding
    normalized_embedding = F.normalize(pooled_embedding, p=2, dim=1)
    return normalized_embedding.squeeze(0)  # Remove batch dimension




def find_similar_apis(text, reference_embeddings, description_list, top_k=5):
    query_embedding = get_sfr_embedding(text)  # Shape: [dim]
    # Stack existing embeddings into a single tensor
    # Compute cosine similarity with all reference embeddings
    scores = F.cosine_similarity(query_embedding.unsqueeze(0), reference_embeddings, dim=1)  # Shape: [N]
    # Get top-k most similar indices
    top_k_indices = torch.topk(scores, k=min(top_k, len(scores))).indices
    # Return top-k (description, score) pairs
    return [(description_list[i], scores[i].item()) for i in top_k_indices]



most_similar = find_similar_apis("dogs and cats", embeddings, passages)
print(most_similar)






