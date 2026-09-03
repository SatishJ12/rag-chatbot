"""Merged retriever over the faq / tickets / guides ChromaDB collections.

To add a new knowledge source: write ingest_<name>.py that persists a collection
under CHROMA_DIR, add its collection name to config.py, and add it to COLLECTIONS below.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import (
    CHROMA_DIR,
    COLLECTION_FAQ,
    COLLECTION_GUIDES,
    COLLECTION_PLANS,
    COLLECTION_TICKETS,
    TOP_K_PER_COLLECTION,
)
from embeddings import get_embeddings

COLLECTIONS = [COLLECTION_FAQ, COLLECTION_TICKETS, COLLECTION_GUIDES, COLLECTION_PLANS]

_stores = {}
_lock = threading.Lock()


def _get_store(collection_name: str) -> Chroma:
    if collection_name not in _stores:
        with _lock:
            if collection_name not in _stores:
                _stores[collection_name] = Chroma(
                    collection_name=collection_name,
                    embedding_function=get_embeddings(),
                    persist_directory=CHROMA_DIR,
                )
    return _stores[collection_name]


def _search_collection(collection_name: str, query: str) -> list[Document]:
    store = _get_store(collection_name)
    return store.similarity_search(query, k=TOP_K_PER_COLLECTION)


def retrieve(query: str) -> list[Document]:
    """Fetch top-K documents from each collection in parallel; returns them source-labelled."""
    with ThreadPoolExecutor(max_workers=len(COLLECTIONS)) as executor:
        futures = [executor.submit(_search_collection, name, query) for name in COLLECTIONS]
        results = [f.result() for f in futures]

    documents = []
    for batch in results:
        documents.extend(batch)
    return documents
