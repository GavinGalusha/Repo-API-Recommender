# Repo‑API‑Recommender

A research‑grade toolkit that combines Retrieval‑Augmented Generation (RAG), large‑language‑model ensembles, and lightweight web search to **recommend implementation strategies for REST‑style microservices**.  Give it a codebase, a single file, or a plain‑text description of an API and it will analyse what you already have, hunt for similar public services, and draft a concrete plan of attack—all while remaining fully offline *or* optionally enriching results with the public web.

> **Heads‑up 🚀** – This README focuses on the main entry points developers will care about on day one. The repository contains many more helpers, prompt templates, tests, CI scripts, notebooks, and Docker artefacts that are intentionally left out here for brevity; explore the tree for the full picture.

---

## ✨ Key Capabilities

| Mode                 | Script               | What it does                                                                                                |
| -------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Hybrid (default)** | `main.py`            | Vector‑DB RAG **plus** optional web search and/or model ensembles. Ideal for maximum context and quality.   |
| **RAG only**         | `rag_only.py`        | Purely leverages your *internal* codebase via a Chroma vector store—no external calls, no ensembles.        |
| **Web‑search only**  | `web_search_only.py` | Skips the vector store and asks the web for inspiration when your repo is empty or green‑field.             |
| **Zero‑shot**        | `zero_shot.py`       | Generates an implementation plan from a hand‑written API description—fastest turnaround, no dependencies.   |
| **Ensemble only**    | `ensemble_only.py`   | Benchmarks three different models (Mistral, LLaMA 3, Mixtral) and merges their answers for higher accuracy. |

All scripts share a consistent CLI so you can swap strategies with minimal friction.

---

## 🗂️ Input File: `apis.txt`

A convenience file that holds one or more **plain‑text API descriptions**—one per line. Any of the scripts can accept it via:

```bash
python main.py --description < apis.txt
```

Use this when you don’t have code on disk but still want the recommender’s insights.

---

## 🔧 Installation

```bash
# 1. Clone the repo
$ git clone https://github.com/your‑org/repo‑api‑recommender.git
$ cd repo‑api‑recommender

# 2. Create a fresh virtual environment (recommended)
$ python -m venv .venv && source .venv/bin/activate

# 3. Install core and optional dependencies
$ pip install -r requirements.txt        # base libs
$ pip install -r requirements‑extras.txt  # CUDA + web search + evaluation (optional)
```

> **GPU note** – All scripts auto‑detect a CUDA device and fall back to CPU if necessary. For large models you’ll want at least 12 GB of VRAM.

---

## 🚀 Quick‑start Examples

### 1. Analyse an entire repository

```bash
python main.py --repo_path /path/to/monorepo
```

### 2. Work on a single file

```bash
python rag_only.py --file_path src/service/users.py
```

### 3. Brainstorm from scratch (zero‑shot)

```bash
python zero_shot.py --description
# Then paste or pipe the API spec
```

### 4. Compare ensemble answers

```bash
python ensemble_only.py --repo_path . --ensemble
```

Outputs are written to `output.txt` (or `output_rag.txt` etc.) in the project root by default.

---


## 🧩 How It Works (in 30 seconds)

1. **Code Crawling** – `walker.py` tokenises your repo, extracts REST endpoints, and summarises them to JSON.
2. **Vector Lookup** – Summaries are embedded and matched against a curated Chroma collection of microservice patterns.
3. **Prompt Building** – Internal matches, external web snippets, and your original API spec are woven into a single implementation prompt.
4. **LLM Generation** – Depending on flags, one or more models (Mistral 7B, LLaMA 3 8B, Mixtral 8×7B) draft the response.
5. **(Optional) Ensemble Merging** – Divergent model answers are reconciled for robustness.

---



## ⚖️ Licence

Distributed under the MIT Licence. See `LICENCE` for more information.

---


