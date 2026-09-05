"""RAG chain: retrieve from faq/tickets/guides, then generate a grounded answer with Groq."""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from config import GROQ_API_KEY, GROQ_MODEL, LLM_TEMPERATURE
from retriever import retrieve

SYSTEM_PROMPT = """You are NovaCell's telecom customer-support assistant.

Answer the customer's question using ONLY the context provided below. Never use
outside knowledge, and never invent prices, policies, or facts that are not in
the context.

If the context does not contain enough information to answer confidently, say
so explicitly and direct the customer to call 611 or use the MyTelecom app.
Do not guess.

Keep answers concise, plain-language, and actionable (step-by-step where
relevant).

Context:
{context}
"""

_llm = None


def get_llm() -> ChatGroq:
    """Shared LLM singleton -- reused by intent.py and refund_agent.py too, so
    every caller gets the same temperature=0 / reasoning_effort="none" config
    rather than risking a second instance that forgets to suppress reasoning
    tokens (which would leak into a tool-loop message or a log line)."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=GROQ_API_KEY,
            model_kwargs={"reasoning_effort": "none"},
        )
    return _llm


def format_context(documents: list[Document]) -> str:
    if not documents:
        return "(no relevant documents found)"
    lines = []
    for doc in documents:
        source = doc.metadata.get("source", "UNKNOWN")
        doc_id = doc.metadata.get("id", "?")
        lines.append(f"[{source} | {doc_id}]\n{doc.page_content}")
    return "\n\n".join(lines)


def build_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{question}"),
        ]
    )
    return prompt | get_llm() | StrOutputParser()


_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        _chain = build_chain()
    return _chain


def get_sources(documents: list[Document]) -> list[dict]:
    return [
        {
            "source": doc.metadata.get("source", "UNKNOWN"),
            "id": doc.metadata.get("id", "?"),
            "content": doc.page_content,
        }
        for doc in documents
    ]


def answer_stream(question: str, history: list | None = None):
    """Retrieve context, then yield answer tokens. Returns (generator, sources).

    `history` (if given) only informs generation -- retrieval always searches
    on the raw current question, never on conversation context."""
    documents = retrieve(question)
    context = format_context(documents)
    sources = get_sources(documents)
    chain = _get_chain()
    token_stream = chain.stream({"question": question, "context": context, "history": history or []})
    return token_stream, sources
