# FinSight Architecture Decisions

## 1. Profile Memory vs Conversation Memory

The system uses two different memory mechanisms.

### Conversation Memory

Conversation memory stores the messages exchanged during the current chat session.

Purpose:

* Remember recent context
* Handle follow-up questions
* Maintain conversational flow

Example:

User: My favorite stock is INFY.

User: What is my favorite stock?

The agent answers using conversation history.

Conversation memory is session-scoped and disappears when the application stops.

### Profile Memory

Profile memory stores long-term financial information inside user_profile.json.

Examples:

* Age
* Monthly income
* Risk tolerance
* Financial goals

This information persists across application restarts.

Purpose:

* Personalised recommendations
* Long-term user understanding

---

## 2. Derived State vs Stored State

Initially, profile completeness was considered for storage inside the JSON profile.

Example:

{
"profile_complete": true
}

This approach creates a stale-state risk.

Example:

User updates income.

If profile_complete is not recalculated immediately, the stored value becomes incorrect.

### Final Decision

Profile completeness is derived from profile data whenever needed.

Benefits:

* Single source of truth
* No stale state
* Easier testing
* Easier maintenance
* Simpler data model

The completeness logic is implemented as a pure helper function.

Example:

_check_profile_completeness(profile)

This function computes completeness without modifying state.

---

## 3. Agent Architecture

User
 ↓
Gemini LLM
 ↓
LangChain ReAct Agent
 ↓
Tool Selection
 ↓
 ├── Financial Tools
 │      ├── Stock Data
 │      ├── SIP Calculator
 │      └── CAGR Calculator
 │
 └── Profile Tools
        ├── get_user_profile
        └── update_user_profile
                ↓
          user_profile.json

The agent follows a ReAct loop:

Reason
→ Tool Call
→ Observation
→ Final Response
## 4. Profile Completeness System

The agent needs to determine whether sufficient user information exists to provide personalised financial recommendations.

A pure helper function is used:

_check_profile_completeness(profile)

The helper returns:

* is_complete
* tier
* completeness percentage
* missing required fields
* missing optional fields

### Design Rationale

Completeness logic is separated from profile storage and profile update operations.

Benefits:

* Single responsibility
* Reusable by multiple tools
* Easy unit testing
* Easy extension when new profile fields are introduced

The helper is the single source of truth for profile completeness.
## 5. Input Validation Layer

Profile updates are validated before being written to persistent storage.

A VALID_FIELDS allow-list is maintained.

Example:

VALID_FIELDS = {
"age",
"monthly_income",
"risk_tolerance",
...
}

Any unknown field is rejected.

### Design Rationale

LLM-generated tool calls are probabilistic and may contain:

* Typos
* Schema drift
* Hallucinated fields

Validation prevents malformed updates from corrupting persistent user data.
## 6. Resilience and Error Handling

Profile tools gracefully handle common persistence failures.

Handled exceptions:

* FileNotFoundError
* JSONDecodeError

Instead of crashing, tools return structured error information that allows the agent to continue interacting with the user.

### Design Rationale

Graceful degradation is preferred over application crashes.

This improves robustness and user experience when profile data becomes unavailable or corrupted.
## 7. Key Engineering Decisions

1. JSON was chosen over a database for MVP simplicity.

2. Profile completeness is derived rather than stored to avoid stale-state bugs.

3. Conversation memory and profile memory are separated because they solve different problems.

4. Profile updates are validated before persistence.

5. Tool failures are handled gracefully through structured error responses.

These decisions prioritise simplicity, maintainability, and testability while keeping the architecture extensible for future enhancements such as databases, RAG systems, and multi-agent workflows.
