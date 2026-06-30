"""
app/streamlit_app.py — FinSight AI Financial Advisor UI
=========================================================
A production-quality Streamlit interface for the FinSight agent.
Calls the FastAPI backend — does NOT import LangChain directly.

Running
-------
    # Terminal 1: start the API
    uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

    # Terminal 2: start the UI
    streamlit run app/streamlit_app.py

Environment
-----------
    API_BASE_URL : defaults to http://localhost:8000
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 120       # seconds — LLM calls can be slow
PAGE_TITLE = "FinSight"
PAGE_ICON = "💼"

# ─────────────────────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — makes it look like a startup product, not a tutorial
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #21262d; }

/* ── Chat bubbles ── */
.user-bubble {
    background: #1f6feb;
    color: #ffffff;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0 0.5rem 20%;
    font-size: 0.9rem;
    line-height: 1.5;
}
.assistant-bubble {
    background: #161b22;
    color: #e6edf3;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 20% 0.5rem 0;
    border: 1px solid #21262d;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ── Metric pill ── */
.metric-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}
.pill-excellent { background: #1a7f37; color: #ffffff; }
.pill-good      { background: #0969da; color: #ffffff; }
.pill-pass      { background: #9a6700; color: #ffffff; }
.pill-partial   { background: #cf6600; color: #ffffff; }
.pill-fail      { background: #b91c1c; color: #ffffff; }

/* ── Tool call chip ── */
.tool-chip {
    display: inline-block;
    background: #21262d;
    color: #58a6ff;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-family: monospace;
    margin: 2px;
}

/* ── Header ── */
.finsight-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1rem 0 0.5rem;
    border-bottom: 1px solid #21262d;
    margin-bottom: 1rem;
}
.finsight-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #e6edf3;
    letter-spacing: -0.02em;
}
.finsight-badge {
    background: #1f6feb22;
    border: 1px solid #1f6feb66;
    color: #58a6ff;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── Latency badge ── */
.latency-badge {
    font-size: 0.7rem;
    color: #7d8590;
    font-family: monospace;
}

/* ── Profile field ── */
.profile-field {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    border-bottom: 1px solid #21262d;
    font-size: 0.82rem;
}
.profile-key   { color: #7d8590; }
.profile-value { color: #e6edf3; font-weight: 500; }

/* ── Completeness bar ── */
.completeness-bar-bg {
    background: #21262d;
    border-radius: 4px;
    height: 6px;
    margin: 4px 0 8px;
}
.completeness-bar-fill {
    background: #1f6feb;
    border-radius: 4px;
    height: 6px;
}

/* ── Section headers in sidebar ── */
.sidebar-section {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #7d8590;
    text-transform: uppercase;
    margin: 1.2rem 0 0.4rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_session() -> None:
    """Initialise all session state keys with defaults on first load."""
    defaults: dict[str, Any] = {
        "messages": [],          # list[dict] with keys: role, content, meta
        "session_id": f"session-{int(time.time())}",
        "profile": {},
        "last_eval": None,
        "api_reachable": None,   # None = unchecked, True/False = result
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session()


# ─────────────────────────────────────────────────────────────────────────────
# API client helpers
# ─────────────────────────────────────────────────────────────────────────────

def _api_get(path: str) -> dict[str, Any] | None:
    """GET request to the API. Returns response dict or None on error."""
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception as exc:
        st.error(f"API error: {exc}")
        return None


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST request to the API. Returns response dict or None on error."""
    try:
        resp = requests.post(
            f"{API_BASE}{path}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "⚠️ Cannot reach the FinSight API. "
            f"Make sure the server is running on {API_BASE}."
        )
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The agent may be processing a complex query.")
        return None
    except requests.exceptions.HTTPError as exc:
        error_detail = "Unknown error"
        try:
            error_detail = exc.response.json().get("error", str(exc))
        except Exception:
            error_detail = str(exc)
        st.error(f"API error {exc.response.status_code}: {error_detail}")
        return None
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
        return None


def _check_api_health() -> bool:
    """Check if the API is reachable. Cached per session."""
    if st.session_state.api_reachable is None:
        result = _api_get("/health")
        st.session_state.api_reachable = result is not None
    return st.session_state.api_reachable


def _load_profile() -> dict[str, Any]:
    """Fetch the current user profile from the API."""
    result = _api_get("/health")   # profile is loaded via agent tools — use a chat ping
    # Return cached profile; it's updated after /chat and /profile calls
    return st.session_state.profile


# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

def _render_metric_pill(label: str, score: float) -> str:
    css_class = {
        "EXCELLENT": "pill-excellent",
        "GOOD": "pill-good",
        "PASS": "pill-pass",
        "PARTIAL": "pill-partial",
        "FAIL": "pill-fail",
    }.get(label, "pill-pass")
    return f'<span class="metric-pill {css_class}">{label} {score:.2f}</span>'


def _render_tool_chip(tool_name: str) -> str:
    return f'<span class="tool-chip">🔧 {tool_name}</span>'


def _render_chat_message(msg: dict[str, Any]) -> None:
    """Render one chat message with its metadata."""
    role = msg["role"]
    content = msg["content"]
    meta = msg.get("meta", {})

    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
        return

    # Assistant message
    st.markdown(f'<div class="assistant-bubble">{content}</div>', unsafe_allow_html=True)

    # Metadata row — tool chips, latency
    if meta:
        cols = st.columns([3, 1])
        with cols[0]:
            tool_calls = meta.get("tool_calls", [])
            if tool_calls:
                chips = " ".join(_render_tool_chip(tc["tool_name"]) for tc in tool_calls)
                st.markdown(chips, unsafe_allow_html=True)

        with cols[1]:
            latency = meta.get("latency_ms", 0)
            st.markdown(
                f'<div class="latency-badge">⏱ {latency:.0f}ms</div>',
                unsafe_allow_html=True,
            )

        # Expandable reasoning trace
        reasoning = meta.get("reasoning", [])
        if reasoning:
            with st.expander("🔍 View reasoning trace", expanded=False):
                for step in reasoning:
                    st.markdown(f"```\n{step}\n```")

        # Expandable eval metrics if present
        eval_data = meta.get("eval", {})
        if eval_data and eval_data.get("metrics"):
            with st.expander("📊 Evaluation metrics", expanded=False):
                metrics = eval_data["metrics"]
                pills = " ".join(
                    _render_metric_pill(m["label"], m["score"])
                    for m in metrics.values()
                )
                wt = eval_data.get("weighted_total", 0)
                st.markdown(
                    f"**Weighted total: {wt:.3f}** &nbsp; {pills}",
                    unsafe_allow_html=True,
                )
                for name, m in metrics.items():
                    st.caption(f"**{name}**: {m['reasoning']}")


def _render_profile_panel(profile: dict[str, Any]) -> None:
    """Render the user profile in the sidebar."""
    if not profile:
        st.caption("No profile data yet. Start chatting to build your profile.")
        return

    display_fields = {
        "name": "Name",
        "age": "Age",
        "monthly_income": "Monthly Income",
        "monthly_expenses": "Monthly Expenses",
        "risk_tolerance": "Risk Tolerance",
        "investment_horizon_years": "Investment Horizon",
        "emergency_fund_months": "Emergency Fund",
        "financial_goals": "Financial Goals",
        "has_loans": "Has Loans",
    }

    for field, label in display_fields.items():
        value = profile.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            display_value = ", ".join(str(v) for v in value) if value else "—"
        elif field == "monthly_income" or field == "monthly_expenses":
            display_value = f"₹{value:,}"
        else:
            display_value = str(value)

        st.markdown(
            f'<div class="profile-field">'
            f'<span class="profile-key">{label}</span>'
            f'<span class="profile-value">{display_value}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Completeness bar
    completeness = profile.get("completeness", {})
    pct = completeness.get("completeness_pct", 0)
    tier = completeness.get("tier", "basic")

    st.markdown(
        f'<div style="margin-top:10px">'
        f'<div style="font-size:0.75rem;color:#7d8590;margin-bottom:3px">'
        f'Profile completeness — {tier.upper()} ({pct}%)'
        f'</div>'
        f'<div class="completeness-bar-bg">'
        f'<div class="completeness-bar-fill" style="width:{pct}%"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    missing = completeness.get("missing_required", [])
    if missing:
        st.caption(
            "Missing: " + ", ".join(m.get("label", m.get("field", "")) for m in missing)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        # API status indicator
        api_ok = _check_api_health()
        status_color = "🟢" if api_ok else "🔴"
        status_text = "API Connected" if api_ok else "API Offline"
        st.markdown(
            f'<div style="font-size:0.8rem;color:#7d8590">{status_color} {status_text}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Profile panel
        st.markdown('<div class="sidebar-section">Your Profile</div>', unsafe_allow_html=True)
        _render_profile_panel(st.session_state.profile)

        st.markdown("---")

        # Quick profile update form
        st.markdown('<div class="sidebar-section">Update Profile</div>', unsafe_allow_html=True)
        with st.form("profile_form", clear_on_submit=True):
            field = st.selectbox(
                "Field",
                options=[
                    "age", "monthly_income", "monthly_expenses",
                    "risk_tolerance", "investment_horizon_years",
                    "emergency_fund_months", "financial_goal",
                ],
                label_visibility="collapsed",
            )
            value = st.text_input("Value", placeholder="Enter value…", label_visibility="collapsed")
            submitted = st.form_submit_button("Update", use_container_width=True)
            if submitted and value:
                # Coerce numeric fields
                numeric_fields = {
                    "age", "monthly_income", "monthly_expenses",
                    "investment_horizon_years", "emergency_fund_months",
                }
                parsed_value: Any = value
                if field in numeric_fields:
                    try:
                        parsed_value = int(value)
                    except ValueError:
                        try:
                            parsed_value = float(value)
                        except ValueError:
                            pass

                result = _api_post(
                    "/profile",
                    {"updates": [{"field": field, "value": parsed_value}]},
                )
                if result and result.get("success"):
                    st.session_state.profile = result.get("profile", {})
                    st.session_state.profile["completeness"] = result.get("completeness", {})
                    st.success(f"Updated {field}")
                    st.rerun()
                elif result:
                    st.error(result.get("error", "Update failed"))

        st.markdown("---")

        # Session controls
        st.markdown('<div class="sidebar-section">Session</div>', unsafe_allow_html=True)
        st.caption(f"ID: `{st.session_state.session_id[:20]}…`")
        st.caption(f"Turns: {len(st.session_state.messages) // 2}")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_eval = None
            st.rerun()

        st.markdown("---")

        # Eval summary
        last_eval = st.session_state.last_eval
        if last_eval:
            st.markdown('<div class="sidebar-section">Last Evaluation</div>', unsafe_allow_html=True)
            wt = last_eval.get("weighted_total", 0)
            passed = last_eval.get("passed", False)
            badge = "✅ PASS" if passed else "❌ FAIL"
            st.markdown(f"**{badge}** &nbsp; Score: **{wt:.3f}**")

            metrics = last_eval.get("metrics", {})
            for name, m in metrics.items():
                score = m.get("score", 0)
                bar_color = "#1a7f37" if score >= 0.85 else ("#0969da" if score >= 0.6 else "#b91c1c")
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;'
                    f'color:#7d8590;margin:2px 0">'
                    f'<span>{name}</span>'
                    f'<span style="color:{bar_color};font-weight:600">{score:.2f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.caption("FinSight v1.0 · Educational use only")
        st.caption("Not certified financial advice.")


# ─────────────────────────────────────────────────────────────────────────────
# Main chat flow
# ─────────────────────────────────────────────────────────────────────────────

def _send_message(user_input: str) -> None:
    """
    Send a user message to the agent, display the response, and optionally
    run evaluation on the result.
    """
    # Append user message to history immediately (optimistic UI)
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "meta": {},
    })

    # Build history for API (exclude the message we just added)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    # Call the agent
    with st.spinner("FinSight is thinking…"):
        result = _api_post("/chat", {
            "message": user_input,
            "history": history,
            "session_id": st.session_state.session_id,
        })

    if not result:
        # Error already shown by _api_post
        st.session_state.messages.pop()  # Remove optimistic message
        return

    if not result.get("success"):
        st.error(f"Agent error: {result.get('error', 'Unknown error')}")
        st.session_state.messages.pop()
        return

    answer = result.get("answer", "")
    tool_calls = result.get("tool_calls", [])
    reasoning = result.get("reasoning", [])
    latency_ms = result.get("latency_ms", 0)

    # Auto-evaluate the response
    eval_result: dict[str, Any] = {}
    tool_outputs = [tc.get("output", {}) for tc in tool_calls]
    if tool_outputs:
        with st.spinner("Evaluating response…"):
            eval_api_result = _api_post("/evaluate", {
                "query": user_input,
                "tool_outputs": tool_outputs,
                "response": answer,
            })
        if eval_api_result and eval_api_result.get("success"):
            eval_result = {
                "weighted_total": eval_api_result.get("weighted_total", 0),
                "passed": eval_api_result.get("passed", False),
                "metrics": eval_api_result.get("metrics", {}),
            }
            st.session_state.last_eval = eval_result

    # Update profile from tool call outputs (if get_user_profile was called)
    for tc in tool_calls:
        if tc.get("tool_name") == "get_user_profile":
            output = tc.get("output", {})
            if isinstance(output, dict) and output.get("success", True):
                st.session_state.profile = {
                    k: v for k, v in output.items() if k not in ("success", "error")
                }

    # Append assistant message with full metadata
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "meta": {
            "tool_calls": tool_calls,
            "reasoning": reasoning,
            "latency_ms": latency_ms,
            "eval": eval_result,
        },
    })


def _render_main() -> None:
    """Render the main chat interface."""
    # Header
    st.markdown(
        '<div class="finsight-header">'
        '<span style="font-size:1.8rem">💼</span>'
        '<span class="finsight-title">FinSight</span>'
        '<span class="finsight-badge">AI Financial Advisor</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # API offline warning
    if not _check_api_health():
        st.warning(
            f"⚠️ Cannot connect to the FinSight API at `{API_BASE}`. "
            "Start the server with: `uvicorn app.api:app --port 8000`",
            icon="⚠️",
        )
        return

    # Empty state
    if not st.session_state.messages:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;color:#7d8590">'
            '<div style="font-size:2.5rem;margin-bottom:0.5rem">💼</div>'
            '<div style="font-size:1.1rem;font-weight:500;color:#e6edf3">'
            'Your AI Financial Advisor</div>'
            '<div style="margin-top:0.5rem;font-size:0.85rem">'
            'Ask about stocks, SIP returns, CAGR, or your investment strategy.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Suggestion chips
        suggestions = [
            "What is the current price of RELIANCE.NS?",
            "If I invest ₹5,000/month at 12% for 20 years, what will I get?",
            "My investment grew from ₹1L to ₹4L in 8 years. What's my CAGR?",
            "Latest news on INFY?",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(
                    suggestion,
                    key=f"suggestion_{i}",
                    use_container_width=True,
                ):
                    _send_message(suggestion)
                    st.rerun()

    # Chat history
    for msg in st.session_state.messages:
        _render_chat_message(msg)

    # Input
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([5, 1])
        with cols[0]:
            user_input = st.text_input(
                "Message",
                placeholder="Ask your financial advisor anything…",
                label_visibility="collapsed",
            )
        with cols[1]:
            send = st.form_submit_button("Send ➤", use_container_width=True)

    if send and user_input and user_input.strip():
        _send_message(user_input.strip())
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

_render_sidebar()
_render_main()