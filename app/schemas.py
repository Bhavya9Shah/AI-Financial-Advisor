"""
app/schemas.py — FinSight API Request and Response Models
==========================================================
All Pydantic models used for request validation and response serialisation
across the FinSight FastAPI backend.

Design principles
-----------------
*  Every endpoint has its own Request model and its own Response model.
   They never share models — decoupling prevents one endpoint's schema
   change from silently breaking another.

*  All responses inherit from BaseResponse, giving the frontend a
   predictable envelope: {success, data, error, timestamp}.

*  Field-level validation lives here, not in route handlers or services.
   If the request is malformed, Pydantic raises a 422 before the handler
   is ever called — no try/except boilerplate in routes.

*  Optional fields use None as the default, never mutable defaults,
   following Pydantic v2 best practices.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Shared envelope
# ─────────────────────────────────────────────────────────────────────────────

class BaseResponse(BaseModel):
    """
    Consistent JSON envelope for every FinSight API response.

    Having a single envelope means the frontend never needs to guess
    whether the error is in the top-level dict or inside a nested key.

    Attributes
    ----------
    success   : False on any handled error; True otherwise.
    error     : Human-readable message when success is False, else None.
    timestamp : UTC ISO-8601 string — useful for latency debugging.
    """
    success: bool = True
    error: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /
# ─────────────────────────────────────────────────────────────────────────────

class RootResponse(BaseResponse):
    """Response for the root endpoint — confirms the API is reachable."""
    name: str = "FinSight API"
    version: str = "1.0.0"
    description: str = "AI-powered financial advisor backend"
    docs_url: str = "/docs"


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseResponse):
    """
    Structured health check response.

    Each dependency is reported independently so a monitoring tool can
    tell whether a degraded state is caused by the LLM, the profile
    store, or the metrics engine — not just 'something is broken'.
    """
    status: str = "ok"                          # "ok" | "degraded" | "down"
    dependencies: dict[str, str] = Field(       # dependency → status string
        default_factory=dict
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /chat
# ─────────────────────────────────────────────────────────────────────────────

class MessageRecord(BaseModel):
    """
    A single turn in a conversation, matching LangChain's message format.

    role    : "user" | "assistant"
    content : raw text of the message
    """
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=8_000)


class ChatRequest(BaseModel):
    """
    Request body for POST /chat.

    Attributes
    ----------
    message  : The current user message (required, non-empty).
    history  : Previous turns in this session.  The service layer
               converts these into LangChain HumanMessage / AIMessage
               objects before invoking the agent.  Keeping raw dicts
               here avoids a LangChain import in the schema layer.
    session_id : Opaque identifier the client uses to correlate turns.
                 The API does not enforce session state — that lives in
                 the client.  Included in the response for correlation.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=4_000,
        description="The user's current message to the financial advisor.",
    )
    history: list[MessageRecord] = Field(
        default_factory=list,
        max_length=50,           # hard cap — prevents context-window abuse
        description="Prior conversation turns, oldest first.",
    )
    session_id: str = Field(
        default="default",
        max_length=64,
        description="Client-provided session identifier.",
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank or whitespace only")
        return v.strip()


class ToolCallRecord(BaseModel):
    """
    A single tool call captured from the agent's ReAct trace.

    Included in ChatResponse so the UI can display the reasoning trace
    (what tools the agent used and what they returned).
    """
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | str = Field(default_factory=dict)
    success: bool = True
    latency_ms: float | None = None


class ChatResponse(BaseResponse):
    """
    Response body for POST /chat.

    Attributes
    ----------
    answer      : The agent's final text response to the user.
    tool_calls  : Ordered list of tool calls made during this turn.
                  Empty if the agent answered without tool use.
    session_id  : Echo of the request's session_id for correlation.
    latency_ms  : Wall-clock time for the full agent invocation.
    reasoning   : Raw ReAct trace for display in the UI's expandable
                  reasoning panel.  May be empty if tracing is disabled.
    """
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    session_id: str = "default"
    latency_ms: float = 0.0
    reasoning: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# POST /evaluate
# ─────────────────────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    """
    Request body for POST /evaluate.

    Decoupled from ChatRequest so evaluation can be called on any
    (query, tool_outputs, response) triple — not only on live agent
    outputs.  This lets you run offline evaluation on saved transcripts.

    Attributes
    ----------
    query        : The original user query that produced the response.
    tool_outputs : The list of tool output dicts from the agent run.
    response     : The agent's final text response to evaluate.
    expected_numeric_values : Optional ground truth for CorrectnessMetric.
    required_topics         : Optional topic list for CompletenessMetric.
    required_caveats        : Optional caveat list for HelpfulnessMetric.
    forbidden_claims        : Optional forbidden phrases for HelpfulnessMetric.
    """
    query: str = Field(..., min_length=1, max_length=4_000)
    tool_outputs: list[dict[str, Any]] = Field(default_factory=list)
    response: str = Field(..., min_length=1, max_length=8_000)
    expected_numeric_values: dict[str, float] = Field(default_factory=dict)
    required_topics: list[str] = Field(default_factory=list)
    required_caveats: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)


class MetricDetail(BaseModel):
    """Per-metric result included in EvaluateResponse."""
    score: float
    label: str           # EXCELLENT | GOOD | PASS | PARTIAL | FAIL
    passed: bool
    reasoning: str
    evidence: list[str] = Field(default_factory=list)


class EvaluateResponse(BaseResponse):
    """
    Response body for POST /evaluate.

    weighted_total is the single number suitable for regression
    detection — compare it against your baseline JSON to know
    whether a code change made the agent better or worse.
    """
    weighted_total: float
    passed: bool
    metrics: dict[str, MetricDetail] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# POST /profile
# ─────────────────────────────────────────────────────────────────────────────

class ProfileField(BaseModel):
    """
    A single field update for the user profile.

    Using a (field, value) pair rather than a full profile dict means
    the endpoint is idempotent per field and never accidentally clears
    fields that weren't included in the request body.
    """
    field: str = Field(
        ...,
        description=(
            "Profile field to update.  Valid values: name, age, "
            "monthly_income, monthly_expenses, risk_tolerance, "
            "investment_horizon_years, financial_goals, "
            "emergency_fund_months, has_loans."
        ),
    )
    value: Any = Field(..., description="New value for the field.")

    @field_validator("field")
    @classmethod
    def field_is_known(cls, v: str) -> str:
        allowed = {
            "name", "age", "monthly_income", "monthly_expenses",
            "risk_tolerance", "investment_horizon_years",
            "financial_goals", "emergency_fund_months", "has_loans",
            "favorite_stock", "favorite_sector", "financial_goal",
        }
        if v not in allowed:
            raise ValueError(
                f"Unknown profile field '{v}'. "
                f"Allowed fields: {sorted(allowed)}"
            )
        return v


class ProfileRequest(BaseModel):
    """Request body for POST /profile — one or more field updates."""
    updates: list[ProfileField] = Field(
        ...,
        min_length=1,
        description="List of field/value pairs to update.",
    )


class ProfileResponse(BaseResponse):
    """
    Response body for POST /profile.

    Returns the full updated profile so the UI can refresh its display
    without a separate GET call.
    """
    profile: dict[str, Any] = Field(default_factory=dict)
    updated_fields: list[str] = Field(default_factory=list)
    completeness: dict[str, Any] = Field(default_factory=dict)