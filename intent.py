"""Intent classification: requirement_inquiry (existing RAG) vs refund_request."""
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel

from chain import get_llm

SYSTEM_PROMPT = """Classify the customer's latest message into exactly one intent:

- requirement_inquiry: a general support question (connectivity, billing, SIM,
  roaming, voice, account, plans/pricing, or HOW to do something).
- refund_request: the customer wants a refund, cancellation, or reversal of a
  recharge/payment they already made.

A request to cancel or reverse a recharge is refund_request. A question about
HOW to cancel something is requirement_inquiry.

Examples:
"Why is my internet slow?" -> requirement_inquiry
"How do I cancel my auto-renewal?" -> requirement_inquiry
"I want a refund of ₹999." -> refund_request
"Please cancel my last recharge, I want my money back." -> refund_request
"""


class IntentResult(BaseModel):
    intent: Literal["requirement_inquiry", "refund_request"]


_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="history", optional=True),
                ("human", "{question}"),
            ]
        )
        _classifier = prompt | get_llm().with_structured_output(IntentResult)
    return _classifier


def classify_intent(question: str, history: list | None = None) -> str:
    result: IntentResult = _get_classifier().invoke({"question": question, "history": history or []})
    return result.intent
