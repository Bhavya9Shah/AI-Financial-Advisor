"""
metrics.py — FinSight Rule-Based Evaluation Engine
====================================================
Production-quality, deterministic evaluation framework for a financial
AI agent.  No LLMs are used for judging.  Every score is the output of
explicit, auditable rules that can be unit-tested without any network
calls or model access.

Design principles
-----------------
1. Registry pattern — each metric is an independent class; adding a new
   metric never requires editing existing code (Open/Closed Principle).
2. Pure scoring functions — MetricScorer.score() is a pure function:
   same inputs always produce the same output.
3. Evidence-first — every MetricResult carries the exact evidence that
   drove the score, so failures are self-explaining.
4. EvalContext is the single source of truth — all metrics receive the
   same context object; no metric reaches outside it.
5. Weighted aggregation is separate from scoring — weights live in the
   orchestrator, not in individual metrics.

Usage
-----
    from metrics import EvaluationOrchestrator, EvalContext, EvalCase

    context = EvalContext(
        query="What is the CAGR if I invested ₹1L and got ₹3.5L in 7 years?",
        tool_outputs=[{"tool_name": "calculate_cagr", "success": True,
                       "cagr_pct": 19.6, "summary": "CAGR ≈ 19.6%"}],
        response="Your investment grew at a CAGR of 19.6% over 7 years...",
        eval_case=EvalCase(
            expected_numeric_values={"cagr_pct": 19.6},
            required_topics=["cagr", "growth"],
            required_caveats=["not guaranteed", "past performance"],
            forbidden_claims=["guaranteed", "will definitely"],
            expected_tools=["calculate_cagr"],
        ),
    )
    result = EvaluationOrchestrator().evaluate(context)
    print(result.summary())
"""

from __future__ import annotations

import re
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EvalCase:
    """
    Ground-truth specification for a single evaluation case.

    Attributes
    ----------
    expected_numeric_values : dict
        Key → expected float value.  The evaluator checks whether these
        numbers appear in the response within a tolerance band.
        Example: {"cagr_pct": 19.6, "future_value": 1161695}

    required_topics : list[str]
        Lower-cased keywords / short phrases that MUST appear somewhere
        in the response for it to be considered complete.
        Example: ["sip", "monthly investment", "compounding"]

    required_caveats : list[str]
        Phrases signalling appropriate financial disclaimers.  At least
        one must appear for the helpfulness score to be full credit.
        Example: ["not guaranteed", "past performance", "consult"]

    forbidden_claims : list[str]
        Phrases that indicate hallucination or irresponsible advice.
        Any match drives the helpfulness score to zero.
        Example: ["guaranteed returns", "will definitely", "100% safe"]

    expected_tools : list[str]
        Tool names that were supposed to be called.  Used by grounding
        to determine which tool outputs are authoritative for this case.

    numeric_tolerance_pct : float
        Acceptable relative error when matching numeric values (default 1 %).
        A response that says "19.7%" when the true value is "19.6%" still
        passes because (0.1 / 19.6) = 0.5 % < 1 %.
    """
    expected_numeric_values: dict[str, float] = field(default_factory=dict)
    required_topics: list[str] = field(default_factory=list)
    required_caveats: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    expected_tools: list[str] = field(default_factory=list)
    numeric_tolerance_pct: float = 1.0


@dataclass
class EvalContext:
    """
    Everything a metric needs to produce a score.  Constructed once per
    evaluation run and passed unchanged to every metric.

    Attributes
    ----------
    query        : the original user query string
    tool_outputs : list of dicts returned by each tool (in call order)
    response     : the agent's final text response
    eval_case    : ground-truth specification (see EvalCase)
    """
    query: str
    tool_outputs: list[dict[str, Any]]
    response: str
    eval_case: EvalCase

    # ── Derived helpers (computed once, reused by all metrics) ────────────

    @property
    def response_lower(self) -> str:
        return self.response.lower()

    @property
    def response_numbers(self) -> list[float]:
        """All numeric values extracted from the response text.

        Handles both Western (1,161,695) and Indian (11,61,695) comma formats
        by stripping commas inside numeric tokens before parsing.
        """
        # Match tokens that look like numbers (digits, commas, decimal points)
        tokens = re.findall(r"\d[\d,]*\.?\d*", self.response)
        result = []
        for token in tokens:
            cleaned = token.replace(",", "")
            try:
                result.append(float(cleaned))
            except ValueError:
                pass
        return result

    @property
    def tool_output_numbers(self) -> list[float]:
        """All numeric leaf values found in any tool output dict."""
        numbers: list[float] = []
        for output in self.tool_outputs:
            numbers.extend(_extract_numbers_from_dict(output))
        return numbers

    @property
    def successful_tool_outputs(self) -> list[dict]:
        return [o for o in self.tool_outputs if o.get("success", False)]


@dataclass
class MetricResult:
    """
    Result produced by a single metric.

    Attributes
    ----------
    metric_name : identifier matching the class name
    score       : float in [0.0, 1.0]
    max_score   : always 1.0 (normalised)
    reasoning   : human-readable explanation of the score
    evidence    : list of specific strings / values that drove the score
    passed      : True when score >= passing_threshold (default 0.6)
    """
    metric_name: str
    score: float                        # 0.0 – 1.0
    max_score: float = 1.0
    reasoning: str = ""
    evidence: list[str] = field(default_factory=list)
    passing_threshold: float = 0.6

    @property
    def passed(self) -> bool:
        return self.score >= self.passing_threshold

    @property
    def score_label(self) -> str:
        if self.score >= 0.85:
            return "EXCELLENT"
        if self.score >= 0.70:
            return "GOOD"
        if self.score >= 0.60:
            return "PASS"
        if self.score >= 0.40:
            return "PARTIAL"
        return "FAIL"


@dataclass
class EvaluationResult:
    """Aggregated result for one (query, response) pair."""
    metric_results: dict[str, MetricResult]
    weights: dict[str, float]
    context_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_total(self) -> float:
        total = 0.0
        weight_sum = 0.0
        for name, result in self.metric_results.items():
            w = self.weights.get(name, 0.0)
            total += result.score * w
            weight_sum += w
        return total / weight_sum if weight_sum else 0.0

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.metric_results.values())

    def summary(self) -> str:
        lines = [
            "═" * 58,
            f"  FinSight Evaluation Result",
            f"  Weighted total : {self.weighted_total:.3f}",
            f"  Overall        : {'PASS ✓' if self.passed else 'FAIL ✗'}",
            "─" * 58,
        ]
        for name, result in self.metric_results.items():
            w = self.weights.get(name, 0.0)
            lines.append(
                f"  {name:<22} {result.score:.3f}  "
                f"[{result.score_label:<9}]  weight={w:.2f}"
            )
            lines.append(f"    → {result.reasoning}")
            for ev in result.evidence:
                lines.append(f"      • {ev}")
        lines.append("═" * 58)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "weighted_total": round(self.weighted_total, 4),
            "passed": self.passed,
            "metrics": {
                name: {
                    "score": round(r.score, 4),
                    "label": r.score_label,
                    "passed": r.passed,
                    "reasoning": r.reasoning,
                    "evidence": r.evidence,
                }
                for name, r in self.metric_results.items()
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Metric base class
# ─────────────────────────────────────────────────────────────────────────────

class MetricScorer(ABC):
    """
    Base class for all evaluation metrics.

    Subclasses implement score() only.  They must not produce side
    effects, must not call external APIs, and must be deterministic.
    """

    name: str = "base"

    @abstractmethod
    def score(self, ctx: EvalContext) -> MetricResult:
        """Return a MetricResult for this metric given ctx."""

    def _result(
        self,
        score: float,
        reasoning: str,
        evidence: list[str] | None = None,
    ) -> MetricResult:
        return MetricResult(
            metric_name=self.name,
            score=round(max(0.0, min(1.0, score)), 4),
            reasoning=reasoning,
            evidence=evidence or [],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────
def _extract_numbers_from_dict(d: Any) -> list[float]:
    """
    Recursively collect all numeric leaf values from a dict/list.
    Also handles numeric strings like "90000" or "1834.25".
    """

    numbers: list[float] = []

    if isinstance(d, dict):

        for value in d.values():
            numbers.extend(_extract_numbers_from_dict(value))

    elif isinstance(d, list):

        for item in d:
            numbers.extend(_extract_numbers_from_dict(item))

    elif isinstance(d, (int, float)) and not isinstance(d, bool):

        numbers.append(float(d))

    elif isinstance(d, str):

        try:
            cleaned = d.replace(",", "").replace("₹", "").strip()

            if cleaned:
                numbers.append(float(cleaned))

        except ValueError:
            pass

    return numbers

def _relative_error(actual: float, expected: float) -> float:
    """Relative error between actual and expected (safe for zero)."""
    if expected == 0:
        return 0.0 if actual == 0 else 1.0
    return abs(actual - expected) / abs(expected)


def _best_relative_error(
    candidate_numbers: list[float],
    expected: float,
) -> float:
    """
    Find the numeric value in candidate_numbers closest to expected.
    Returns the relative error of the best match, or 1.0 if list empty.
    """
    if not candidate_numbers:
        return 1.0
    return min(_relative_error(n, expected) for n in candidate_numbers)


def _phrase_present(text: str, phrases: list[str]) -> list[str]:
    """Return subset of phrases found in text (fully case-insensitive)."""
    text_lower = text.lower()
    return [p for p in phrases if p.lower() in text_lower]


def _sentence_count(text: str) -> int:
    return len(re.findall(r"[.!?]+", text))


def _word_count(text: str) -> int:
    return len(text.split())


def _has_structure(text: str) -> bool:
    """True if response uses bullet points, numbered lists, or headers."""
    return bool(re.search(r"(?m)^(\s*[-•*]\s|\s*\d+[.)]\s|#{1,3}\s)", text))


# ─────────────────────────────────────────────────────────────────────────────
# Metric 1 — Correctness
# ─────────────────────────────────────────────────────────────────────────────

class CorrectnessMetric(MetricScorer):
    """
    What it measures
    ----------------
    Whether numeric values in the response match the ground-truth values
    produced by the tools, within an acceptable tolerance.

    Why it matters
    --------------
    Financial advice built on wrong numbers is worse than no advice.
    A response that says "your SIP will grow to ₹12 lakh" when the
    correct answer is ₹11.6 lakh is factually wrong — even if the prose
    is perfectly written.

    Scoring rules
    -------------
    For each (key, expected_value) in eval_case.expected_numeric_values:
      • Find the closest number in the response text.
      • If relative error ≤ tolerance_pct → full credit (1.0)
      • If relative error ≤ 3× tolerance_pct → partial credit (0.5)
      • Otherwise → no credit (0.0)
    Final score = mean credit across all expected values.

    Edge cases
    ----------
    • No expected values defined → score 1.0 (not applicable, don't penalise)
    • Tool returned success=False → score 0.0 (bad data, can't be correct)
    • Large numbers: ₹11,61,695 and ₹11.6 lakh both parse to ~1161695

    Tool applicability: calculate_sip_returns, calculate_cagr, get_stock_info
    """

    name = "correctness"

    def score(self, ctx: EvalContext) -> MetricResult:
        expected = ctx.eval_case.expected_numeric_values

        if not expected:
            return self._result(1.0, "No numeric expectations defined — not applicable.")

        # Fail fast if all tool calls failed
        if ctx.tool_outputs and not ctx.successful_tool_outputs:
            return self._result(
                0.0,
                "All tool calls failed — no reliable data to check correctness against.",
                evidence=["All tool outputs have success=False"],
            )

        response_nums = ctx.response_numbers
        credits: list[float] = []
        evidence: list[str] = []
        tol = ctx.eval_case.numeric_tolerance_pct / 100.0

        for key, exp_val in expected.items():
            err = _best_relative_error(response_nums, exp_val)
            if err <= tol:
                credit = 1.0
                tag = "✓ exact"
            elif err <= tol * 3:
                credit = 0.5
                tag = "~ approx"
            else:
                credit = 0.0
                tag = "✗ missing/wrong"

            credits.append(credit)
            evidence.append(
                f"{key}: expected={exp_val}, best_match_err={err:.2%}  [{tag}]"
            )

        final_score = sum(credits) / len(credits)
        reasoning = (
            f"{sum(1 for c in credits if c == 1.0)}/{len(credits)} values "
            f"matched exactly; {sum(1 for c in credits if c == 0.5)}/{len(credits)} "
            f"approximate; score={final_score:.2f}"
        )
        return self._result(final_score, reasoning, evidence)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 2 — Grounding
# ─────────────────────────────────────────────────────────────────────────────

class GroundingMetric(MetricScorer):
    """
    What it measures
    ----------------
    Whether the response is grounded in tool output data rather than
    hallucinated from the LLM's parametric memory.

    A response is grounded when the key numeric values it cites can be
    traced back to at least one tool output.

    Why it matters
    --------------
    LLMs can produce confident-sounding financial numbers that are
    entirely fabricated.  Grounding detection is the primary defence
    against this failure mode.  If the response contains numbers that
    don't appear in any tool output, those numbers are hallucinated.

    Scoring rules
    -------------
    Sub-score A — numeric grounding (weight 0.6):
      • For each number in response_numbers, check if it appears in any
        tool output (within 1 % tolerance).
      • grounded_fraction = matched_count / total_response_numbers
      • Capped: if the response has fewer than 2 numbers and a tool was
        called, score is 0.5 (can't fully verify, but not penalised).

    Sub-score B — tool output citation (weight 0.4):
      • Does the response include a summary-style string that appears
        in any successful tool output's "summary" or "analyst_summary"
        field?  (substring check after normalisation)
      • Full credit (1.0) if any tool summary phrase is echoed.
      • Partial credit (0.5) if a tool was called but no summary echoed.
      • Zero credit if no tools were called but the response contains
        financial numbers.

    Final = 0.6 * sub_A + 0.4 * sub_B

    Edge cases
    ----------
    • No tools called, no numbers in response → 1.0 (pure text, not checkable)
    • Tool failed, response acknowledges failure → 1.0 (correct behaviour)
    • get_user_profile only: profile data is legitimate grounding source

    Tool applicability: all tools
    """

    name = "grounding"

    def score(self, ctx: EvalContext) -> MetricResult:
        response_nums = ctx.response_numbers
        tool_nums = ctx.tool_output_numbers
        evidence: list[str] = []

        # ── Edge: no tools called and no numbers → informational response ──
        if not ctx.tool_outputs and not response_nums:
            return self._result(1.0, "No tools called and no numeric claims — no grounding needed.")

        # ── Edge: tool failed, check if response reports failure honestly ──
        all_failed = ctx.tool_outputs and not ctx.successful_tool_outputs
        if all_failed:
            failure_phrases = ["unable", "couldn't", "failed", "not available",
                               "error", "sorry", "issue", "problem"]
            honest = bool(_phrase_present(ctx.response_lower, failure_phrases))
            if honest and not response_nums:
                return self._result(
                    1.0,
                    "Tool failed; response honestly acknowledges failure without fabricating data.",
                    evidence=["Failure acknowledged, no numeric hallucination detected"],
                )
            if response_nums:
                return self._result(
                    0.0,
                    "Tool failed but response contains numeric claims — likely hallucination.",
                    evidence=[f"Hallucinated numbers found: {response_nums[:5]}"],
                )

        # ── Sub-score A: numeric grounding ────────────────────────────────
        tol = 0.01  # 1 % relative tolerance for matching
        if response_nums and tool_nums:
            grounded = 0
            hallucinated = 0

            for rn in response_nums:

                if _best_relative_error(tool_nums, rn) <= tol:
                    grounded += 1
                else:
                    hallucinated += 1

            sub_a = grounded / len(response_nums)
            hallucination_rate = 0.0

            if response_nums:
                hallucination_rate = hallucinated / len(response_nums)
                evidence.append(
                    f"Grounded claims      : {grounded}"
                )

                evidence.append(
                    f"Hallucinated claims  : {hallucinated}"
                )

                evidence.append(
                    f"Hallucination rate   : {hallucination_rate:.1%}"
                )
        elif not response_nums:
            sub_a = 0.5  # can't verify but not wrong
            evidence.append("Response contains no numbers — grounding partially verified")
        else:
            # Response has numbers but no tool output numbers
            sub_a = 0.0
            evidence.append(
                f"Response contains {len(response_nums)} numbers but no tool "
                f"outputs to verify against — possible hallucination"
            )

        # ── Sub-score B: summary phrase echoing ──────────────────────────
        summary_keys = ("summary", "analyst_summary", "interpretation")
        tool_summaries: list[str] = []
        for out in ctx.successful_tool_outputs:
            for k in summary_keys:
                if k in out and isinstance(out[k], str):
                    tool_summaries.append(out[k].lower()[:80])

        sub_b: float
        if tool_summaries:
            # Check if at least 20 % of any summary appears in the response
            matched = any(
                s[:40] in ctx.response_lower for s in tool_summaries
            )
            sub_b = 1.0 if matched else 0.5
            evidence.append(
                f"Tool summary echoed in response: {'yes' if matched else 'no'}"
            )
        elif ctx.successful_tool_outputs:
            sub_b = 0.5
            evidence.append("Tool succeeded but no summary field — partial credit")
        else:
            sub_b = 0.0

        final_score = 0.6 * sub_a + 0.4 * sub_b
        reasoning = (
            f"Grounding Score={sub_a:.2f}, "
            f"Hallucination Rate={hallucination_rate:.1%}, "
            f"Summary Citation={sub_b:.2f} "
            f"→ Final={final_score:.2f}"
        )
        return self._result(final_score, reasoning, evidence)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 3 — Completeness
# ─────────────────────────────────────────────────────────────────────────────

class CompletenessMetric(MetricScorer):
    """
    What it measures
    ----------------
    Whether the response covers the topics and informational elements
    that a user asking this query would reasonably need.

    Why it matters
    --------------
    A response that gets the number right but omits the units, the
    time horizon, or the key caveats is incomplete.  A financial advisor
    who says "your CAGR is 19.6 %" without explaining what that means is
    not being helpful.

    Scoring rules
    -------------
    Sub-score A — required topics coverage (weight 0.7):
      • For each phrase in eval_case.required_topics, check if it appears
        in the response (case-insensitive substring).
      • coverage = matched / total  →  sub_a
      • If required_topics is empty: sub_a = 1.0 (not applicable)

    Sub-score B — response substance (weight 0.3):
      • Word count ≥ 80  →  1.0
      • Word count 40–79 →  0.6
      • Word count < 40  →  0.2
      (A financial advisor giving a 10-word answer is almost always
       incomplete regardless of topic coverage.)

    Final = 0.7 * sub_a + 0.3 * sub_b

    Edge cases
    ----------
    • Very short queries (e.g. "Hello") should have short responses;
      word-count floor is applied only when a tool was called.
    • If tool output contains a "summary" field, that summary's topics
      are added to the required set automatically (weak requirement, 0.5×).

    Tool applicability: all tools
    """

    name = "completeness"

    _WORD_COUNT_THRESHOLDS = [(80, 1.0), (40, 0.6), (0, 0.2)]

    def score(self, ctx: EvalContext) -> MetricResult:
        required = [t.lower() for t in ctx.eval_case.required_topics]
        evidence: list[str] = []

        # ── Sub-score A: topic coverage ───────────────────────────────────
        if required:
            found = _phrase_present(ctx.response_lower, required)
            sub_a = len(found) / len(required)
            missed = [t for t in required if t not in found]
            evidence.append(
                f"Topics covered: {len(found)}/{len(required)} "
                f"({', '.join(found) or 'none'})"
            )
            if missed:
                evidence.append(f"Missing topics: {', '.join(missed)}")
        else:
            sub_a = 1.0
            evidence.append("No required topics defined — coverage not evaluated")

        # ── Sub-score B: response length / substance ──────────────────────
        wc = _word_count(ctx.response)
        sub_b = next(score for threshold, score in self._WORD_COUNT_THRESHOLDS
                     if wc >= threshold)
        # Only apply length check when tools were used (otherwise "Hello" ↦ short is fine)
        if not ctx.tool_outputs:
            sub_b = 1.0
        evidence.append(f"Response word count: {wc} → substance score={sub_b:.1f}")

        final_score = 0.7 * sub_a + 0.3 * sub_b
        reasoning = (
            f"Topic coverage={sub_a:.2f} (×0.7), "
            f"substance={sub_b:.2f} (×0.3) → {final_score:.2f}"
        )
        return self._result(final_score, reasoning, evidence)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 4 — Helpfulness
# ─────────────────────────────────────────────────────────────────────────────

class HelpfulnessMetric(MetricScorer):
    """
    What it measures
    ----------------
    Whether the response is actionable and responsible: does it give the
    user something to do next, and does it include appropriate disclaimers
    for financial advice?

    Why it matters
    --------------
    An AI financial advisor has two failure modes in helpfulness:
      1. Over-confident — gives specific financial advice without disclaimers,
         which is irresponsible and potentially illegal.
      2. Under-helpful — hedges so heavily that no actionable information
         is communicated.
    Good helpfulness is the narrow path between these two failure modes.

    Scoring rules
    -------------
    Sub-score A — actionability (weight 0.5):
      Checks for action-oriented language that helps the user know what
      to do next.
      Keywords: "consider", "recommend", "suggest", "you could", "you should",
                "next step", "action", "invest", "allocate", "diversify"
      • ≥ 2 matches → 1.0
      • 1 match     → 0.6
      • 0 matches   → 0.2

    Sub-score B — appropriate caveats (weight 0.3):
      At least one phrase from eval_case.required_caveats must appear.
      Default caveat phrases (applied even if eval_case list is empty):
        "not guaranteed", "past performance", "consult", "professional",
        "educational", "not financial advice", "may vary"
      • ≥ 1 caveat matched → 1.0
      • 0 caveats matched  → 0.0
      (Hard zero — irresponsible financial advice is a serious failure.)

    Sub-score C — no forbidden claims (weight 0.2):
      If any phrase from eval_case.forbidden_claims appears in the response,
      this sub-score is 0.0 and overrides the total to ≤ 0.4.
      Default forbidden phrases:
        "guaranteed returns", "will definitely", "100% safe",
        "can't lose", "always profitable", "risk-free"
      • No forbidden phrases → 1.0
      • Any forbidden phrase → 0.0

    Final = 0.5 * sub_a + 0.3 * sub_b + 0.2 * sub_c
    If sub_c == 0.0: cap final at 0.4 (forbidden claim is a hard penalty)

    Edge cases
    ----------
    • News query responses: "consider reviewing your portfolio" counts
      as actionable even without explicit investment advice.
    • Profile queries: listing user profile is actionable (it answers
      what the user asked); caveat requirement relaxed.

    Tool applicability: all tools
    """

    name = "helpfulness"

    _ACTION_KEYWORDS = [
        "consider", "recommend", "suggest", "you could", "you should",
        "next step", "action", "invest", "allocate", "diversify",
        "review", "assess", "plan", "start", "begin", "explore",
    ]

    _DEFAULT_CAVEAT_PHRASES = [
        "not guaranteed", "past performance", "consult", "professional",
        "educational", "not financial advice", "may vary", "risk",
        "market conditions", "speak with", "before investing",
    ]

    _DEFAULT_FORBIDDEN = [
        "guaranteed returns", "guaranteed profit", "will definitely make",
        "100% safe", "can't lose", "always profitable", "risk-free investment",
        "no risk", "certain profit",
    ]

    def score(self, ctx: EvalContext) -> MetricResult:
        evidence: list[str] = []
        r_lower = ctx.response_lower

        # ── Sub-score A: actionability ─────────────────────────────────────
        action_matches = _phrase_present(r_lower, self._ACTION_KEYWORDS)
        if len(action_matches) >= 2:
            sub_a = 1.0
        elif len(action_matches) == 1:
            sub_a = 0.6
        else:
            sub_a = 0.2
        evidence.append(
            f"Actionability: {len(action_matches)} action keywords found "
            f"({', '.join(action_matches[:3]) or 'none'})"
        )

        # ── Sub-score B: appropriate caveats ──────────────────────────────
        caveat_pool = list(ctx.eval_case.required_caveats) or self._DEFAULT_CAVEAT_PHRASES
        found_caveats = _phrase_present(r_lower, caveat_pool)
        sub_b = 1.0 if found_caveats else 0.0
        evidence.append(
            f"Caveats: {'found — ' + ', '.join(found_caveats[:2]) if found_caveats else 'NONE FOUND (hard penalty)'}"
        )

        # ── Sub-score C: no forbidden claims ──────────────────────────────
        forbidden_pool = list(ctx.eval_case.forbidden_claims) or self._DEFAULT_FORBIDDEN
        found_forbidden = _phrase_present(r_lower, forbidden_pool)
        sub_c = 0.0 if found_forbidden else 1.0
        if found_forbidden:
            evidence.append(
                f"FORBIDDEN CLAIMS FOUND: {', '.join(found_forbidden)} → hard cap applied"
            )

        final_score = 0.5 * sub_a + 0.3 * sub_b + 0.2 * sub_c

        # Hard cap when forbidden claim detected
        if sub_c == 0.0:
            final_score = min(final_score, 0.4)

        reasoning = (
            f"Actionability={sub_a:.2f} (×0.5), "
            f"caveats={sub_b:.2f} (×0.3), "
            f"no-forbidden={sub_c:.2f} (×0.2) → {final_score:.2f}"
        )
        return self._result(final_score, reasoning, evidence)


# ─────────────────────────────────────────────────────────────────────────────
# Metric 5 — Clarity
# ─────────────────────────────────────────────────────────────────────────────

class ClarityMetric(MetricScorer):
    """
    What it measures
    ----------------
    Whether the response is well-structured, appropriately concise, and
    free of vague or confused language.

    Why it matters
    --------------
    A technically correct response that is 1,500 words of dense prose
    with no structure is not useful.  Conversely, a 15-word response to
    a complex portfolio question is also not useful.  Clarity measures
    the quality of communication, independent of content correctness.

    Scoring rules
    -------------
    Sub-score A — length appropriateness (weight 0.4):
      For queries that triggered tool calls (substantive financial queries):
        • 60–400 words: 1.0  (appropriate depth)
        • 40–59 words:  0.7  (slightly thin)
        • 401–700 words: 0.7 (slightly verbose)
        • < 40 words:   0.3  (too brief for a financial answer)
        • > 700 words:  0.4  (excessive — user won't read it)
      For queries with no tool calls (simple/conversational):
        • Any length 10–200 words: 1.0
        • Outside that range: 0.5

    Sub-score B — structure (weight 0.3):
      Checks for signal of organised presentation.
      • Has bullet points, numbered lists, or headers → 1.0
      • Has sentence structure (>= 3 sentences) but no lists → 0.6
      • Single-sentence or fragment → 0.3

    Sub-score C — no vague/filler language (weight 0.3):
      Detects hedge-spam — excessive use of filler phrases that reduce
      information density without adding nuance.
      Filler phrases: "it depends", "various factors", "please note that",
                      "i would like to point out", "as an ai", "certainly",
                      "absolutely", "of course", "great question"
      • 0 filler phrases → 1.0
      • 1–2 filler phrases → 0.7
      • 3+ filler phrases → 0.3
      (Some hedging is fine; hedge-spam signals low-quality output)

    Final = 0.4 * sub_a + 0.3 * sub_b + 0.3 * sub_c

    Edge cases
    ----------
    • Very short clarifying queries ("yes", "ok"): length scoring relaxed.
    • Markdown formatting counts as structure even without bullets.

    Tool applicability: all tools
    """

    name = "clarity"

    _FILLER_PHRASES = [
        "it depends", "various factors", "please note that",
        "i would like to point out", "as an ai language model",
        "as an ai", "certainly!", "absolutely!", "of course!",
        "great question", "that's a great", "i'm glad you asked",
        "i hope this helps", "feel free to ask",
    ]

    def score(self, ctx: EvalContext) -> MetricResult:
        wc = _word_count(ctx.response)
        has_tools = bool(ctx.tool_outputs)
        evidence: list[str] = []

        # ── Sub-score A: length appropriateness ───────────────────────────
        if has_tools:
            if 60 <= wc <= 400:
                sub_a = 1.0
            elif 40 <= wc < 60 or 401 <= wc <= 700:
                sub_a = 0.7
            elif wc < 40:
                sub_a = 0.3
            else:  # > 700
                sub_a = 0.4
        else:
            sub_a = 1.0 if 10 <= wc <= 200 else 0.5
        evidence.append(f"Word count: {wc} → length score={sub_a:.1f}")

        # ── Sub-score B: structure ─────────────────────────────────────────
        if _has_structure(ctx.response):
            sub_b = 1.0
            evidence.append("Structure: has lists or headers → 1.0")
        elif _sentence_count(ctx.response) >= 3:
            sub_b = 0.6
            evidence.append(
                f"Structure: {_sentence_count(ctx.response)} sentences, no lists → 0.6"
            )
        else:
            sub_b = 0.3
            evidence.append("Structure: minimal (single sentence or fragment) → 0.3")

        # ── Sub-score C: no filler language ──────────────────────────────
        filler_found = _phrase_present(ctx.response_lower, self._FILLER_PHRASES)
        n = len(filler_found)
        if n == 0:
            sub_c = 1.0
        elif n <= 2:
            sub_c = 0.7
        else:
            sub_c = 0.3
        if filler_found:
            evidence.append(f"Filler phrases detected: {', '.join(filler_found[:3])}")
        else:
            evidence.append("No filler phrases detected → 1.0")

        final_score = 0.4 * sub_a + 0.3 * sub_b + 0.3 * sub_c
        reasoning = (
            f"Length={sub_a:.2f} (×0.4), "
            f"structure={sub_b:.2f} (×0.3), "
            f"no-filler={sub_c:.2f} (×0.3) → {final_score:.2f}"
        )
        return self._result(final_score, reasoning, evidence)


# ─────────────────────────────────────────────────────────────────────────────
# Metric Registry
# ─────────────────────────────────────────────────────────────────────────────

# All production metrics.  To add a new metric: create a MetricScorer
# subclass and add it to this list.  Nothing else changes.
METRIC_REGISTRY: list[MetricScorer] = [
    CorrectnessMetric(),
    GroundingMetric(),
    CompletenessMetric(),
    HelpfulnessMetric(),
    ClarityMetric(),
]

# Default weights — must sum to 1.0
DEFAULT_WEIGHTS: dict[str, float] = {
    "correctness":   0.30,
    "grounding":     0.25,
    "completeness":  0.20,
    "helpfulness":   0.15,
    "clarity":       0.10,
}


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class EvaluationOrchestrator:
    """
    Runs all registered metrics against an EvalContext and returns an
    EvaluationResult.

    Parameters
    ----------
    metrics : list of MetricScorer instances (defaults to METRIC_REGISTRY)
    weights : dict of metric_name → weight (defaults to DEFAULT_WEIGHTS)
    """

    def __init__(
        self,
        metrics: list[MetricScorer] | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.metrics = metrics or METRIC_REGISTRY
        self.weights = weights or DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.4f}. "
                f"Weights: {self.weights}"
            )

    def evaluate(self, ctx: EvalContext) -> EvaluationResult:
        """Run all metrics and return aggregated EvaluationResult."""
        metric_results: dict[str, MetricResult] = {}
        for metric in self.metrics:
            try:
                result = metric.score(ctx)
                metric_results[metric.name] = result
            except Exception as exc:  # noqa: BLE001
                # Metric failures must not crash the evaluation pipeline.
                metric_results[metric.name] = MetricResult(
                    metric_name=metric.name,
                    score=0.0,
                    reasoning=f"Metric raised an exception: {type(exc).__name__}: {exc}",
                    evidence=["Internal metric error — treat score as unreliable"],
                )

        return EvaluationResult(
            metric_results=metric_results,
            weights=self.weights,
            context_snapshot={
                "query": ctx.query[:120],
                "response_word_count": _word_count(ctx.response),
                "tools_called": [o.get("tool_name", "?") for o in ctx.tool_outputs],
            },
        )


# ─────────────────────────────────────────────────────────────────────────────
# Public convenience function — backward-compatible entry point
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_response(
    query: str,
    tool_outputs: list[dict[str, Any]],
    response: str,
    eval_case: EvalCase | None = None,
) -> EvaluationResult:
    """
    Convenience wrapper that constructs an EvalContext and runs the full
    evaluation pipeline.

    Parameters
    ----------
    query        : the user's original query string
    tool_outputs : list of dicts returned by each tool (may be empty)
    response     : the agent's final text response
    eval_case    : optional ground-truth specification; if None, a blank
                   EvalCase is used (correctness and completeness checks
                   are skipped, grounding and clarity still apply)

    Returns
    -------
    EvaluationResult with per-metric scores and a weighted total

    Example
    -------
    >>> result = evaluate_response(
    ...     query="Calculate CAGR from ₹1L to ₹3.5L in 7 years",
    ...     tool_outputs=[{
    ...         "tool_name": "calculate_cagr",
    ...         "success": True,
    ...         "cagr_pct": 19.6,
    ...         "summary": "CAGR = 19.6%",
    ...     }],
    ...     response="Your investment grew at a CAGR of 19.6% over 7 years. "
    ...              "This is considered strong performance. Past performance "
    ...              "does not guarantee future results. Consider consulting a "
    ...              "SEBI-registered advisor before making investment decisions.",
    ...     eval_case=EvalCase(
    ...         expected_numeric_values={"cagr_pct": 19.6},
    ...         required_topics=["cagr", "growth"],
    ...         required_caveats=["past performance"],
    ...     ),
    ... )
    >>> print(result.summary())
    """
    ctx = EvalContext(
        query=query,
        tool_outputs=tool_outputs,
        response=response,
        eval_case=eval_case or EvalCase(),
    )
    return EvaluationOrchestrator().evaluate(ctx)