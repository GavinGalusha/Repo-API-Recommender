import argparse
import chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.web_search import search_for_microservice
from utils.helpers import read_code
from utils.helpers import find_similar_apis
from utils.helpers import parse_rag_response

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

# summarization prompt (pass 1)
summary_prompt = """
Summarize the purpose of this internal API. Just say what it does.

Path: {path}
Code:
{code}
"""

# implementation prompt (pass 2)
main_prompt = """
You are a senior software engineer assistant. A developer has provided an API feature request (INPUT API), and your job is to review both internal APIs (RECOMMENDED INTERNAL APIs) and relevant open-source examples (OPTIONAL EXTERNAL APIs) to offer specific, implementation-level guidance.

For each recommended API (internal or external), respond using this format:

---
**Source:** <file path or GitHub URL>  
**Summary:** <1–2 sentence summary of what the code does, based on filename and contents.>  
**Implementation Guidance:**  
- Explain how this code is related to the INPUT API functionality.  
- Reference specific function names, classes, or logic.  
- Avoid generic phrases — clearly map features from this code to possible components in the INPUT API.  
- If external, suggest how this repo might be used as a reference only (not directly imported).  
---

**Rules:**
- Be concise but technically detailed.
- For INTERNAL APIs: treat them as available for direct use.
- For EXTERNAL APIs: treat them as optional *inspiration only* — do not assume they are installed or imported.
- Avoid generalities like “create a task queue” unless directly supported by the source code.
- Do not mention proprietary APIs (e.g., Stripe, Twitter).
- Use only the provided materials.

### INPUT API  
{input_api}

### RECOMMENDED INTERNAL APIs (with code excerpts and summaries)  
{internal_apis}

### OPTIONAL EXTERNAL APIs (from public repositories or documentation)  
{external_apis}

**Final Instructions:**
- Include **all internal APIs** in your response unless clearly irrelevant.
- Include **one or two external APIs** if they offer concrete implementation ideas. Be sure to include the github url.
- Do **not** restate features (e.g., “this has user registration”); explain how they are implemented.
- Include **code examples** from the RECOMMENDED INTERNAL APIs where implementation details are relevant.
"""

# get user input and query vector db
user_input = input("Input an API description: ")
rag_response = find_similar_apis(collection=collection, text_input=user_input)
rag = parse_rag_response(rag_response)

# summarize and format internal APIs
internal_blocks = []
for path, doc in rag:
    code = read_code(path)
    truncated_code = code[:1500]
    input_summary = summary_prompt.format(path=path, code=truncated_code)
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
final_input = main_prompt.format(
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

    # set up prompt for merger to analyze input from mistral and llama
    merger_prompt = f"""
    You are an expert software assistant. Two AI models provided implementation guidance for the same API request.

    Your job is to merge the best parts of each response into a single, coherent, structured recommendation for the developer. Remove redundant content, correct hallucinations, and preserve all specific and helpful implementation suggestions.

    Each API block should follow this format:

    ---
    **Source:** <file path or GitHub URL>
    **Summary:** <what the code does>
    **Implementation Guidance:** <how it helps implement the INPUT API>
    ---

    ### INPUT API
    {user_input}

    ### Assistant 1 (Mistral) Output
    {mistral_text}

    ### Assistant 2 (LLaMA) Output
    {llama_text}
    """

    # generate with merger
    refiner_ids = merger_tokenizer(merger_prompt, return_tensors="pt").input_ids.to(merger_model.device)
    refiner_output = merger_model.generate(refiner_ids, max_new_tokens=3072)
    final_response = merger_tokenizer.decode(refiner_output[0][refiner_ids.shape[1]:], skip_special_tokens=True)

    # write output to output file
    with open("output.txt", "w") as f:
        f.write(final_response)
    print("Output saved to output.txt.")
