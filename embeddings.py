import threading

from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL

_embeddings = None
_lock = threading.Lock()


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        with _lock:
            if _embeddings is None:
                _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings
