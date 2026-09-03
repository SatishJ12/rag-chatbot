# Product Requirements Document — RAG Telecom Customer Care Chatbot

**Date:** 2026-08-30  
**Author:** Dhaval Patel

---

## 1. Overview

A Retrieval-Augmented Generation (RAG) chatbot that resolves common telecom customer-support queries without live agent involvement. The bot answers questions about mobile connectivity, billing, SIM management, roaming, voice issues, and account management by grounding every response in curated knowledge — never hallucinating policy or pricing details.

---

## 2. Problem Statement

Telecom support centres handle a high volume of repetitive, resolvable queries (slow data, incorrect billing, SIM errors, roaming setup). These queries:

- Drain agent capacity from complex escalations
- Follow predictable resolution paths that are well documented internally
- Frustrate customers who wait on hold for answers available in an FAQ

There is no self-serve channel that combines FAQ lookup, historical resolution patterns, and technical guide content into a single, conversational interface.

---

## 3. Goals

| Goal | Metric |
|---|---|
| Deflect Tier-1 support queries | >70% of sample questions answered without "call 611" escalation |
| Ground responses in verified knowledge | 0 answers generated from LLM-internal knowledge alone |
| Reduce time-to-answer | Under 10 seconds end-to-end (retrieval + generation) |
| Accessible to non-technical users | No login, no setup; works in a browser |

---

## 4. Non-Goals

- Live CRM or billing system integration (real-time account data)
- Ticket creation or case management
- Authentication / personalised account lookup
- Languages other than English (v1)
- Mobile native app

---

## 5. Users

**Primary:** Telecom subscribers with Tier-1 support questions (connectivity issues, billing confusion, SIM problems, roaming queries).

**Secondary:** Telecom support operations teams who maintain the knowledge sources (FAQ CSV, ticket database, PDF guides) that power the bot.

---

## 6. Functional Requirements

### 6.1 Conversational Interface

| ID | Requirement |
|---|---|
| FR-01 | Users can type a free-text question and receive a contextually grounded answer |
| FR-02 | Users can click a sample question from the sidebar to send it instantly |
| FR-03 | Conversation history is maintained within a session |
| FR-04 | A "Clear conversation" button resets the session |
| FR-05 | Responses stream token-by-token (no full-page wait) |
| FR-05a | 👍 / 👎 control on every assistant answer, written to the interaction log |


### 6.2 Knowledge Retrieval

| ID | Requirement |
|---|---|
| FR-06 | The system retrieves from three parallel knowledge collections: FAQ entries, resolved support tickets, and telecom guide chunks |
| FR-07 | Top-3 documents are fetched from each collection (9 context documents total per query) |
| FR-08 | Retrieved documents are labelled by source (FAQ / TICKETS / GUIDES) in the prompt context |
| FR-09 | Embeddings are generated locally using `all-MiniLM-L6-v2` (no external embedding API cost) |

### 6.3 Answer Generation

| ID | Requirement |
|---|---|
| FR-10 | The LLM must use **only** retrieved context to answer — no internal knowledge fallback |
| FR-11 | When context is insufficient, the bot explicitly says so and directs the user to call 611 or use the MyTelecom app |
| FR-12 | LLM temperature is 0 (deterministic, factual output) |
| FR-13 | Model: `qwen/qwen3.6-27b` served via Groq API with reasoning_effort="none" |
| FR-13a | Every answer renders an expandable Sources section listing each retrieved document used (FAQ / TICKET / GUIDE, with identifier) alongside the response |


### 6.4 Knowledge Ingestion

| ID | Requirement |
|---|---|
| FR-14 | FAQ entries are loaded from `data/faq.csv` (1 row = 1 vector document) |
| FR-15 | Resolved tickets are loaded from `data/tickets.db` (SQLite; 1 ticket = 1 vector document) |
| FR-16 | PDF guide is chunked at 600 characters with 100-character overlap before embedding |
| FR-17 | All collections persist to `chroma_store/` on disk; ingest scripts are idempotent re-runs |

### 6.5 CLI Interface

| ID | Requirement |
|---|---|
| FR-18 | A CLI mode (`main.py`) provides an interactive REPL for non-browser use |
| FR-19 | Typing `quit` exits the CLI session |

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | **Latency**: End-to-end response (first token) under 3 seconds on a standard laptop with internet access |
| NFR-02 | **Offline embeddings**: The embedding model runs locally; no embedding calls to external APIs |
| NFR-03 | **No credentials in code**: API keys are loaded from `.env`; `.env.example` ships without secrets |
| NFR-04 | **Isolated environment**: All dependencies install into a project-local virtual environment .venv in the working folder. Never install into a global or shared interpreter. |
| NFR-04a | **Portability**: Runs on Python 3.11+ (tested on 3.13.5) via `pip install -r requirements.txt`; no OS-specific dependencies |
| NFR-05 | **Restartability**: Chroma store persists to disk; the app does not re-ingest on each start |
| NFR-06 | **Extensibility**: New knowledge sources can be added by writing a new `ingest_*.py` and registering the collection in `retriever.py` |

---

## 8. Data Sources

| Collection | Source | Format | Documents |
|---|---|---|---|
| `faq` | `data/faq.csv` | CSV (question, answer pairs) | 1 per row |
| `tickets` | `data/tickets.db` | SQLite (`tickets` table) | 1 per resolved ticket |
| `guides` | `data/telecom_guide.pdf` | PDF, chunked | 600-char chunks, 100-char overlap |

### Ticket Categories Covered

`connectivity`, `data`, `roaming`, `sim`, `billing`, `voice`, `device`, `account`

### Sample Topics

- Mobile internet loss, slow 4G, intermittent signal drops, network outages
- Unexpected roaming charges, no service abroad
- SIM not recognised, eSIM activation failure, number porting delays
- Double billing, plan auto-renewal at wrong price, itemised bill download failure
- Call barring, echo on calls, VoLTE incompatibility
- App login failures, unauthorised plan changes

---

## 9. System Architecture

```
User question
     │
     ▼
Merged Retriever  (parallel invoke)
  ├── ChromaDB · faq        top-3 FAQ entries
  ├── ChromaDB · tickets    top-3 resolved ticket resolutions
  └── ChromaDB · guides     top-3 PDF guide chunks
     │
     ▼  (9 context documents, source-labelled)
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

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (local, HuggingFace)  
**Vector store:** ChromaDB (persisted to `chroma_store/`)  
**LLM:** `qwen/qwen3.6-27b` via Groq API with reasoning_effort="none" 
**Framework:** LangChain (LCEL chain)  
**UI:** Streamlit

---

## 10. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | Customer | Ask why my internet is slow and get step-by-step guidance | I can fix the issue without calling support |
| US-02 | Customer | Ask about unexpected charges on my bill | I understand what I was billed for |
| US-03 | Customer | Ask how to activate roaming before a trip | I don't get stranded without service abroad |
| US-04 | Customer | Click a sample question | I can explore the bot's capabilities without typing |
| US-05 | Customer | Clear the conversation | I can start a new query without prior context influencing answers |
| US-06 | Support operator | Update `faq.csv` and re-run `ingest_faq.py` | The bot reflects the latest policies without redeployment |
| US-07 | Support operator | Seed new tickets into `tickets.db` | Real resolved cases improve retrieval quality over time |

---

## 11. Out-of-Scope (Future Iterations)

- **Account authentication** — personalised answers (e.g., "your current balance is…")
- **Live CRM integration** — real-time plan, usage, and billing data
- **Ticket creation** — escalating unresolved queries to a human agent queue
- **Multi-turn memory** — conversation history influencing retrieval (RAG with chat history)
- **Multilingual support** — non-English queries
- **Re-ranking** — cross-encoder re-ranking of retrieved documents before generation
- **Hybrid search** — combining dense vector search with BM25 keyword search
- **Evaluation harness** — automated RAGAS or similar metrics for retrieval/generation quality

---

## 12. Dependencies & Constraints

> **Build inside a project-local virtual environment. Never install into the global or
> shared interpreter.**

| Item | Detail |
|---|---|
| Groq API key | Required; free tier available at console.groq.com |
| HuggingFace embedding model | Auto-downloaded on first run; ~90 MB |
| Python 3.11+ | Minimum runtime version |
| `uv` or `pip` | Package management |
| Disk space | ChromaDB store grows with ingested data |
| Network | Groq API calls require internet access; embeddings are local |
