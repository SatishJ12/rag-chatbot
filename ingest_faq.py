"""Ingest data/faq.csv into the `faq` ChromaDB collection. Idempotent: re-run any time after editing the CSV."""
import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DIR, COLLECTION_FAQ, FAQ_CSV
from embeddings import get_embeddings


def load_faq_documents() -> list[Document]:
    df = pd.read_csv(FAQ_CSV)
    documents = []
    for _, row in df.iterrows():
        content = f"Question: {row['question']}\nAnswer: {row['answer']}"
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": "FAQ",
                    "id": f"FAQ-{row['id']}",
                    "category": row.get("category", ""),
                },
            )
        )
    return documents


def main():
    documents = load_faq_documents()
    ids = [doc.metadata["id"] for doc in documents]

    store = Chroma(
        collection_name=COLLECTION_FAQ,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    store.reset_collection()
    store.add_documents(documents=documents, ids=ids)

    print(f"Ingested {len(documents)} FAQ entries into collection '{COLLECTION_FAQ}'.")


if __name__ == "__main__":
    main()
