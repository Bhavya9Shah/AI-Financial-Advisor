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
LangChain Agent
↓
Tool Selection
↓
Financial Tools
↓
Profile Storage / External APIs

The agent follows a ReAct loop:

Reason
→ Tool Call
→ Observation
→ Final Response
