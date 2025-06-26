# create summarization prompt
def create_summary_prompt(path, code) -> str:
    return f"""
    Summarize the purpose of this internal API. Just say what it does.

    Path: {path}
    Code:
    {code}
    """

# create implementation prompt
def create_implementation_prompt(input_api, internal_apis, external_apis) -> str:
    return f"""
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

def create_merger_prompt(user_input, mistral_text, llama_text) -> str:
    return f"""
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
