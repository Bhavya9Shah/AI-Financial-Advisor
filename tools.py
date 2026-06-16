"""
tools.py — Financial Agent Tool Suite
======================================
Production-quality LangChain tools for a financial advisory agent.

Tools included:
    - get_stock_info       : Fetches live stock data from Yahoo Finance
    - calculate_sip_returns: Computes projected SIP (mutual fund) returns
    - calculate_cagr       : Computes Compound Annual Growth Rate

Design principles:
    - Every tool returns a structured dict (JSON-serialisable)
    - Every tool catches its own errors and returns them inside the dict
      so the agent can reason about failures rather than crashing
    - Docstrings are written for the LLM, not just the developer —
      the agent reads them to decide when and how to call each tool
    - Input validation is explicit and returns human-readable error messages

Dependencies:
    pip install langchain-core yfinance
"""

from __future__ import annotations

import math
from typing import Any

import yfinance as yf
from langchain_core.tools import tool
import json
from pathlib import Path

VALID_FIELDS = {
    "name",
    "age",
    "monthly_income",
    "monthly_expenses",
    "risk_tolerance",
    "investment_horizon_years",
    "existing_investments",
    "financial_goals",
    "emergency_fund_months",
    "has_loans",
    "loan_details"
}

REQUIRED_FIELDS = [
    ("age", "Your age"),
    ("monthly_income", "Your monthly income"),
    ("risk_tolerance", "Your risk tolerance"),
]
def _check_profile_completeness(profile):

    missing_required = []

    for field, label in REQUIRED_FIELDS:

        value = profile.get(field)

        if value is None or value == "":
            missing_required.append({
                "field": field,
                "label": label
            })

    return {
        "is_complete": len(missing_required) == 0,
        "missing_required": missing_required
    }
# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _fmt_large_number(value: float | None) -> str | None:
    """
    Convert a raw large number to a human-readable string with suffix.

    Examples
    --------
    1_500_000_000 → "1.50B"
    42_000_000    → "42.00M"
    950_000       → "950.00K"
    """
    if value is None:
        return None
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:.2f}"


def _safe_round(value: Any, decimals: int = 2) -> float | None:
    """Return a rounded float or None if the value is missing / non-numeric."""
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Tool 1 — Stock Information
# ---------------------------------------------------------------------------

@tool
def get_stock_info(ticker: str) -> dict:
    """
    Fetch real-time stock information for a publicly traded company.

    Use this tool whenever the user asks about a stock's current price,
    valuation, 52-week range, market capitalisation, sector, or any other
    live market data for a specific company.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol.
        - Indian NSE stocks  → append ".NS"  (e.g. "RELIANCE.NS", "INFY.NS")
        - Indian BSE stocks  → append ".BO"  (e.g. "RELIANCE.BO")
        - US stocks          → use plain symbol (e.g. "AAPL", "TSLA", "MSFT")

    Returns
    -------
    dict with keys:
        success        : bool   — False if the lookup failed
        error          : str    — populated only when success is False
        ticker         : str    — normalised ticker used for the lookup
        company_name   : str    — full legal name of the company
        current_price  : float  — latest traded price in local currency
        currency       : str    — currency of the price (e.g. "INR", "USD")
        week_52_high   : float  — highest price in the past 52 weeks
        week_52_low    : float  — lowest price in the past 52 weeks
        price_vs_52w_high_pct : float — % below the 52-week high (negative = below)
        market_cap     : str    — market capitalisation as human-readable string
        pe_ratio       : float  — trailing price-to-earnings ratio (None if N/A)
        sector         : str    — GICS sector classification
        industry       : str    — industry within the sector
        analyst_summary: str    — plain-English one-liner for the agent to use

    Examples
    --------
    get_stock_info("RELIANCE.NS")
    get_stock_info("AAPL")
    get_stock_info("HDFCBANK.NS")
    """
    # ── Input validation ────────────────────────────────────────────────────
    if not ticker or not isinstance(ticker, str):
        return {
            "success": False,
            "error": "Ticker must be a non-empty string (e.g. 'RELIANCE.NS').",
        }

    ticker = ticker.strip().upper()

    if len(ticker) > 20:
        return {
            "success": False,
            "error": f"'{ticker}' is too long to be a valid ticker symbol.",
        }

    # ── Data fetch ──────────────────────────────────────────────────────────
    try:
        stock = yf.Ticker(ticker)
        info = stock.info  # single network call; returns a dict

        # yfinance returns an almost-empty dict for unknown tickers
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            return {
                "success": False,
                "ticker": ticker,
                "error": (
                    f"No data found for ticker '{ticker}'. "
                    "Check the symbol and exchange suffix (e.g. .NS for NSE India)."
                ),
            }

        # ── Extract & normalise fields ───────────────────────────────────────
        current_price = _safe_round(
            info.get("currentPrice") or info.get("regularMarketPrice")
        )
        week_52_high  = _safe_round(info.get("fiftyTwoWeekHigh"))
        week_52_low   = _safe_round(info.get("fiftyTwoWeekLow"))
        market_cap_raw = info.get("marketCap")
        pe_ratio      = _safe_round(info.get("trailingPE"))
        sector        = info.get("sector", "N/A")
        industry      = info.get("industry", "N/A")
        company_name  = info.get("longName") or info.get("shortName", ticker)
        currency      = info.get("currency", "N/A")

        # How far is the current price from its 52-week high? (useful for agent reasoning)
        price_vs_52w_high_pct = None
        if current_price and week_52_high and week_52_high != 0:
            price_vs_52w_high_pct = _safe_round(
                ((current_price - week_52_high) / week_52_high) * 100
            )

        # Plain-English one-liner the agent can embed directly in its response
        analyst_summary = (
            f"{company_name} is currently trading at {currency} {current_price}, "
            f"which is {abs(price_vs_52w_high_pct or 0):.1f}% "
            f"{'below' if (price_vs_52w_high_pct or 0) < 0 else 'above'} its 52-week high "
            f"of {currency} {week_52_high}. "
            f"The stock operates in the {sector} sector"
            + (f" with a P/E ratio of {pe_ratio}." if pe_ratio else ".")
        )

        return {
            "success": True,
            "ticker": ticker,
            "company_name": company_name,
            "current_price": current_price,
            "currency": currency,
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "price_vs_52w_high_pct": price_vs_52w_high_pct,
            "market_cap": _fmt_large_number(market_cap_raw),
            "market_cap_raw": market_cap_raw,
            "pe_ratio": pe_ratio,
            "sector": sector,
            "industry": industry,
            "analyst_summary": analyst_summary,
        }

    except Exception as exc:  # noqa: BLE001
        # Return error inside the dict — never let a tool raise an unhandled
        # exception into the agent loop; the agent should reason about the failure.
        return {
            "success": False,
            "ticker": ticker,
            "error": f"Data fetch failed: {type(exc).__name__}: {exc}",
        }


# ---------------------------------------------------------------------------
# Tool 2 — SIP Returns Calculator
# ---------------------------------------------------------------------------

@tool
def calculate_sip_returns(
    monthly_amount: float,
    annual_rate: float,
    years: int,
) -> dict:
    """
    Calculate the projected future value of a Systematic Investment Plan (SIP).

    A SIP is a disciplined way to invest a fixed amount every month into a
    mutual fund (or any investment vehicle). This tool computes the future
    corpus using compound interest on each monthly instalment.

    Use this tool when the user asks questions like:
        - "If I invest ₹5,000/month for 10 years at 12%, how much will I get?"
        - "What will my SIP be worth?"
        - "How much corpus can I build with monthly investments?"

    Formula applied (standard SIP future-value formula):
        M  = monthly_amount
        r  = annual_rate / 100 / 12   (monthly rate)
        n  = years * 12               (total months)
        FV = M × [((1 + r)^n − 1) / r] × (1 + r)

    Parameters
    ----------
    monthly_amount : float
        Amount invested every month (in any currency; assumed same as output).
        Must be > 0.
    annual_rate : float
        Expected annual return rate as a percentage (e.g. 12 for 12%).
        Typical ranges: debt funds 6–8%, hybrid 9–11%, equity 11–15%.
        Must be > 0 and ≤ 50.
    years : int
        Investment duration in years. Must be between 1 and 50.

    Returns
    -------
    dict with keys:
        success               : bool
        error                 : str    — populated when success is False
        inputs                : dict   — echo of validated inputs
        total_invested        : float  — total amount put in (monthly × months)
        future_value          : float  — projected corpus at end of period
        wealth_gained         : float  — future_value − total_invested
        wealth_gain_pct       : float  — (wealth_gained / total_invested) × 100
        monthly_rate          : float  — monthly rate used in calculation
        total_months          : int    — total number of instalments
        summary               : str    — plain-English summary for agent use

    Examples
    --------
    calculate_sip_returns(5000, 12, 10)   → ~₹11.6L on ₹6L invested
    calculate_sip_returns(10000, 14, 20)  → long-horizon equity SIP
    calculate_sip_returns(2000, 7, 5)     → conservative debt-fund SIP
    """
    # ── Input validation ────────────────────────────────────────────────────
    errors: list[str] = []

    try:
        monthly_amount = float(monthly_amount)
    except (TypeError, ValueError):
        errors.append("monthly_amount must be a number.")

    try:
        annual_rate = float(annual_rate)
    except (TypeError, ValueError):
        errors.append("annual_rate must be a number.")

    try:
        years = int(years)
    except (TypeError, ValueError):
        errors.append("years must be an integer.")

    if not errors:
        if monthly_amount <= 0:
            errors.append("monthly_amount must be greater than 0.")
        if monthly_amount > 10_000_000:
            errors.append("monthly_amount seems unrealistically large (> 1 crore). Please verify.")
        if annual_rate <= 0 or annual_rate > 50:
            errors.append("annual_rate must be between 0 (exclusive) and 50.")
        if years < 1 or years > 50:
            errors.append("years must be between 1 and 50.")

    if errors:
        return {
            "success": False,
            "error": " | ".join(errors),
            "inputs": {
                "monthly_amount": monthly_amount,
                "annual_rate": annual_rate,
                "years": years,
            },
        }

    # ── Calculation ──────────────────────────────────────────────────────────
    monthly_rate  = annual_rate / 100 / 12
    total_months  = years * 12
    total_invested = monthly_amount * total_months

    # Standard SIP future-value formula
    future_value = (
        monthly_amount
        * (((1 + monthly_rate) ** total_months - 1) / monthly_rate)
        * (1 + monthly_rate)
    )

    wealth_gained    = future_value - total_invested
    wealth_gain_pct  = (wealth_gained / total_invested) * 100

    # ── Human-readable summary ────────────────────────────────────────────────
    summary = (
        f"Investing {monthly_amount:,.0f}/month for {years} years at {annual_rate}% annual return: "
        f"Total invested = {total_invested:,.0f} | "
        f"Projected corpus = {future_value:,.0f} | "
        f"Wealth gained = {wealth_gained:,.0f} ({wealth_gain_pct:.1f}% gain on invested capital). "
        f"Note: Returns are projected and not guaranteed. Past market performance may differ."
    )

    return {
        "success": True,
        "inputs": {
            "monthly_amount": monthly_amount,
            "annual_rate": annual_rate,
            "years": years,
        },
        "total_invested": round(total_invested, 2),
        "future_value": round(future_value, 2),
        "wealth_gained": round(wealth_gained, 2),
        "wealth_gain_pct": round(wealth_gain_pct, 2),
        "monthly_rate": round(monthly_rate, 6),
        "total_months": total_months,
        "summary": summary,
    }
# ---------------------------------------------------------------------------
# Tool 3 — user profile
# ---------------------------------------------------------------------------

@tool
def get_user_profile() -> dict:
    """
    Retrieve the current user's financial profile.

    IMPORTANT: Call this tool FIRST before giving any personalised
    financial advice.

    Returns the profile and indicates whether it is complete.
    """
    profile_path = Path("user_profile.json")

    try:
        with open(profile_path, "r") as file:
            profile = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Profile file not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Profile file is corrupted."
        }

    completeness = _check_profile_completeness(profile)

    return {
        **profile,
        "completeness": completeness
    }
# ---------------------------------------------------------------------------
# Tool 4 — update_user_profile
# ---------------------------------------------------------------------------
@tool
def update_user_profile(field: str, value:str) -> dict:
    """
    Update a field in the user's financial profile.
    """

    profile_path = Path("user_profile.json")

    try:
        with open(profile_path, "r") as file:
            profile = json.load(file)

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Profile file not found."
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Profile file is corrupted."
        }
    if field not in VALID_FIELDS:
        return {
            "success": False,
            "error": f"Invalid field: {field}"
        }
    profile[field] = value

    with open(profile_path, "w") as file:
        json.dump(profile, file, indent=2)

    completeness = _check_profile_completeness(profile)

    return  {
    "success": True,
    "updated_field": field,
    "new_value": value,
    "completeness": completeness
    }
# ---------------------------------------------------------------------------
# Tool 5 — CAGR Calculator
# ---------------------------------------------------------------------------

@tool
def calculate_cagr(
    initial_value: float,
    final_value: float,
    years: float,
) -> dict:
    """
    Calculate the Compound Annual Growth Rate (CAGR) between two values.

    CAGR answers the question: "What constant annual return rate would turn
    my initial investment into the final value over this many years?"

    It smooths out year-to-year volatility and is the standard way to
    compare investment performance across different asset classes or time
    periods. A Nifty 50 CAGR of 12% since 2000 means ₹1L became ₹13.7L.

    Use this tool when the user asks:
        - "What is the CAGR of Nifty 50 over 10 years?"
        - "My investment grew from ₹1L to ₹3.5L in 7 years. What was the return?"
        - "Compare the CAGR of gold vs equity"

    Formula:
        CAGR = (final_value / initial_value) ^ (1 / years) − 1

    Parameters
    ----------
    initial_value : float
        Starting value of the investment. Must be > 0.
    final_value   : float
        Ending value of the investment. Must be > 0.
        Can be less than initial_value (negative growth is valid).
    years         : float
        Number of years over which the growth occurred.
        Accepts decimals (e.g. 2.5 for 2.5 years). Must be > 0.

    Returns
    -------
    dict with keys:
        success              : bool
        error                : str    — populated when success is False
        inputs               : dict   — echo of validated inputs
        cagr_pct             : float  — CAGR expressed as a percentage
        growth_multiple      : float  — final / initial (e.g. 3.5 = "3.5x growth")
        absolute_gain        : float  — final_value − initial_value
        absolute_gain_pct    : float  — simple (non-compounded) % gain
        direction            : str    — "growth", "decline", or "flat"
        interpretation       : str    — plain-English benchmark comparison
        summary              : str    — one-liner for agent use

    Examples
    --------
    calculate_cagr(100000, 350000, 7)    → CAGR ≈ 19.6% (strong equity return)
    calculate_cagr(100000, 180000, 10)   → CAGR ≈ 6.05% (typical debt return)
    calculate_cagr(50000, 45000, 2)      → CAGR ≈ -5.1% (loss scenario)
    """
    # ── Input validation ────────────────────────────────────────────────────
    errors: list[str] = []

    try:
        initial_value = float(initial_value)
    except (TypeError, ValueError):
        errors.append("initial_value must be a number.")

    try:
        final_value = float(final_value)
    except (TypeError, ValueError):
        errors.append("final_value must be a number.")

    try:
        years = float(years)
    except (TypeError, ValueError):
        errors.append("years must be a number.")

    if not errors:
        if initial_value <= 0:
            errors.append("initial_value must be greater than 0.")
        if final_value <= 0:
            errors.append("final_value must be greater than 0.")
        if years <= 0:
            errors.append("years must be greater than 0.")
        if years > 100:
            errors.append("years > 100 is not a realistic investment horizon.")

    if errors:
        return {
            "success": False,
            "error": " | ".join(errors),
            "inputs": {
                "initial_value": initial_value,
                "final_value": final_value,
                "years": years,
            },
        }

    # ── Calculation ──────────────────────────────────────────────────────────
    growth_multiple   = final_value / initial_value
    cagr              = (growth_multiple ** (1 / years)) - 1
    cagr_pct          = cagr * 100
    absolute_gain     = final_value - initial_value
    absolute_gain_pct = (absolute_gain / initial_value) * 100

    if cagr_pct > 0.05:
        direction = "growth"
    elif cagr_pct < -0.05:
        direction = "decline"
    else:
        direction = "flat"

    # ── Benchmark interpretation ──────────────────────────────────────────────
    # Helps the agent contextualise the number for the user
    if direction == "growth":
        if cagr_pct >= 20:
            benchmark = "exceptional (better than most equity mutual funds)"
        elif cagr_pct >= 14:
            benchmark = "strong (above Nifty 50 historical average of ~12–14%)"
        elif cagr_pct >= 10:
            benchmark = "good (in line with long-term equity market returns)"
        elif cagr_pct >= 7:
            benchmark = "moderate (comparable to debt/hybrid fund returns)"
        elif cagr_pct >= 4:
            benchmark = "below inflation — real returns may be near zero"
        else:
            benchmark = "poor — likely below inflation"
    elif direction == "decline":
        benchmark = f"negative return of {abs(cagr_pct):.2f}%/year — capital erosion"
    else:
        benchmark = "flat — no real growth"

    interpretation = f"A CAGR of {cagr_pct:.2f}% is considered {benchmark}."

    summary = (
        f"{initial_value:,.0f} grew to {final_value:,.0f} over {years:.1f} years "
        f"({growth_multiple:.2f}x). CAGR = {cagr_pct:.2f}%. {interpretation}"
    )

    return {
        "success": True,
        "inputs": {
            "initial_value": initial_value,
            "final_value": final_value,
            "years": years,
        },
        "cagr_pct": round(cagr_pct, 4),
        "growth_multiple": round(growth_multiple, 4),
        "absolute_gain": round(absolute_gain, 2),
        "absolute_gain_pct": round(absolute_gain_pct, 2),
        "direction": direction,
        "interpretation": interpretation,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Tool registry — import this list into your agent initialisation
# ---------------------------------------------------------------------------

# Usage in your agent:
#
#   from tools import FINANCIAL_TOOLS
#   agent = create_react_agent(llm=llm, tools=FINANCIAL_TOOLS, ...)
#
REQUIRED_FIELDS = [
    ("age", "Your age"),
    ("monthly_income", "Your monthly income"),
    ("risk_tolerance", "Your risk tolerance"),
]
OPTIONAL_FIELDS = [
    ("investment_horizon_years", "Investment horizon"),
    ("monthly_expenses", "Monthly expenses"),
    ("financial_goals", "Financial goals"),
]
def _check_profile_completeness(profile: dict) -> dict:

    missing_required = []
    missing_optional = []

    for field, label in REQUIRED_FIELDS:

        value = profile.get(field)

        if value is None or value == "" or value == []:
            missing_required.append({
                "field": field,
                "label": label
            })

    for field, label in OPTIONAL_FIELDS:

        value = profile.get(field)

        if value is None or value == "" or value == []:
            missing_optional.append({
                "field": field,
                "label": label
            })

    total_fields = len(REQUIRED_FIELDS) + len(OPTIONAL_FIELDS)

    filled_fields = (
        total_fields
        - len(missing_required)
        - len(missing_optional)
    )

    if missing_required:
        tier = "basic"
    elif missing_optional:
        tier = "intermediate"
    else:
        tier = "complete"

    return {
        "is_complete": len(missing_required) == 0,
        "tier": tier,
        "completeness_pct": round(
            (filled_fields / total_fields) * 100
        ),
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "filled_count": filled_fields,
        "total_count": total_fields
    }
FINANCIAL_TOOLS = [
    get_stock_info,
    calculate_sip_returns,
    calculate_cagr,
    get_user_profile,
    update_user_profile,
]


# ---------------------------------------------------------------------------
# Quick smoke-test — run `python tools.py` to verify without an agent
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("TOOL SMOKE TEST")
    print("=" * 60)

    # Test 1 — valid Indian stock
    print("\n[1] get_stock_info('INFY.NS')")
    result = get_stock_info.invoke({"ticker": "INFY.NS"})
    print(json.dumps(result, indent=2))

    # Test 2 — invalid ticker
    print("\n[2] get_stock_info('NOTASTOCK')")
    result = get_stock_info.invoke({"ticker": "NOTASTOCK"})
    print(json.dumps(result, indent=2))

    # Test 3 — SIP calculation
    print("\n[3] calculate_sip_returns(5000, 12, 10)")
    result = calculate_sip_returns.invoke({
        "monthly_amount": 5000,
        "annual_rate": 12,
        "years": 10,
    })
    print(json.dumps(result, indent=2))

    # Test 4 — invalid SIP (bad rate)
    print("\n[4] calculate_sip_returns(5000, -5, 10)  ← should fail gracefully")
    result = calculate_sip_returns.invoke({
        "monthly_amount": 5000,
        "annual_rate": -5,
        "years": 10,
    })
    print(json.dumps(result, indent=2))

    # Test 5 — CAGR, positive growth
    print("\n[5] calculate_cagr(100000, 350000, 7)")
    result = calculate_cagr.invoke({
        "initial_value": 100000,
        "final_value": 350000,
        "years": 7,
    })
    print(json.dumps(result, indent=2))

    # Test 6 — CAGR, loss scenario
    print("\n[6] calculate_cagr(100000, 75000, 3)  ← loss scenario")
    result = calculate_cagr.invoke({
        "initial_value": 100000,
        "final_value": 75000,
        "years": 3,
    })
    print(json.dumps(result, indent=2))
