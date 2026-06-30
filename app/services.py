"""
app/services.py — FinSight Service Layer
=========================================
Contains the three service classes that mediate between the FastAPI
route handlers and the underlying LangChain agent, evaluation framework,
and profile persistence layer.

Design principles
-----------------
*  The service layer is the ONLY place that imports from the agent,
   tools, or metrics modules.  Route handlers import services only.
   This keeps routes thin and makes each service independently testable.

*  Every public method returns plain Python types (dicts, lists, strings,
   floats).  No LangChain objects, no Pydantic models, no dataclasses
   cross the service boundary.  This eliminates the entire class of
   JSON-serialisation errors that cause HTTP 500s.

*  All external calls (LLM, file I/O, news API) are wrapped in
   try/except.  A service method never raises to the route handler —
   it returns a structured error dict that the handler converts into a
   proper HTTP response.

*  Services are stateless classes — all state lives in the profile JSON
   file or in the LangChain agent's conversation history passed in by
   the caller.  This means services are safe to instantiate per-request.

Integration points
------------------
AgentService   ← imports from agent.py (your create_agent setup)
EvaluationService ← imports from metrics.py
ProfileService ← imports from tools.py (get_user_profile, update_user_profile)

IMPORTANT: the import paths below assume your project root structure is:
    project/
        agent.py          ← contains `agent` object and FINANCIAL_TOOLS
        tools.py          ← contains get_user_profile, update_user_profile
        metrics.py        ← contains EvaluationOrchestrator, EvalContext, EvalCase
        app/
            services.py   ← this file
            schemas.py
            api.py

Adjust the import paths to match your actual file layout.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Type aliases  (plain dicts — no Pydantic or LangChain objects cross boundary)
# ─────────────────────────────────────────────────────────────────────────────

AgentRunResult = dict[str, Any]
"""
Keys:
    success     : bool
    answer      : str
    tool_calls  : list[dict]  — each has tool_name, arguments, output, success, latency_ms
    reasoning   : list[str]   — human-readable ReAct steps for the UI trace panel
    latency_ms  : float
    error       : str | None
"""

EvalRunResult = dict[str, Any]
"""
Keys:
    success        : bool
    weighted_total : float
    passed         : bool
    metrics        : dict[str, dict]  — metric_name → {score, label, passed, reasoning, evidence}
    error          : str | None
"""

ProfileRunResult = dict[str, Any]
"""
Keys:
    success        : bool
    profile        : dict
    updated_fields : list[str]
    completeness   : dict
    error          : str | None
"""


# ─────────────────────────────────────────────────────────────────────────────
# AgentService
# ─────────────────────────────────────────────────────────────────────────────

class AgentService:
    """
    Runs the LangChain ReAct agent and converts its streaming output into
    plain Python types suitable for JSON serialisation.

    The agent is imported lazily (inside the method) to avoid import-time
    errors if the GOOGLE_API_KEY environment variable is not set when the
    module is first loaded.  FastAPI's lifespan hook should validate env
    vars before the first request, but lazy import provides a safety net.
    """

    def run(
        self,
        message: str,
        history: list[dict[str, str]],
        session_id: str = "default",
    ) -> AgentRunResult:
        """
        Invoke the LangChain agent for one conversational turn.

        Parameters
        ----------
        message    : The user's current input.
        history    : List of {"role": "user"|"assistant", "content": "..."} dicts.
                     Converted to HumanMessage / AIMessage for the agent.
        session_id : Passed through to the result for correlation.

        Returns
        -------
        AgentRunResult dict — always succeeds structurally; errors are
        captured in the "error" key rather than raised.
        """
        start = time.perf_counter()

        try:
            # ── Lazy import — keeps module loadable even without API key ──
            from agent_test import agent  # noqa: PLC0415  # adjust path if needed
        except ImportError as exc:
            logger.error("Could not import agent: %s", exc)
            return self._error_result(
                f"Agent module not found: {exc}. "
                "Check that agent.py is on the Python path.",
                start,
            )

        # ── Build conversation history for the agent ──────────────────────
        lc_messages: list[Any] = []
        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            # Unknown roles are silently skipped — defensive behaviour

        lc_messages.append(HumanMessage(content=message))

        agent_input = {"messages": lc_messages}

        # ── Stream the agent and collect trace data ───────────────────────
        tool_calls: list[dict[str, Any]] = []
        reasoning_steps: list[str] = []
        final_answer: str = ""

        try:
            for chunk in agent.stream(agent_input, stream_mode="updates"):
                self._process_chunk(chunk, tool_calls, reasoning_steps)

            # Final answer is the last AIMessage with no tool_calls
            # (extract from the last model-node chunk)
            final_answer = self._extract_final_answer(
                agent, agent_input, tool_calls, reasoning_steps
            )

        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent stream failed for session %s", session_id)
            return self._error_result(str(exc), start)

        latency_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "Agent run complete | session=%s tools=%d latency=%.1fms",
            session_id,
            len(tool_calls),
            latency_ms,
        )

        return {
            "success": True,
            "answer": final_answer,
            "tool_calls": tool_calls,
            "reasoning": reasoning_steps,
            "latency_ms": round(latency_ms, 2),
            "error": None,
        }

    # ── Private helpers ───────────────────────────────────────────────────

    def _process_chunk(
        self,
        chunk: dict[str, Any],
        tool_calls: list[dict[str, Any]],
        reasoning_steps: list[str],
    ) -> None:
        """
        Parse one streaming chunk from agent.stream(stream_mode='updates').

        Each chunk is {"node_name": {"messages": [...]}} where node_name
        is "model" (LLM output) or "tools" (tool execution output).
        """
        for node_name, node_output in chunk.items():
            messages = node_output.get("messages", [])

            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        # LLM decided to call tool(s) — log as reasoning step
                        for tc in msg.tool_calls:
                            step = (
                                f"[model] → calling {tc['name']} "
                                f"with args: {json.dumps(tc.get('args', {}), default=str)}"
                            )
                            reasoning_steps.append(step)
                    elif msg.content:
                        # Final answer step — log content preview
                        reasoning_steps.append(
                            f"[model] → final answer ({len(msg.content)} chars)"
                        )

                elif isinstance(msg, ToolMessage):
                    # Tool returned a result — parse and record
                    tool_call_record = self._parse_tool_message(msg)
                    tool_calls.append(tool_call_record)
                    reasoning_steps.append(
                        f"[tool:{msg.name}] → "
                        f"{'✓ success' if tool_call_record['success'] else '✗ failed'}"
                    )

    def _parse_tool_message(self, msg: ToolMessage) -> dict[str, Any]:
        """
        Convert a LangChain ToolMessage to a plain dict.

        ToolMessage.content is always a string — it may be a JSON string
        (from our tools that return dicts) or a plain error string.
        """
        tool_name = getattr(msg, "name", "unknown_tool")
        raw_content = msg.content or ""

        output: dict[str, Any] | str
        success: bool

        try:
            output = json.loads(raw_content)
            success = bool(output.get("success", True)) if isinstance(output, dict) else True
        except (json.JSONDecodeError, TypeError):
            output = raw_content
            success = "error" not in raw_content.lower()

        return {
            "tool_name": tool_name,
            "arguments": {},        # args are in the prior AIMessage; captured in reasoning
            "output": output,
            "success": success,
            "latency_ms": None,     # per-tool latency requires the tracer (Phase 2)
        }

    def _extract_final_answer(
        self,
        agent: Any,
        agent_input: dict[str, Any],
        tool_calls: list[dict[str, Any]],
        reasoning_steps: list[str],
    ) -> str:
        """
        Extract the agent's final text response.

        When streaming with stream_mode='updates', the final AIMessage
        (the one with no tool_calls) is in the last chunk from the model
        node.  We re-invoke without streaming to get the clean final state,
        but only if we didn't already capture it during streaming.

        This approach avoids a second LLM call — we use agent.invoke()
        only if stream_mode='updates' didn't yield the final answer
        (which can happen if the agent ends on a tool call with no
        subsequent model response, though this is unusual).
        """
        # Check if reasoning already has a final answer marker
        has_final = any("[model] → final answer" in s for s in reasoning_steps)
        if not has_final:
            # Fallback: invoke synchronously to get the clean final state
            try:
                result = agent.invoke(agent_input)
                messages = result.get("messages", [])
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
                        return msg.content
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fallback invoke failed: %s", exc)
                return "I encountered an issue generating a response. Please try again."

        # Re-run invoke to get the final structured state
        # (stream gives us chunks; invoke gives us the full final state)
        try:
            result = agent.invoke(agent_input)
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and not msg.tool_calls and msg.content:
                    if isinstance(msg.content, list):
                        text = ""
                        for part in msg.content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text += part.get("text", "")
                        return text

                    return str(msg.content)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Final answer extraction failed: %s", exc)

        return "I was unable to generate a response. Please try again."

    @staticmethod
    def _error_result(error_message: str, start: float) -> AgentRunResult:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "answer": "",
            "tool_calls": [],
            "reasoning": [],
            "latency_ms": round(latency_ms, 2),
            "error": error_message,
        }


# ─────────────────────────────────────────────────────────────────────────────
# EvaluationService
# ─────────────────────────────────────────────────────────────────────────────

class EvaluationService:
    """
    Bridges the FastAPI /evaluate endpoint to the existing metrics framework.

    Converts the API request payload into EvalContext + EvalCase, runs
    EvaluationOrchestrator, and converts the result back to plain dicts.
    The metrics module is never aware that it's being called from an API —
    it receives and returns the same types it always has.
    """

    def evaluate(
        self,
        query: str,
        tool_outputs: list[dict[str, Any]],
        response: str,
        expected_numeric_values: dict[str, float] | None = None,
        required_topics: list[str] | None = None,
        required_caveats: list[str] | None = None,
        forbidden_claims: list[str] | None = None,
    ) -> EvalRunResult:
        """
        Run the evaluation harness and return a plain dict result.

        Parameters match the EvaluateRequest schema fields directly so
        the route handler can unpack the request model with **kwargs.
        """
        try:
            from metrics import (   # noqa: PLC0415
                EvalCase,
                EvalContext,
                EvaluationOrchestrator,
            )
        except ImportError as exc:
            logger.error("Could not import metrics: %s", exc)
            return {
                "success": False,
                "weighted_total": 0.0,
                "passed": False,
                "metrics": {},
                "error": f"Metrics module not found: {exc}",
            }

        try:
            eval_case = EvalCase(
                expected_numeric_values=expected_numeric_values or {},
                required_topics=required_topics or [],
                required_caveats=required_caveats or [],
                forbidden_claims=forbidden_claims or [],
            )
            ctx = EvalContext(
                query=query,
                tool_outputs=tool_outputs,
                response=response,
                eval_case=eval_case,
            )
            result = EvaluationOrchestrator().evaluate(ctx)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Evaluation failed")
            return {
                "success": False,
                "weighted_total": 0.0,
                "passed": False,
                "metrics": {},
                "error": str(exc),
            }

        # ── Convert EvaluationResult to plain dict ────────────────────────
        metrics_dict: dict[str, dict[str, Any]] = {}
        for name, metric_result in result.metric_results.items():
            metrics_dict[name] = {
                "score": round(metric_result.score, 4),
                "label": metric_result.score_label,
                "passed": metric_result.passed,
                "reasoning": metric_result.reasoning,
                "evidence": metric_result.evidence,
            }

        return {
            "success": True,
            "weighted_total": round(result.weighted_total, 4),
            "passed": result.passed,
            "metrics": metrics_dict,
            "error": None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ProfileService
# ─────────────────────────────────────────────────────────────────────────────

class ProfileService:
    """
    Reads and writes the user financial profile via the existing tool functions.

    Using the tool functions (rather than reading user_profile.json directly)
    means the service respects the same validation and derived-state logic
    (e.g. _check_profile_completeness) that the agent uses.  There is one
    source of truth for what a "valid profile update" means.
    """

    def get_profile(self) -> ProfileRunResult:
        """Read the current user profile and return it with completeness metadata."""
        try:
            from tools import get_user_profile  # noqa: PLC0415
        except ImportError as exc:
            return self._error_profile(f"Tools module not found: {exc}")

        try:
            # get_user_profile is a LangChain @tool — invoke it directly
            profile_data = get_user_profile.invoke({})
            return {
                "success": True,
                "profile": self._sanitise_profile(profile_data),
                "updated_fields": [],
                "completeness": profile_data.get("completeness", {}),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("Profile read failed")
            return self._error_profile(str(exc))

    def update_profile(
        self,
        updates: list[dict[str, Any]],
    ) -> ProfileRunResult:
        """
        Apply a list of {field, value} updates to the user profile.

        Each update is applied sequentially.  If any individual update
        fails, it is logged but processing continues — the response
        reports which fields were successfully updated.
        """
        try:
            from tools import update_user_profile  # noqa: PLC0415
        except ImportError as exc:
            return self._error_profile(f"Tools module not found: {exc}")

        updated_fields: list[str] = []
        last_result: dict[str, Any] = {}
        errors: list[str] = []

        for update in updates:
            field = update.get("field", "")
            value = update.get("value")
            try:
                result = update_user_profile.invoke(
                    {"field": field, "value": value}
                )
                if result.get("success", False):
                    updated_fields.append(field)
                    last_result = result
                else:
                    errors.append(f"{field}: {result.get('error', 'update failed')}")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to update field '%s': %s", field, exc)
                errors.append(f"{field}: {exc}")

        # Re-read the profile after all updates for a consistent final state
        final_profile_result = self.get_profile()
        final_profile = final_profile_result.get("profile", {})
        completeness = final_profile_result.get("completeness", {})

        return {
            "success": len(updated_fields) > 0,
            "profile": final_profile,
            "updated_fields": updated_fields,
            "completeness": completeness,
            "error": "; ".join(errors) if errors else None,
        }

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _sanitise_profile(profile_data: Any) -> dict[str, Any]:
        """
        Ensure the profile is a plain dict with JSON-serialisable values.

        The get_user_profile tool returns a dict that may include a nested
        'completeness' dict.  We keep the completeness at the top level of
        ProfileRunResult and strip it from the profile dict here to avoid
        duplication.
        """
        if not isinstance(profile_data, dict):
            return {}
        return {
            k: v for k, v in profile_data.items()
            if k != "completeness"
        }

    @staticmethod
    def _error_profile(error_message: str) -> ProfileRunResult:
        return {
            "success": False,
            "profile": {},
            "updated_fields": [],
            "completeness": {},
            "error": error_message,
        }