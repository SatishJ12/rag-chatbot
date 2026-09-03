"""Ingest data/plans.json into the `plans` ChromaDB collection. Idempotent: re-run any time plan pricing changes."""
import json

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import CHROMA_DIR, COLLECTION_PLANS, PLANS_JSON
from embeddings import get_embeddings


def _format_price(plan: dict) -> str:
    if "monthly_price" in plan:
        price = f"${plan['monthly_price']:.2f}/month"
        if plan.get("price_per_line"):
            price += f" (${plan['price_per_line']:.2f} per line, {plan.get('lines_included')} lines included)"
        return price
    return f"${plan['price']:.2f} {plan.get('price_unit', '')}".strip()


def _format_data(plan: dict) -> str:
    if plan.get("data_unlimited"):
        return "unlimited data"
    data_gb = plan.get("data_gb")
    if data_gb is None:
        return "no dedicated data allowance"
    return f"{data_gb} GB" if isinstance(data_gb, (int, float)) else str(data_gb)


def _plan_to_text(plan: dict, currency: str) -> str:
    lines = [
        f"Plan: {plan['name']} ({plan['id']})",
        f"Type: {plan.get('type', plan.get('category', 'n/a'))}",
        f"Price: {_format_price(plan)} {currency}",
        f"Data: {_format_data(plan)}",
    ]
    for label, key in [
        ("Talk", "talk_minutes"),
        ("Texts", "texts"),
        ("Hotspot", "hotspot_gb"),
        ("Network", "network"),
        ("Contract", "contract"),
        ("Coverage", "coverage"),
        ("Eligibility", "eligibility"),
        ("Intro offer", "intro_offer"),
        ("Best for", "best_for"),
    ]:
        value = plan.get(key)
        if value not in (None, ""):
            lines.append(f"{label}: {value}")
    if plan.get("features"):
        lines.append("Features: " + "; ".join(plan["features"]))
    return "\n".join(lines)


def load_plan_documents() -> list[Document]:
    with open(PLANS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    currency = data.get("currency", "USD")
    documents = []
    for plan in data["plans"]:
        documents.append(
            Document(
                page_content=_plan_to_text(plan, currency),
                metadata={
                    "source": "PLANS",
                    "id": plan["id"],
                    "category": plan.get("category", plan.get("type", "")),
                },
            )
        )
    return documents


def main():
    documents = load_plan_documents()
    ids = [doc.metadata["id"] for doc in documents]

    store = Chroma(
        collection_name=COLLECTION_PLANS,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    store.reset_collection()
    store.add_documents(documents=documents, ids=ids)

    print(f"Ingested {len(documents)} plans into collection '{COLLECTION_PLANS}'.")


if __name__ == "__main__":
    main()
