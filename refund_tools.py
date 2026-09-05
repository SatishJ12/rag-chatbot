"""Refund tools.

get_user_account and validate_refund are @tool-decorated and meant to be
bound to the LLM (agent_PRD.md FR-19/20) -- they are read-only and their
eligibility logic is fully deterministic, so the LLM can call them without
ever being trusted to decide eligibility itself (FR-29/30).

process_refund and submit_to_support are deliberately plain functions, never
decorated as @tool and never bound to the LLM (FR-23a). Only application
code (refund_agent.py) invokes them, and only after validation + explicit
human confirmation.
"""
import uuid

from langchain_core.tools import tool

from config import REFUND_WINDOW_DAYS
from refund_data import CURRENT_USER_ID, get_store


def _resolve_user_id(user_id: str) -> tuple[str, bool]:
    """Always use the real session user, regardless of what the LLM supplied (GR-03)."""
    overridden = user_id != CURRENT_USER_ID
    return CURRENT_USER_ID, overridden


def _is_eligible_for_refund(recharge: dict) -> bool:
    return (
        recharge["recharge_status"] == "completed"
        and recharge["refund_status"] == "not_refunded"
        and recharge["recharge_age_days"] <= REFUND_WINDOW_DAYS
    )


def _find_recharge_by_amount(user: dict, amount: float) -> dict | None:
    for recharge in user["recharges"]:
        if recharge["recharge_amount"] == amount:
            return recharge
    return None


@tool
def get_user_account(user_id: str) -> dict:
    """Retrieve the current customer's account and recharge history.

    Always call this with the current session's user id. Each recharge in
    the response includes a precomputed `eligible_for_refund` boolean -- use
    it to answer questions about which recharges could be refunded; do not
    compute eligibility yourself from status/age.
    """
    real_user_id, _ = _resolve_user_id(user_id)
    store = get_store()
    user = store.get(real_user_id)
    if user is None:
        return {"error": "user not found"}

    recharges = [
        {**r, "eligible_for_refund": _is_eligible_for_refund(r)} for r in user["recharges"]
    ]
    return {"name": user["name"], "plan": user["plan"], "plan_amount": user["plan_amount"], "recharges": recharges}


@tool
def validate_refund(user_id: str, amount: float) -> dict:
    """Deterministically validate whether a refund of `amount` is eligible.

    Always call this fresh for the current requested amount -- never rely on
    a conclusion stated earlier in the conversation. This tool computes
    eligibility in code; you must not decide eligibility yourself.
    """
    real_user_id, _ = _resolve_user_id(user_id)
    store = get_store()
    user = store.get(real_user_id)
    if user is None:
        return {"eligible": False, "reason": "user not found", "requested_amount": amount, "recharge_amount": None, "recharge_id": None}

    recharge = _find_recharge_by_amount(user, amount)
    if recharge is None:
        return {
            "eligible": False,
            "reason": "no recharge found for that amount",
            "requested_amount": amount,
            "recharge_amount": None,
            "recharge_id": None,
        }

    base = {
        "requested_amount": amount,
        "recharge_amount": recharge["recharge_amount"],
        "recharge_id": recharge["recharge_id"],
    }

    if recharge["recharge_status"] != "completed":
        return {**base, "eligible": False, "reason": "recharge is not completed"}
    if recharge["recharge_age_days"] > REFUND_WINDOW_DAYS:
        return {**base, "eligible": False, "reason": f"recharge is outside the {REFUND_WINDOW_DAYS}-day refund window"}
    if amount <= 0:
        return {**base, "eligible": False, "reason": "requested amount must be greater than zero"}
    if amount > recharge["recharge_amount"]:
        return {**base, "eligible": False, "reason": "requested amount exceeds recharge amount"}
    if recharge["refund_status"] == "refunded":
        return {**base, "eligible": False, "reason": "recharge already refunded"}

    return {**base, "eligible": True, "reason": "Refund is eligible."}


def process_refund(user_id: str, amount: float) -> dict:
    """Simulate executing a refund. NOT an LLM-callable tool (FR-23a).

    Only ever called by application code, only after validate_refund
    returned eligible=True and the user gave explicit confirmation.
    """
    real_user_id, _ = _resolve_user_id(user_id)
    store = get_store()
    user = store[real_user_id]
    recharge = _find_recharge_by_amount(user, amount)
    recharge["refund_status"] = "refunded"
    return {
        "success": True,
        "refund_id": f"ref_{uuid.uuid4().hex[:6]}",
        "amount": amount,
        "status": "refunded",
    }


def submit_to_support(user_id: str, amount: float) -> dict:
    """Simulate submitting a refund above the approval limit for human review.

    NOT an LLM-callable tool (FR-23a). Does not mutate refund_status and does
    not simulate the Support Team's eventual decision (FR-40a / GR-09).
    """
    real_user_id, _ = _resolve_user_id(user_id)
    return {
        "submitted": True,
        "user_id": real_user_id,
        "amount": amount,
        "reference": f"sup_{uuid.uuid4().hex[:6]}",
    }
