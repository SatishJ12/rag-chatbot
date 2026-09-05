# Product Requirements Document — Agentic Refund Capability

**Date:** 2026-09-03
**Author:** Dhaval Patel

---

## 1. Overview

Extend the existing RAG Telecom Customer Care Chatbot with a simple agentic refund capability.

Add intent detection with two intents:

1. `requirement_inquiry` — continues through the existing RAG pipeline.
2. `refund_request` — routes to a Refund Agent.

The Refund Agent retrieves the user's recharge details, validates the refund request, asks for confirmation, and executes a simulated refund.

User/account data is hard-coded for this iteration. No real CRM, billing, authentication, or payment integration is required.

---

## 2. Problem Statement

The existing chatbot can answer telecom support questions but cannot perform customer actions.

For refund requests, the system needs to:

* Identify the request as a refund.
* Retrieve the user's recharge details.
* Validate the requested refund.
* Prevent invalid refunds.
* Get explicit user confirmation.
* Execute a simulated refund.
* Return the result to the user.

---

## 3. Goals

| Goal                         | Metric                                                             |
| ---------------------------- | ------------------------------------------------------------------ |
| Add intent routing           | 2 supported intents: requirement inquiry and refund request        |
| Preserve existing RAG        | Requirement inquiries continue through the existing pipeline       |
| Demonstrate agentic behavior | Refund requests handled by a tool-using agent                      |
| Add refund guardrails        | Deterministic validation before refund execution                   |
| Add human approval           | Explicit confirmation required before refund                       |
| Keep implementation simple   | Hard-coded data; simulated refund; no external billing integration |

---

## 4. Non-Goals

* Real CRM integration
* Real billing system integration
* Real payment/refund provider integration
* Real user authentication
* Real customer database
* Real financial transactions
* Multiple agents
* Multi-agent orchestration
* Production fraud detection
* Production payment security
* Automatic refund without confirmation
* Changes to the existing RAG retrieval pipeline

The refund execution is simulated only.

---

## 5. Users

**Primary:** Telecom subscribers seeking answers to customer care questions or requesting cancellation or reversal of a recent recharge.

---

## 6. Functional Requirements

### 6.1 Intent Detection

| ID    | Requirement                                                                |
| ----- | -------------------------------------------------------------------------- |
| FR-01 | Classify each user request as `requirement_inquiry` or `refund_request`    |
| FR-02 | `requirement_inquiry` continues through the existing RAG pipeline          |
| FR-03 | `refund_request` is routed to the Refund Agent                             |
| FR-04 | Intent detection should use the existing LLM configuration where practical |
| FR-05 | The classifier should return a structured intent value                     |
| FR-05a | A request to cancel or reverse a recharge is `refund_request`; a question about how to cancel is `requirement_inquiry` |

Example:

```text
Why is my internet slow?
→ requirement_inquiry
```

```text
I want a refund of ₹999.
→ refund_request
```

---

### 6.2 Refund Agent

| ID    | Requirement                                                                  |
| ----- | ---------------------------------------------------------------------------- |
| FR-06 | Refund requests are handled by a tool-using Refund Agent                     |
| FR-07 | The agent determines the requested refund amount                             |
| FR-08 | The agent retrieves the user's account/recharge information                  |
| FR-09 | The agent validates the refund before attempting execution                   |
| FR-10 | The agent asks for missing information when required                         |
| FR-11 | The agent requests explicit confirmation before executing an eligible refund |
| FR-12 | The agent executes the simulated refund only after confirmation              |
| FR-13 | The agent returns a clear success or rejection message                       |

---

### 6.3 Simulated User Data

| ID    | Requirement                                                                   |
| ----- | ----------------------------------------------------------------------------- |
| FR-14 | Create a small hard-coded user/account data source                            |
| FR-15 | Use a hard-coded user ID for the demonstration                                |
| FR-16 | Treat the hard-coded user ID as if it came from authenticated session context |
| FR-17 | The user must not be asked to provide the user ID                             |
| FR-18 | Include recharge amount, status, age, and refund status in the simulated data |
| FR-18a | Give the demonstration user two recharges: ₹499 and ₹999 |

Example:

```python
USERS = {
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
                "refund_status": "not_refunded"
            },
            {
                "recharge_id": "rch_457",
                "recharge_amount": 499,
                "recharge_status": "completed",
                "recharge_age_days": 1,
                "refund_status": "not_refunded"
            }
        ]
    }
}
```

The ₹499 recharge is at the approval limit and can be refunded by the application.
The ₹999 recharge is above it and goes to the Support Team (see 6.7).


---

### 6.4 Refund Tools

| ID    | Requirement                                       |
| ----- | ------------------------------------------------- |
| FR-19 | Provide a `get_user_account(user_id)` tool        |
| FR-20 | Provide a `validate_refund(user_id, amount)` tool |
| FR-21 | Provide a `process_refund(user_id, amount)` tool  |
| FR-21a | Provide a `submit_to_support(user_id, amount)` tool |
| FR-22 | Tools return structured results                   |
| FR-23 | `process_refund` only performs a simulated refund |
| FR-23a | `process_refund` and `submit_to_support` must not be exposed to the LLM as callable tools |

---

### 6.5 Refund Validation

| ID    | Requirement                                                                      |
| ----- | -------------------------------------------------------------------------------- |
| FR-24 | Recharge must have `completed` status                                            |
| FR-25 | Recharge must be within 7 days                                                   |
| FR-26 | Requested amount must be greater than zero                                       |
| FR-27 | Requested amount must not exceed the recharge amount                             |
| FR-27a | When the user has more than one recharge, select which recharge the refund applies to deterministically. An amount matching a recharge exactly identifies that recharge, even if it is already refunded |
| FR-28 | Already-refunded recharge cannot be refunded again                               |
| FR-28a | A refund consumes the whole recharge; no remaining balance is tracked           |
| FR-29 | Validation rules must be implemented deterministically in application/tool logic |
| FR-30 | The LLM must not independently determine refund eligibility                      |

Example validation result:

```python
{
    "eligible": True,
    "reason": "Refund is eligible.",
    "requested_amount": 499,
    "recharge_amount": 499,
    "recharge_id": "rch_457"
}
```

Validation decides eligibility only. Whether an eligible refund can be executed here
is a separate question, answered by the approval limit in 6.7.

---

### 6.6 Refund Execution

| ID    | Requirement                                                           |
| ----- | --------------------------------------------------------------------- |
| FR-31 | `process_refund` must only be called after successful validation      |
| FR-32 | `process_refund` must only be called after explicit user confirmation |
| FR-33 | Successful execution updates the simulated refund status              |
| FR-34 | Successful execution returns a simulated refund reference             |
| FR-35 | No real payment or billing API is called                              |

Example:

```python
{
    "success": True,
    "refund_id": "ref_789",
    "amount": 499,
    "status": "refunded"
}
```

---

### 6.7 Refund Approval

| ID    | Requirement                                                                                                                                                                        |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-36 | Refunds of ₹499 or less require explicit user confirmation before execution                                                                                                        |
| FR-36a | The ₹499 limit must be enforced in application code, not by the LLM                                                                                                               |
| FR-36b | The original refund request is not sufficient confirmation                                                                                                                        |
| FR-36c | Only an explicit confirmation such as "Yes, proceed" allows execution                                                                                                             |
| FR-36d | If the user rejects the refund, no refund is executed                                                                                                                             |
| FR-36e | Ambiguous confirmation must not trigger execution; ask again instead                                                                                                              |
| FR-37 | Refunds greater than ₹499 must not be processed automatically                                                                                                                      |
| FR-38 | For refunds greater than ₹499, the Refund Agent submits the refund request to the Support Team for review                                                                          |
| FR-39 | After submission, the Refund Agent must not call `process_refund`                                                                                                                  |
| FR-40 | For refunds greater than ₹499, the agent responds that the request has been submitted to the Support Team, who will review it and process the request or take the necessary action |
| FR-40a | The agent must not claim that the refund has been approved, rejected, or processed by the Support Team. The Support Team review and subsequent processing are outside the scope of this application                                                                                        |

**Flow:**

```text
Refund ≤ ₹499
→ Validate
→ Ask user confirmation
→ User confirms
→ process_refund()
```

```text
Refund > ₹499
→ Validate
→ Submit request to Support Team
→ Inform user
→ End
```

Example:

```text
User:
I want a refund of ₹999.

Agent:
Your refund request has been submitted to our Support Team.
They will review the request and process it or take the necessary action.
```

The application must **not** simulate the Support Team's review or response.


---

### 6.8 Missing Amount

| ID    | Requirement                                                                       |
| ----- | --------------------------------------------------------------------------------- |
| FR-41 | If the user does not specify an amount, retrieve the relevant recharge amount     |
| FR-42 | If there is a single eligible recent recharge, offer that amount for confirmation |
| FR-42a | If more than one recharge is eligible, ask the user which amount to refund       |
| FR-43 | If the amount cannot be determined, ask the user for the amount                   |
| FR-44 | The agent must never invent a refund amount                                       |

Example:

```text
User:
I want a refund.

Agent:
I can see more than one recent recharge - ₹999 and ₹499.
Which amount would you like refunded?
```
---

### 6.9 Conversation Context

| ID    | Requirement |
| ----- | ----------- |
| FR-45 | Maintain conversation history within the current session |
| FR-46 | Pass previous user and assistant messages as context when processing a new message |
| FR-47 | Conversation context must be available to both the existing RAG pipeline and Refund Agent |
| FR-48 | Clear conversation must reset the conversation history |
| FR-49 | Conversation context must not change the existing retrieval query |
| FR-50 | Limit the conversation context to a fixed number of recent exchanges |

---

## 7. Refund Workflow

```text
User Request
     │
     ▼
Intent Detection
     │
     ├── requirement_inquiry ──→ Existing RAG Pipeline
     │
     └── refund_request
              │
              ▼
        Refund Agent
              │
              ▼
       Get User Account
              │
              ▼
       Determine Amount
              │
              ▼
        Validate Refund
              │
         ┌────┴────┐
         │         │
      Invalid    Eligible
         │         │
         ▼         ▼
      Reject   Approval Limit
                   │
         ┌─────────┴─────────┐
         │                   │
      ≤ ₹499              > ₹499
         │                   │
         ▼                   ▼
    Confirmation      Submit to Support Team
         │                   │
    ┌────┴────┐              │
    │         │              │
   No        Yes             │
    │         │              │
    ▼         ▼              │
 Cancel  Process Refund      │
              │              │
              └──────┬───────┘
                     ▼
               Final Response
```


---

## 8. Demonstration Scenarios

### Scenario 1 — Successful Refund

```text
Recharge amount: ₹499
Recharge age: 1 day
Recharge status: completed
Refund status: not_refunded
```

User:

```text
I want a refund of ₹499.
```

Expected:

```text
refund_request
→ Refund Agent
→ Get account
→ Validate ₹499
→ Eligible
→ At or below ₹499
→ Ask confirmation
→ User confirms
→ Process refund
→ Success response
```

### Scenario 2 — Amount Exceeds Recharge

```text
User:
Give me a refund of ₹2,000.
```

Expected:

```text
Validation → not eligible
Reason → requested amount exceeds recharge amount
process_refund → not called
```

### Scenario 3 — Recharge Too Old

```text
recharge_age_days = 15
```

Expected:

```text
Validation → not eligible
Reason → outside 7-day refund window
process_refund → not called
```

### Scenario 4 — Already Refunded

```text
refund_status = "refunded"
```

Expected:

```text
Validation → not eligible
Reason → recharge already refunded
process_refund → not called
```

### Scenario 5 — Existing RAG Query

```text
User:
Why is my mobile internet slow?
```

Expected:

```text
requirement_inquiry
→ Existing RAG pipeline
→ Existing grounded response
```

### Scenario 6 — Refund Above the Approval Limit

```text
Recharge amount: ₹999
Recharge age: 2 days
Recharge status: completed
Refund status: not_refunded
```

User:

```text
I want a refund of ₹999.
```

Expected:

```text
refund_request
→ Refund Agent
→ Get account
→ Validate ₹999
→ Eligible
→ Above ₹499
→ Submit to Support Team
→ Submission response
process_refund → not called
refund_status → unchanged
```

### Scenario 7 — Follow-up Question

```text
User:
How do I activate international roaming?

Agent:
[grounded answer]

User:
Should I do that before I travel?
```

Expected:

```text
requirement_inquiry
→ Previous messages passed as context
→ Answer resolves "that" as activating roaming
```

---

## 9. Guardrails

| ID    | Guardrail                                                                         |
| ----- | --------------------------------------------------------------------------------- |
| GR-01 | Refund cannot execute without validation                                          |
| GR-02 | Refund cannot execute without explicit confirmation                               |
| GR-03 | User-provided account/recharge information cannot override retrieved account data |
| GR-04 | Refund amount cannot exceed actual recharge amount                                |
| GR-05 | Refund eligibility is determined by deterministic code                            |
| GR-06 | Previously refunded recharge cannot be refunded again                             |
| GR-07 | Refund execution is simulated only                                                |
| GR-08 | Refunds above ₹499 cannot be executed by the application                          |
| GR-09 | The application must not simulate or report the Support Team's review outcome     |
| GR-10 | Conversation history cannot override retrieved account data                       |

---

## 10. State Requirements

The refund workflow should maintain enough state to track:

```text
refund_requested
refund_validated
awaiting_confirmation
awaiting_amount
refund_confirmed
refund_processed
refund_rejected
refund_cancelled
refund_submitted_for_review
```

The implementation may use LangGraph state if appropriate.

The state must prevent the agent from executing a refund before validation and confirmation.

---

## 11. UI Requirements

The existing Streamlit chat interface should be reused.

No separate refund dashboard is required.

For an eligible refund of ₹499 or less, show a clear confirmation step:

```text
Refund eligible: ₹499

Do you want to proceed with this refund?

[Confirm Refund]    [Cancel]
```

If buttons are difficult to integrate with the existing chat flow, explicit natural-language confirmation may be used.

For a refund above ₹499, show no confirmation step. There is nothing for the user to
approve, so the agent reports the submission and the turn ends.

Clear conversation must reset the conversation history and any pending refund.

---

## 12. Logging / Observability

Log the major workflow steps:

```text
[Intent] refund_request
[Agent] get_user_account
[Agent] validate_refund(amount=499)
[Validation] eligible=True
[Agent] awaiting_user_confirmation
[User] confirmed
[Agent] process_refund(amount=499)
[Refund] success
```

Do not expose private LLM chain-of-thought.

---

## 13. Technology Requirements

Use the existing application stack.

| Component | Requirement                          |
| --------- | ------------------------------------ |
| Language  | Python 3.11+                         |
| Framework | Existing LangChain / LangGraph setup |
| LLM       | Existing Qwen3.6-27B via Groq        |
| UI        | Existing Streamlit application       |
| Data      | Hard-coded Python data structure     |
| Refund    | Simulated local operation            |

Do not introduce unnecessary dependencies.

Do not introduce a multi-agent architecture.

---

## 14. Acceptance Criteria

* [ ] Two intents are supported: `requirement_inquiry` and `refund_request`
* [ ] Requirement inquiries continue through the existing RAG pipeline
* [ ] Refund requests are routed to the Refund Agent
* [ ] User ID is hard-coded for the demonstration
* [ ] Agent retrieves simulated account/recharge data using a tool
* [ ] Agent validates refund using deterministic business rules
* [ ] Refund amount cannot exceed the recharge amount
* [ ] Refunds older than 7 days are rejected
* [ ] Already-refunded recharges are rejected
* [ ] Invalid refunds never call `process_refund`
* [ ] Eligible refunds of ₹499 or less require explicit user confirmation
* [ ] Refund is processed only after confirmation
* [ ] Simulated refund state is updated after execution
* [ ] Successful refund returns a simulated refund reference
* [ ] Refunds above ₹499 are submitted to the Support Team
* [ ] Refunds above ₹499 never call `process_refund`
* [ ] The agent never claims a Support Team approval, rejection, or outcome
* [ ] Refunding one recharge leaves the other recharge refundable
* [ ] Missing refund amount is handled correctly
* [ ] Conversation history is maintained within the session
* [ ] Previous messages are passed as context to both routes
* [ ] Clear conversation resets the conversation history
* [ ] Existing RAG functionality continues to work
* [ ] No real financial or billing transaction is performed
* [ ] All seven demonstration scenarios work

---

## 15. Implementation Instructions

**Extend the existing application. Do not rebuild it from scratch.**

Before making changes:

1. Inspect the existing project structure.
2. Understand the existing RAG and Streamlit implementation.
3. Reuse the existing LLM configuration.
4. Add intent detection before the existing RAG flow.
5. Keep `requirement_inquiry` behavior unchanged.
6. Add the Refund Agent as a separate flow.
7. Add the simulated user/account data.
8. Add the three refund tools.
9. Implement deterministic refund validation.
10. Add the confirmation step before refund execution.
11. Keep the implementation simple and suitable

The final application should demonstrate:

```text
Existing RAG
    ↓
Intent Detection
    ↓
 ┌──────────────────────┐
 │ Requirement Inquiry  │ → Existing RAG
 │ Refund Request       │ → Refund Agent
 └──────────────────────┘
                              ↓
                         Tool Calling
                              ↓
                         Validation
                              ↓
                     Human Confirmation
                              ↓
                       Simulated Action
```


## Final system Architecture

The updated architecture should be:

                         User
                           │
                           ▼
                    Intent Detection
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
       Requirement Inquiry       Refund Request
                │                     │
                ▼                     ▼
          Existing RAG           Refund Agent
           Pipeline                  │
                                     │
                          ┌──────────┼───────────┐
                          │          │           │
                          ▼          ▼           ▼
                     Get Account  Validate   Approval Limit
                          │          │           │
                          └──────┬───┘           │
                                 │               │
                                 ▼               │
                           Agent Decision        │
                                 │               │
                     ┌───────────┴───────────┐   │
                     │                       │   │
                     ▼                       ▼   │
             Human Confirmation      Submit to Support Team
                (≤ ₹499)                  (> ₹499)
                     │                       │
                     ▼                       │
              Process Refund ────────────────┤
                                             ▼
                                      Final Response