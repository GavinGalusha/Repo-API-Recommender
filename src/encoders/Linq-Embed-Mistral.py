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
    "Hangul was personally created and promulgated by the fourth king of the Joseon dynasty, Sejong the Great.[1][2] Sejong's scholarly institute, the Hall of Worthies, is often credited with the work, and at least one of its scholars was heavily involved in its creation, but it appears to have also been a personal project of Sejong."
]

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('Linq-AI-Research/Linq-Embed-Mistral')
model = AutoModel.from_pretrained('Linq-AI-Research/Linq-Embed-Mistral')

max_length = 4096
input_texts = [*passages]
# Tokenize the input texts
batch_dict = tokenizer(input_texts, max_length=max_length, padding=True, truncation=True, return_tensors="pt")
outputs = model(**batch_dict)
embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

# Normalize embeddings
embeddings = F.normalize(embeddings, p=2, dim=1)
print(embeddings)
