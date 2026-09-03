"""Append-only interaction log (answers + thumbs up/down feedback) for FR-05a."""
import json
import time
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "interactions.jsonl"


def _append(record: dict):
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def log_answer(message_id: str, question: str, answer: str, sources: list[dict]):
    _append(
        {
            "type": "answer",
            "message_id": message_id,
            "timestamp": time.time(),
            "question": question,
            "answer": answer,
            "sources": sources,
        }
    )


def log_feedback(message_id: str, feedback: str):
    _append(
        {
            "type": "feedback",
            "message_id": message_id,
            "timestamp": time.time(),
            "feedback": feedback,
        }
    )
