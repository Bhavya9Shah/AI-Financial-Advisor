"""
app/api.py — FinSight FastAPI Application
==========================================
Defines the FastAPI app, lifespan handler, middleware, exception handlers,
and all five API route handlers.

Architecture
------------
Route handlers are intentionally thin — they:
    1. Accept a validated Pydantic request model
    2. Call exactly one service method
    3. Convert the service result to a Pydantic response model
    4. Return it

No business logic lives in route handlers.  No LangChain imports live
here.  If you read a handler and it's more than ~15 lines, something
that belongs in services.py has leaked into the route layer.

Running the server
------------------
From the project root:
    uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

The --reload flag watches for file changes during development.
Remove it in production.

Environment variables required
-------------------------------
    GOOGLE_API_KEY    : Gemini API key
    PROFILE_PATH      : (optional) Path to user_profile.json.
                        Defaults to user_profile.json in project root.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import (
    ChatRequest,
    ChatResponse,
    EvaluateRequest,
    EvaluateResponse,
    HealthResponse,
    MessageRecord,
    MetricDetail,
    ProfileRequest,
    ProfileResponse,
    RootResponse,
    ToolCallRecord,
)
from app.services import AgentService, EvaluationService, ProfileService

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Service singletons
# ─────────────────────────────────────────────────────────────────────────────
# Instantiated once at module load — each class is stateless so this is safe.

agent_service = AgentService()
evaluation_service = EvaluationService()
profile_service = ProfileService()


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — startup validation
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run startup checks before the server accepts any requests.

    Catching configuration errors here (before the first request) means
    the problem is obvious in server logs rather than buried inside a
    mid-request traceback.
    """
    logger.info("FinSight API starting up…")

    # Check required environment variables
    missing: list[str] = []
    if not os.getenv("GOOGLE_API_KEY"):
        missing.append("GOOGLE_API_KEY")

    if missing:
        logger.warning(
            "Missing environment variables: %s. "
            "The /chat endpoint will fail until these are set.",
            ", ".join(missing),
        )
    else:
        logger.info("Environment variables: OK")

    logger.info("FinSight API ready — docs at http://localhost:8000/docs")
    yield
    logger.info("FinSight API shutting down.")


# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FinSight API",
    description=(
        "AI-powered financial advisor backend. "
        "Built on LangChain ReAct + Gemini 2.5 Flash."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow the Streamlit app (runs on port 8501 by default) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",     # Streamlit dev server
        "http://127.0.0.1:8501",
        "http://localhost:3000",     # if you ever add a React frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.

    Returns a structured JSON 500 instead of FastAPI's default plain-text
    traceback.  The response shape matches BaseResponse so the frontend
    handles it identically to a well-formed error response.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": f"Internal server error: {type(exc).__name__}",
            "timestamp": "",   # avoids a second import of datetime here
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return HTTP errors in the same BaseResponse envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": "",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper — convert service result to HTTP response or raise
# ─────────────────────────────────────────────────────────────────────────────

def _require_success(result: dict[str, Any], status_code: int = 502) -> None:
    """
    Raise HTTPException if a service result indicates failure.

    Centralises the success-check pattern so route handlers don't each
    need their own if/raise block.  502 Bad Gateway is used for agent/
    tool failures (an upstream dependency failed) rather than 500 (which
    implies a bug in our own code).
    """
    if not result.get("success", False):
        error_msg = result.get("error", "An unknown error occurred.")
        logger.warning("Service call failed: %s", error_msg)
        raise HTTPException(status_code=status_code, detail=error_msg)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_model=RootResponse, tags=["Meta"])
async def root() -> RootResponse:
    """
    Confirm the API is reachable and return basic metadata.

    Use this for a simple connectivity check before calling /health.
    """
    return RootResponse()


@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health() -> HealthResponse:
    """
    Structured health check.

    Reports the status of each dependency independently so a monitoring
    system can distinguish between 'LLM unreachable' and 'profile file
    missing'.  Status is 'degraded' if any dependency is unhealthy but
    the API is still partially functional.
    """
    dependencies: dict[str, str] = {}
    overall_status = "ok"

    # Check: Google API key present (doesn't make a network call)
    if os.getenv("GOOGLE_API_KEY"):
        dependencies["google_api_key"] = "ok"
    else:
        dependencies["google_api_key"] = "missing — /chat will fail"
        overall_status = "degraded"

    # Check: agent module importable
    try:
        import agent_test  # noqa: F401, PLC0415
        dependencies["agent_module"] = "ok"
    except ImportError as exc:
        dependencies["agent_module"] = f"import error: {exc}"
        overall_status = "degraded"

    # Check: metrics module importable
    try:
        import metrics  # noqa: F401, PLC0415
        dependencies["metrics_module"] = "ok"
    except ImportError as exc:
        dependencies["metrics_module"] = f"import error: {exc}"
        overall_status = "degraded"

    # Check: profile file readable
    profile_path = os.getenv("PROFILE_PATH", "user_profile.json")
    if os.path.exists(profile_path):
        dependencies["profile_file"] = "ok"
    else:
        dependencies["profile_file"] = f"not found at {profile_path}"
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        dependencies=dependencies,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the FinSight financial advisor agent.

    The agent uses a ReAct loop to decide which financial tools to call,
    executes them, and synthesises a final response.  The response
    includes the agent's reasoning trace and all tool calls made during
    this turn — suitable for display in the UI's 'reasoning' panel.

    Pass prior conversation turns in `history` to maintain context.
    The session_id is echoed back for client-side correlation.
    """
    logger.info(
        "POST /chat | session=%s | message_len=%d | history_turns=%d",
        request.session_id,
        len(request.message),
        len(request.history),
    )

    history_dicts = [
        {"role": turn.role, "content": turn.content}
        for turn in request.history
    ]

    result = agent_service.run(
        message=request.message,
        history=history_dicts,
        session_id=request.session_id,
    )

    _require_success(result)

    tool_call_records = [
        ToolCallRecord(
            tool_name=tc["tool_name"],
            arguments=tc.get("arguments", {}),
            output=tc.get("output", {}),
            success=tc.get("success", True),
            latency_ms=tc.get("latency_ms"),
        )
        for tc in result["tool_calls"]
    ]

    return ChatResponse(
        answer=result["answer"],
        tool_calls=tool_call_records,
        session_id=request.session_id,
        latency_ms=result["latency_ms"],
        reasoning=result["reasoning"],
    )


@app.post("/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """
    Run the FinSight evaluation harness on a (query, tool_outputs, response) triple.

    This endpoint is decoupled from /chat — you can call it with outputs
    from a live agent run or with saved transcripts for offline analysis.

    All five metrics are run: Correctness, Grounding, Completeness,
    Helpfulness, and Clarity.  Returns per-metric scores plus a weighted
    total suitable for regression detection against your baseline JSON.
    """
    logger.info(
        "POST /evaluate | query_len=%d | tool_count=%d",
        len(request.query),
        len(request.tool_outputs),
    )

    result = evaluation_service.evaluate(
        query=request.query,
        tool_outputs=request.tool_outputs,
        response=request.response,
        expected_numeric_values=request.expected_numeric_values,
        required_topics=request.required_topics,
        required_caveats=request.required_caveats,
        forbidden_claims=request.forbidden_claims,
    )

    _require_success(result)

    metric_details = {
        name: MetricDetail(
            score=m["score"],
            label=m["label"],
            passed=m["passed"],
            reasoning=m["reasoning"],
            evidence=m.get("evidence", []),
        )
        for name, m in result["metrics"].items()
    }

    return EvaluateResponse(
        weighted_total=result["weighted_total"],
        passed=result["passed"],
        metrics=metric_details,
    )


@app.post("/profile", response_model=ProfileResponse, tags=["Profile"])
async def update_profile(request: ProfileRequest) -> ProfileResponse:
    """
    Update one or more fields in the user's persistent financial profile.

    Uses the same update_user_profile tool the agent uses internally,
    ensuring consistent validation and completeness-tier computation.

    Returns the full updated profile and the completeness metadata so
    the UI can refresh its profile panel in a single round-trip.

    Example request body:
        {
            "updates": [
                {"field": "age", "value": 27},
                {"field": "monthly_income", "value": 90000},
                {"field": "risk_tolerance", "value": "moderate"}
            ]
        }
    """
    logger.info(
        "POST /profile | updating fields: %s",
        [u.field for u in request.updates],
    )

    updates_dicts = [
        {"field": u.field, "value": u.value}
        for u in request.updates
    ]

    result = profile_service.update_profile(updates_dicts)

    # Profile update is best-effort — partial success is still a 200
    # (some fields updated, some failed).  Only a total failure is an error.
    if not result["success"] and not result["updated_fields"]:
        _require_success(result, status_code=422)

    return ProfileResponse(
        success=result["success"],
        profile=result["profile"],
        updated_fields=result["updated_fields"],
        completeness=result["completeness"],
        error=result.get("error"),
    )