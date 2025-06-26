import argparse
import chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.web_search import search_for_microservice
from utils.helpers import read_code
from utils.helpers import find_similar_apis
from utils.helpers import parse_rag_response
from utils.prompts import create_summary_prompt
from utils.prompts import create_implementation_prompt
from utils.prompts import create_merger_prompt

# check ensemble argument
parser = argparse.ArgumentParser()
parser.add_argument('--ensemble', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()
ensemble = args.ensemble

# access vector DB
chroma_client = chromadb.PersistentClient(path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="my_collection")

# set and verify device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

# load mistral (default model, ensemble or not)
mistral_tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
mistral_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.float16, device_map="auto"
)

if ensemble:
    # load llama
    llama_tokenizer = AutoTokenizer.from_pretrained("NousResearch/Hermes-2-Pro-Llama-3-8B")
    llama_model = AutoModelForCausalLM.from_pretrained(
        "NousResearch/Hermes-2-Pro-Llama-3-8B", torch_dtype=torch.float16, device_map="auto"
    )

    # load mixtral
    merger_tokenizer = AutoTokenizer.from_pretrained("NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO")
    merger_model = AutoModelForCausalLM.from_pretrained(
        "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", torch_dtype=torch.float16, device_map="auto"
    )

# get user input and query vector db
user_input = input("Input an API description: ")
rag_response = find_similar_apis(collection=collection, text_input=user_input)
rag = parse_rag_response(rag_response)

# summarize and format internal APIs
internal_blocks = []
for path, doc in rag:
    code = read_code(path)
    truncated_code = code[:1500]
    input_summary = create_summary_prompt(path=path, code=truncated_code)
    input_ids = mistral_tokenizer(input_summary, return_tensors="pt").input_ids.to(mistral_model.device)
    output = mistral_model.generate(input_ids, max_new_tokens=128)
    summary = mistral_tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)

    internal_blocks.append(f"""---
Path: {path}
Summary: {summary.strip()}
Code:
{truncated_code}
""")

# include external repo if relevant
external_apis = search_for_microservice(user_input)
external_formatted = external_apis.strip() if external_apis else "None provided"

# final input
final_input = create_implementation_prompt(
    input_api=user_input,
    internal_apis="\n".join(internal_blocks),
    external_apis=external_formatted
)

# generate response with Mistral
mistral_ids = mistral_tokenizer(final_input, return_tensors="pt").input_ids.to(mistral_model.device)
mistral_output = mistral_model.generate(mistral_ids, max_new_tokens=2048)
mistral_text = mistral_tokenizer.decode(mistral_output[0][mistral_ids.shape[1]:], skip_special_tokens=True)

if not ensemble:
    with open("output.txt", "w") as f:
        f.write(mistral_text)
    print("Output saved to output.txt.")
else:
    # generate response with LLaMA
    llama_ids = llama_tokenizer(final_input, return_tensors="pt").input_ids.to(llama_model.device)
    llama_output = llama_model.generate(llama_ids, max_new_tokens=2048)
    llama_text = llama_tokenizer.decode(llama_output[0][llama_ids.shape[1]:], skip_special_tokens=True)

    # generate merger output
    merger_prompt = create_merger_prompt(user_input=user_input, mistral_text=mistral_text, llama_text=llama_text)
    refiner_ids = merger_tokenizer(merger_prompt, return_tensors="pt").input_ids.to(merger_model.device)
    refiner_output = merger_model.generate(refiner_ids, max_new_tokens=3072)
    final_response = merger_tokenizer.decode(refiner_output[0][refiner_ids.shape[1]:], skip_special_tokens=True)

    # write output to output file
    with open("output.txt", "w") as f:
        f.write(final_response)
    print("Output saved to output.txt.")
