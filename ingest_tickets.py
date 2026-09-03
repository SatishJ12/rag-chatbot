"""Ingest data/tickets.db resolved tickets into the `tickets` ChromaDB collection. Idempotent: re-run any time after seeding new tickets."""
import sqlite3

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DIR, COLLECTION_TICKETS, TICKETS_DB
from embeddings import get_embeddings


def load_ticket_documents() -> list[Document]:
    conn = sqlite3.connect(TICKETS_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE status = 'resolved'")
    rows = cur.fetchall()
    conn.close()

    documents = []
    for row in rows:
        content = (
            f"Issue: {row['issue_type']}\n"
            f"Description: {row['description']}\n"
            f"Resolution: {row['resolution']}"
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": "TICKETS",
                    "id": row["ticket_id"],
                    "category": row["category"],
                },
            )
        )
    return documents


def main():
    documents = load_ticket_documents()
    ids = [doc.metadata["id"] for doc in documents]

    store = Chroma(
        collection_name=COLLECTION_TICKETS,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    store.reset_collection()
    store.add_documents(documents=documents, ids=ids)

    print(f"Ingested {len(documents)} resolved tickets into collection '{COLLECTION_TICKETS}'.")


if __name__ == "__main__":
    main()
