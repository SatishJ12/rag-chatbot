"""Ingest data/telecom_guide.pdf into the `guides` ChromaDB collection. Idempotent: re-run any time the PDF changes."""
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHROMA_DIR, COLLECTION_GUIDES, GUIDE_CHUNK_OVERLAP, GUIDE_CHUNK_SIZE, GUIDE_PDF
from embeddings import get_embeddings


def load_guide_documents():
    loader = PyPDFLoader(str(GUIDE_PDF))
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=GUIDE_CHUNK_SIZE,
        chunk_overlap=GUIDE_CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)

    ids = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"GUIDE-{i}"
        chunk.metadata = {
            "source": "GUIDES",
            "id": chunk_id,
            "page": chunk.metadata.get("page", 0),
        }
        ids.append(chunk_id)
    return chunks, ids


def main():
    chunks, ids = load_guide_documents()

    store = Chroma(
        collection_name=COLLECTION_GUIDES,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    store.reset_collection()
    store.add_documents(documents=chunks, ids=ids)

    print(f"Ingested {len(chunks)} guide chunks into collection '{COLLECTION_GUIDES}'.")


if __name__ == "__main__":
    main()
