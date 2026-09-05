"""Hard-coded, session-scoped simulated account data for the Refund Agent.

No real CRM/billing/auth — CURRENT_USER_ID stands in for an authenticated
session's user id and is never asked of the user (see agent_PRD.md FR-15-17).
Storage lives in st.session_state so each browser session gets its own
independent, resettable copy rather than one process-global dict shared
(and corrupted) across every concurrent visitor.
"""
import copy

import streamlit as st

CURRENT_USER_ID = "user_123"

USERS_TEMPLATE = {
    "user_123": {
        "name": "Rahul",
        "plan": "Pro",
        "plan_amount": 999,
        "recharges": [
            {
                "recharge_id": "rch_456",
                "recharge_amount": 999,
                "recharge_status": "completed",
                "recharge_age_days": 2,
                "refund_status": "not_refunded",
            },
            {
                "recharge_id": "rch_457",
                "recharge_amount": 499,
                "recharge_status": "completed",
                "recharge_age_days": 1,
                "refund_status": "not_refunded",
            },
        ],
    }
}


def get_store() -> dict:
    return st.session_state.setdefault("refund_users", copy.deepcopy(USERS_TEMPLATE))


def reset_store():
    st.session_state["refund_users"] = copy.deepcopy(USERS_TEMPLATE)
