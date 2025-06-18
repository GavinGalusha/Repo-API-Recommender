import chromadb
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from web_search import search_for_microservice

#access database
chroma_client = chromadb.PersistentClient(path="/data/hamaraa/Repo-API-Recommender/src/Database/database.chroma")
collection = chroma_client.get_or_create_collection(name="my_collection")
print(collection.count())

#transformers method
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2", torch_dtype=torch.float16, device_map=device
)
 
def find_similar_apis(text_input, top_k=1):
    results = collection.query(
    query_texts=[text_input],
    n_results=top_k
    )
    return results

def parse_rag_response(rag_response):
    """
    Parses a RAG response and returns a list of tuples with (file, document) in order.
    """
    documents = rag_response['documents'][0]
    metadatas = rag_response['metadatas'][0]

    if len(documents) != len(metadatas):
        raise ValueError("Mismatch between number of documents and metadata entries.")

    result = []
    for doc, meta in zip(documents, metadatas):
        file = meta.get('file', 'UNKNOWN FILE')
        result.append((file, doc))

    return result

def read_code(filename):
    with open(filename, 'r') as f:
        code = f.read()
    return code

##### Experimental add ons
def chain_of_retrieval(
        query: str,
        *,
        max_depth: int = 3,
        top_k: int = 6,
        confidence_threshold: float = 0.25,
        verbose: bool = True,
):
    """
    Iteratively retrieves code snippets until either:
      • confidence ≥ threshold   OR
      • depth == max_depth
    Returns a list of (file, document) tuples (deduplicated, ordered by first appearance).
    """
    def _chromadb_confidence(distances):
        """
        Chroma returns cosine *distances* (0 = identical, 2 = opposite).
        Map to similarity in [0,1] and grab the best.
        """
        if not distances:
            return 0.0
        sims = [1 - d/2 for d in distances]    
        return max(sims)
    aggregated = []              
    seen_ids   = set()         
    current_q  = query           

    for depth in range(max_depth):
        if verbose:
            print(f"\n[CoR] Depth {depth+1}  |  query →  {current_q!r}")
        
        
        rag = collection.query(query_texts=[current_q], n_results=top_k, include=["metadatas"])
        conf  = _chromadb_confidence(rag["distances"][0])
        pairs = parse_rag_response(rag)
        for (file, doc), uuid in zip(pairs, rag["ids"][0]):
            if uuid not in seen_ids:
                aggregated.append((file, doc))
                seen_ids.add(uuid)

        if verbose:
            print(f"[CoR]   ↳ confidence = {conf:.3f}   |   +{len(pairs)} hits   |   total={len(aggregated)}")

        # ------- Early stop if we’re confident enough -----
        if conf >= confidence_threshold:
            break
        # ------- 3️⃣ Ask the LLM to refine the query ------
        refine_prompt = (
            "You are an expert search assistant for code retrieval.\n"
            "User need: {need}\n"
            "Top results so far:\n{hits}\n\n"
            "Produce a *single* improved search query that will retrieve "
            "more specific or missing implementation details. "
            "Do NOT add commentary—only the query."
        ).format(
            need=query,
            hits="\n".join([doc[:120] for (_, doc) in pairs[:3]])
        )

        with torch.no_grad():
            in_ids = tokenizer(refine_prompt, return_tensors="pt").to(model.device)
            out    = model.generate(**in_ids, max_new_tokens=32, temperature=0.2)
        current_q = tokenizer.decode(out[0][in_ids.input_ids.shape[1]:],
                                     skip_special_tokens=True).strip()

    return aggregated

##########################













prompt = """
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

### RECOMMENDED INTERNAL APIs (with code excerpts)  
{recommended_apis}

### OPTIONAL EXTERNAL APIs (from public repositories or documentation)  
{external_apis}



**Final Instructions:**
- Include **all internal APIs** in your response unless clearly irrelevant.
- Include **one or two external APIs** if they offer concrete implementation ideas. Be sure to include the github url.
- Do **not** restate features (e.g., “this has user registration”); explain how they are implemented.
"""






user_input = input("Input an api description to receive similar api's that could be useful: \n")

'''
rag_response = find_similar_apis(user_input)
rag_response = parse_rag_response(rag_response)
'''
rag_response = chain_of_retrieval(user_input)


response = [] 
for path, summary in rag_response:
    code = read_code(path)
    response.append({
        "path": path,
        "summary": summary,
        "code": code
    })

formatted_apis = ""
for r in response:
    formatted_apis += f"\n---\nPath: {r['path']}\nSummary: {r['summary']}\nCode:\n{r['code'][:1000]}\n"

public_repo_info = search_for_microservice(user_input)

input_text = prompt.format(
    input_api = user_input,
    recommended_apis = formatted_apis,
    external_apis = public_repo_info
)
print(input_text)

input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(model.device)
print('generating model output...')
outputs = model.generate(input_ids, max_new_tokens=2048)

print("final structured output:")
generated_tokens = outputs[0][input_ids.shape[1]:]
structured_output = tokenizer.decode(generated_tokens, skip_special_tokens=True)
with open('output.txt', 'w') as f:
    f.write(structured_output)
