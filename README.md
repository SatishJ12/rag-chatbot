# NovaCell Support Assistant

A Retrieval-Augmented Generation (RAG) chatbot that resolves common telecom
customer-support queries without live agent involvement. It answers questions
about mobile connectivity, billing, SIM management, roaming, voice issues, and
account management by grounding every response in NovaCell's own knowledge —
FAQ entries, resolved support tickets, and technical guides — and never
answers from the LLM's internal knowledge alone.

Built from the PRD in [PRD.md](PRD.md), based on the brief in
[PROBLEM_STATEMENT.txt](PROBLEM_STATEMENT.txt).

## Why this exists

Telecom support centres handle a high volume of repetitive, resolvable
queries (slow data, billing confusion, SIM errors, roaming setup) whose
answers already exist across three disconnected sources: a public FAQ, a
database of resolved tickets, and PDF user guides. There's no single surface
that lets a customer ask a plain-language question and get a trustworthy
answer drawn from all three at once. This bot is that surface — and when it
can't answer confidently from verified sources, it says so and directs the
customer to call 611 or use the MyTelecom app, rather than guessing.

## How it works

```
User question
     │
     ▼
Merged Retriever  (parallel invoke)
  ├── ChromaDB · faq        top-3 FAQ entries
  ├── ChromaDB · tickets    top-3 resolved ticket resolutions
  ├── ChromaDB · guides     top-3 PDF guide chunks
  └── ChromaDB · plans      top-3 plan/pricing entries
     │
     ▼  (12 context documents, source-labelled)
ChatPromptTemplate
  ├── system: telecom assistant persona + context injection
  └── human: user question
     │
     ▼
Qwen3.6-27B on Groq  (temperature=0, reasoning_effort="none")
     │
     ▼
StrOutputParser → streamed response to UI
```

- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`, run locally (no
  external embedding API cost)
- **Vector store**: ChromaDB, persisted to `chroma_store/`
- **LLM**: `qwen/qwen3.6-27b` via the Groq API
- **Framework**: LangChain (LCEL)
- **UI**: Streamlit

## Features

- Free-text chat with token-by-token streaming responses
- Sidebar of sample questions you can click to send instantly
- Every answer shows an expandable **Sources** section listing exactly which
  FAQ entries, tickets, and guide chunks it drew from
- 👍 / 👎 feedback on every answer, logged to `logs/interactions.jsonl`
- "Clear conversation" to reset the session
- A CLI REPL (`main.py`) for non-browser use

## Project layout

| File | Purpose |
|---|---|
| `ingest_faq.py` | Loads `data/faq.csv` into the `faq` ChromaDB collection |
| `ingest_tickets.py` | Loads resolved tickets from `data/tickets.db` into the `tickets` collection |
| `ingest_guides.py` | Chunks `data/telecom_guide.pdf` (600 chars, 100 overlap) into the `guides` collection |
| `ingest_plans.py` | Loads `data/plans.json` (plan and add-on pricing) into the `plans` collection |
| `retriever.py` | Fetches top-3 documents from each collection in parallel |
| `chain.py` | Builds the grounded-answer LCEL chain against Groq |
| `app.py` | Streamlit chat UI |
| `main.py` | CLI REPL |
| `logger.py` | Appends answers and feedback to `logs/interactions.jsonl` |
| `config.py` | Shared settings (models, paths, collection names) |

## Setup

Requires Python 3.11+ (this build was verified on 3.10.11 as well) and a
[Groq API key](https://console.groq.com) (free tier available).

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env               # then add your GROQ_API_KEY
```

Ingest the knowledge sources (run once, or again any time the source files
change — the ingest scripts are idempotent):

```bash
python ingest_faq.py
python ingest_tickets.py
python ingest_guides.py
python ingest_plans.py
```

## Running it

**Streamlit UI:**

```bash
streamlit run app.py
```

**CLI:**

```bash
python main.py
```

Type `quit` to exit the CLI session.

## Keeping the knowledge current

Support ops can update the bot's answers without an engineering release:

- Edit `data/faq.csv`, then re-run `python ingest_faq.py`
- Seed new resolved cases into `data/tickets.db`, then re-run `python ingest_tickets.py`
- Replace `data/telecom_guide.pdf`, then re-run `python ingest_guides.py`
- Edit `data/plans.json`, then re-run `python ingest_plans.py`

### Adding a new knowledge source

Per NFR-06 in the PRD, adding a source doesn't require touching the retrieval
or generation logic — the `plans` source above followed this exact path and
is a template for the next one:

1. Write `ingest_<name>.py` that loads the source, turns each item into a
   `Document` with `metadata={"source": "<LABEL>", "id": ..., ...}`, and
   writes it to its own ChromaDB collection (see `ingest_plans.py`).
2. Add the collection name to `config.py`.
3. Add it to the `COLLECTIONS` list in `retriever.py`.

`chain.py`'s prompt context and the UI's Sources display are both
source-agnostic — they read whatever `source`/`id` metadata each collection
provides, so no changes are needed there.

## Scope (v1)

This bot does **not** do live CRM/billing lookups, personalized account data,
ticket creation/escalation to a human queue, multi-turn conversational
memory in retrieval, or non-English languages — see [PRD.md](PRD.md) §4 and
§11 for the full list of non-goals and future iterations.
