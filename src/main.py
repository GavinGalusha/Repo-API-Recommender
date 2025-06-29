import json
import argparse
import chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.web_search import search_for_microservice
from utils.helpers import find_similar_apis
from utils.helpers import parse_rag_response
from utils.helpers import generate_text
from utils.helpers import generate_internal_prompt_blocks
from utils.prompts import create_implementation_prompt
from utils.prompts import create_merger_prompt
from utils.prompts import create_project_summary_prompt
from walker import read_and_check_file, walk_repo


# check ensemble argument
parser = argparse.ArgumentParser()
parser.add_argument('--repo_path', type=str)
parser.add_argument('--file_path', type=str)
parser.add_argument('--ensemble', action=argparse.BooleanOptionalAction, default=False)
parser.add_argument('--description', action=argparse.BooleanOptionalAction, default=False)
args = parser.parse_args()
ensemble = args.ensemble
repo_path = args.repo_path
file_path = args.file_path
description_condition = args.description

if repo_path:
    results = walk_repo(repo_path)

    summaries = []
    for r in results:
        try:
            entry = json.loads(r)
            summaries.append(entry['endpoints']['api_summary'])
        except Exception as e:
            print(e)
    api_summary = '\n'.join(summaries) if summaries else "No REST APIs were found in this repo"
elif file_path:
    result = read_and_check_file(file_path)
    api_summary = result['endpoints']['api_summary'] if result else "No REST API found in this file."

elif description_condition:
    api_summary = input("Describe an API in plain text: ")
else:
    raise ValueError("You must provide either --repo_path or --description.")

# access vector DB
chroma_client = chromadb.PersistentClient(path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="microservice_descriptions")

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

# format RAG code and descriptions
project_summary_prompt = create_project_summary_prompt(api_summary)
description = generate_text(model=mistral_model, tokenizer=mistral_tokenizer, input_text=project_summary_prompt, max_new_tokens=512)
rag_response = find_similar_apis(collection=collection, text_input=description)
parsed_rag_response = parse_rag_response(rag_response)
internal_prompt_blocks = generate_internal_prompt_blocks(parsed_rag_response=parsed_rag_response)

# include external repo
external_apis = search_for_microservice(api_summary)
external_formatted = external_apis.strip() if external_apis else "None provided"

# final input
final_input = create_implementation_prompt(
    input_api=api_summary,
    internal_apis="\n".join(internal_prompt_blocks),
    external_apis=external_formatted
)

# generate response with Mistral
mistral_text = generate_text(model=mistral_model, tokenizer=mistral_tokenizer, input_text=final_input, max_new_tokens=2048)

if not ensemble:
    final_response = mistral_text
else:
    # generate response with LLaMA
    llama_text = generate_text(model=llama_model, tokenizer=llama_tokenizer, input_text=final_input, max_new_tokens=2048)

    # generate merger output
    merger_prompt = create_merger_prompt(user_input=api_summary, mistral_text=mistral_text, llama_text=llama_text)
    final_response = generate_text(model=merger_model, tokenizer=merger_tokenizer, input_text=merger_prompt, max_new_tokens=3072)

with open("output.txt", "w", encoding='utf-8') as f:
    f.write(final_response)
print("Output saved to output.txt.")
