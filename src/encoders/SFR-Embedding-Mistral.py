import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel


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
