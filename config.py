import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = str(BASE_DIR / "chroma_store")

FAQ_CSV = DATA_DIR / "faq.csv"
TICKETS_DB = DATA_DIR / "tickets.db"
GUIDE_PDF = DATA_DIR / "telecom_guide.pdf"
PLANS_JSON = DATA_DIR / "plans.json"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

COLLECTION_FAQ = "faq"
COLLECTION_TICKETS = "tickets"
COLLECTION_GUIDES = "guides"
COLLECTION_PLANS = "plans"

GUIDE_CHUNK_SIZE = 600
GUIDE_CHUNK_OVERLAP = 100

TOP_K_PER_COLLECTION = 3

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "qwen/qwen3.6-27b"
LLM_TEMPERATURE = 0
