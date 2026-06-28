"""
test_metrics.py — Unit test suite for FinSight evaluation engine
================================================================
Every test is deterministic: no LLM calls, no network, no file I/O.
Run with: pytest test_metrics.py -v

Design principle: test the scoring *logic*, not the scoring *output*.
Each test encodes a specific rule from the metric's docstring and verifies
that the rule produces the expected score.  If a rule changes, the test
that encodes it will fail — that is the intended behaviour.
"""

import pytest
from metrics import (
    EvalCase,
    EvalContext,
    EvaluationOrchestrator,
    CorrectnessMetric,
    GroundingMetric,
    CompletenessMetric,
    HelpfulnessMetric,
    ClarityMetric,
    evaluate_response,
    DEFAULT_WEIGHTS,
    _relative_error,
    _best_relative_error,
    _phrase_present,
    _word_count,
    _has_structure,
    _extract_numbers_from_dict,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper factories
# ─────────────────────────────────────────────────────────────────────────────

def make_ctx(
    query="Test query",
    tool_outputs=None,
    response="Test response",
    eval_case=None,
) -> EvalContext:
    return EvalContext(
        query=query,
        tool_outputs=tool_outputs or [],
        response=response,
        eval_case=eval_case or EvalCase(),
    )


def sip_tool_output(future_value=1161695.0, total_invested=600000.0) -> dict:
    return {
        "tool_name": "calculate_sip_returns",
        "success": True,
        "future_value": future_value,
        "total_invested": total_invested,
        "cagr_pct": 12.0,
        "summary": (
            f"Investing 5000/month for 10 years at 12% annual return: "
            f"Projected corpus = {future_value:,.0f}"
        ),
    }


def stock_tool_output(price=3400.5) -> dict:
    return {
        "tool_name": "get_stock_info",
        "success": True,
        "current_price": price,
        "week_52_high": 3800.0,
        "week_52_low": 2600.0,
        "pe_ratio": 28.5,
        "sector": "Technology",
        "analyst_summary": (
            f"Infosys is currently trading at INR {price}, "
            "which is 10.5% below its 52-week high."
        ),
    }


def failed_tool_output(tool_name="get_stock_info") -> dict:
    return {
        "tool_name": tool_name,
        "success": False,
        "error": "API timeout after 5 seconds",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helper tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPrivateHelpers:

    def test_relative_error_exact(self):
        assert _relative_error(100.0, 100.0) == 0.0

    def test_relative_error_ten_percent(self):
        assert abs(_relative_error(110.0, 100.0) - 0.10) < 1e-9

    def test_relative_error_zero_expected(self):
        assert _relative_error(0.0, 0.0) == 0.0
        assert _relative_error(5.0, 0.0) == 1.0

    def test_best_relative_error_perfect_match(self):
        assert _best_relative_error([100.0, 200.0, 300.0], 200.0) == 0.0

    def test_best_relative_error_empty_list(self):
        assert _best_relative_error([], 100.0) == 1.0

    def test_phrase_present_found(self):
        result = _phrase_present("consider investing in index funds", ["consider", "missing"])
        assert result == ["consider"]

    def test_phrase_present_case_insensitive(self):
        result = _phrase_present("Past Performance Does Not Guarantee", ["past performance"])
        assert "past performance" in result

    def test_word_count(self):
        assert _word_count("hello world this is a test") == 6
        assert _word_count("") == 0

    def test_has_structure_bullets(self):
        assert _has_structure("Some text\n- bullet one\n- bullet two")

    def test_has_structure_numbered(self):
        assert _has_structure("Steps:\n1. First\n2. Second")

    def test_has_structure_none(self):
        assert not _has_structure("This is a plain paragraph with no lists.")

    def test_extract_numbers_from_dict_nested(self):
        d = {"a": 1.0, "b": {"c": 2.5, "d": [3.0, 4.0]}, "text": "ignored"}
        numbers = _extract_numbers_from_dict(d)
        assert set(numbers) == {1.0, 2.5, 3.0, 4.0}

    def test_extract_numbers_excludes_booleans(self):
        # True/False should not appear as 1.0/0.0
        numbers = _extract_numbers_from_dict({"flag": True, "val": 42.0})
        assert 42.0 in numbers
        assert 1.0 not in numbers


# ─────────────────────────────────────────────────────────────────────────────
# EvalContext derived properties
# ─────────────────────────────────────────────────────────────────────────────

class TestEvalContext:

    def test_response_numbers_extracts_integers(self):
        ctx = make_ctx(response="The value is 1161695 and rate is 12.")
        assert 1161695.0 in ctx.response_numbers
        assert 12.0 in ctx.response_numbers

    def test_response_numbers_extracts_decimals(self):
        ctx = make_ctx(response="CAGR is 19.6% over 7 years.")
        assert 19.6 in ctx.response_numbers
        assert 7.0 in ctx.response_numbers

    def test_response_numbers_ignores_commas_in_numbers(self):
        ctx = make_ctx(response="Corpus = 11,61,695")
        # After comma removal, should find 1161695
        assert any(abs(n - 1161695) < 1 for n in ctx.response_numbers)

    def test_tool_output_numbers_from_nested_dict(self):
        ctx = make_ctx(tool_outputs=[sip_tool_output()])
        nums = ctx.tool_output_numbers
        assert 1161695.0 in nums
        assert 600000.0 in nums

    def test_successful_tool_outputs_filters(self):
        ctx = make_ctx(tool_outputs=[
            sip_tool_output(),
            failed_tool_output(),
        ])
        assert len(ctx.successful_tool_outputs) == 1


# ─────────────────────────────────────────────────────────────────────────────
# CorrectnessMetric
# ─────────────────────────────────────────────────────────────────────────────

class TestCorrectnessMetric:

    metric = CorrectnessMetric()

    def test_no_expected_values_returns_full_score(self):
        ctx = make_ctx(response="Some response", eval_case=EvalCase())
        result = self.metric.score(ctx)
        assert result.score == 1.0

    def test_exact_match_returns_full_score(self):
        ctx = make_ctx(
            response="Your CAGR is 19.6 percent.",
            eval_case=EvalCase(expected_numeric_values={"cagr_pct": 19.6}),
        )
        result = self.metric.score(ctx)
        assert result.score == 1.0

    def test_approximate_match_within_tolerance(self):
        # 19.7 vs 19.6: error = 0.51% < 1% tolerance → full credit
        ctx = make_ctx(
            response="Your CAGR is approximately 19.7 percent.",
            eval_case=EvalCase(
                expected_numeric_values={"cagr_pct": 19.6},
                numeric_tolerance_pct=1.0,
            ),
        )
        result = self.metric.score(ctx)
        assert result.score == 1.0

    def test_approximate_match_partial_credit(self):
        # 19.7 vs 19.6: error = 0.51% > 1% tolerance? No, 0.51% < 1%.
        # Need error between 1% and 3%: try 20.1 vs 19.6 → error = 2.55%
        ctx = make_ctx(
            response="Roughly 20.1 percent growth.",
            eval_case=EvalCase(
                expected_numeric_values={"cagr_pct": 19.6},
                numeric_tolerance_pct=1.0,
            ),
        )
        result = self.metric.score(ctx)
        assert result.score == 0.5

    def test_wrong_number_returns_zero(self):
        ctx = make_ctx(
            response="Your CAGR is 5.0 percent.",
            eval_case=EvalCase(expected_numeric_values={"cagr_pct": 19.6}),
        )
        result = self.metric.score(ctx)
        assert result.score == 0.0

    def test_multiple_values_partial_match(self):
        # One value correct (19.6), one wrong (500000 vs 1161695)
        ctx = make_ctx(
            response="CAGR = 19.6%, future value = 500000",
            eval_case=EvalCase(
                expected_numeric_values={"cagr": 19.6, "fv": 1161695.0}
            ),
        )
        result = self.metric.score(ctx)
        # 1/2 exact + 0/2 → 0.5
        assert 0.4 < result.score < 0.6

    def test_all_tools_failed_returns_zero(self):
        ctx = make_ctx(
            tool_outputs=[failed_tool_output()],
            response="The stock price is 3400.",
            eval_case=EvalCase(expected_numeric_values={"price": 3400.0}),
        )
        result = self.metric.score(ctx)
        assert result.score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# GroundingMetric
# ─────────────────────────────────────────────────────────────────────────────

class TestGroundingMetric:

    metric = GroundingMetric()

    def test_no_tools_no_numbers_fully_grounded(self):
        ctx = make_ctx(response="Diversification reduces portfolio risk.")
        result = self.metric.score(ctx)
        assert result.score == 1.0

    def test_response_uses_tool_numbers(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output(future_value=1161695.0)],
            response=(
                "Based on the calculation, your SIP will grow to ₹11,61,695 "
                "over 10 years. Past performance does not guarantee results."
            ),
        )
        result = self.metric.score(ctx)
        # Response is grounded — should at minimum pass the threshold
        assert result.score >= 0.5

    def test_hallucinated_numbers_after_tool_call(self):
        # Tool returns 1161695 but response cites 9999999 (not in tool output)
        ctx = make_ctx(
            tool_outputs=[sip_tool_output(future_value=1161695.0)],
            response="Your SIP will definitely reach ₹99,99,999.",
        )
        result = self.metric.score(ctx)
        assert result.score < 0.5

    def test_failed_tool_honest_acknowledgement(self):
        ctx = make_ctx(
            tool_outputs=[failed_tool_output()],
            response="I was unable to fetch the stock data due to a timeout. Please try again.",
        )
        result = self.metric.score(ctx)
        assert result.score == 1.0

    def test_failed_tool_with_hallucinated_data(self):
        ctx = make_ctx(
            tool_outputs=[failed_tool_output()],
            response="The stock is currently trading at ₹3,400.",
        )
        result = self.metric.score(ctx)
        assert result.score == 0.0

    def test_summary_echoed_increases_score(self):
        out = stock_tool_output(price=3400.5)
        ctx = make_ctx(
            tool_outputs=[out],
            response=(
                "Infosys is currently trading at INR 3400.5, "
                "which is below its 52-week high. Consider reviewing your position."
            ),
        )
        result = self.metric.score(ctx)
        assert result.score >= 0.7


# ─────────────────────────────────────────────────────────────────────────────
# CompletenessMetric
# ─────────────────────────────────────────────────────────────────────────────

class TestCompletenessMetric:

    metric = CompletenessMetric()

    def test_all_topics_covered(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response=(
                "Your SIP of ₹5,000/month compounded monthly at 12% annual return "
                "will generate a corpus of ₹11.6 lakh over 10 years. "
                "The power of compounding means each rupee you invest today earns "
                "returns that themselves earn returns, exponentially growing your wealth. "
                "Starting early maximises the investment horizon and makes a significant "
                "difference to your final corpus. A 10-year SIP benefits greatly from "
                "this compounding effect compared to a lump-sum investment."
            ),
            eval_case=EvalCase(required_topics=["sip", "compounding", "corpus"]),
        )
        result = self.metric.score(ctx)
        assert result.score > 0.85

    def test_missing_topics_reduce_score(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response="Your investment will grow over time.",
            eval_case=EvalCase(
                required_topics=["sip", "compounding", "corpus", "monthly"]
            ),
        )
        result = self.metric.score(ctx)
        assert result.score < 0.5

    def test_no_required_topics_uses_length(self):
        long_response = " ".join(["word"] * 100)
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response=long_response,
            eval_case=EvalCase(),
        )
        result = self.metric.score(ctx)
        assert result.score > 0.8

    def test_very_short_response_with_tools_penalised(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response="Your SIP will grow.",
            eval_case=EvalCase(
                required_topics=["sip", "corpus", "compounding", "returns", "monthly"]
            ),
        )
        result = self.metric.score(ctx)
        # Short + missing required topics = low score
        assert result.score < 0.6

    def test_no_tools_short_response_not_penalised(self):
        ctx = make_ctx(
            tool_outputs=[],
            response="Hello! How can I help you today?",
        )
        result = self.metric.score(ctx)
        # sub_b should be 1.0 (no tools, length not evaluated strictly)
        assert result.score >= 1.0 * 0.7  # at least full topic credit


# ─────────────────────────────────────────────────────────────────────────────
# HelpfulnessMetric
# ─────────────────────────────────────────────────────────────────────────────

class TestHelpfulnessMetric:

    metric = HelpfulnessMetric()

    def test_actionable_with_caveat_full_score(self):
        ctx = make_ctx(
            response=(
                "I recommend starting a SIP of ₹5,000/month in a Nifty 50 index fund. "
                "You should also consider building an emergency fund first. "
                "Past performance does not guarantee future returns. "
                "Please consult a SEBI-registered advisor before investing."
            ),
        )
        result = self.metric.score(ctx)
        assert result.score > 0.8

    def test_no_caveat_hard_zero_on_sub_b(self):
        ctx = make_ctx(
            response=(
                "You should definitely invest ₹10,000/month in this fund. "
                "It will grow significantly."
            ),
        )
        result = self.metric.score(ctx)
        # sub_b = 0.0 (no caveat): max possible = 0.5*1 + 0.3*0 + 0.2*1 = 0.7
        # A response WITH a caveat would score higher than this
        assert result.score <= 0.7

    def test_forbidden_claim_hard_caps_score(self):
        ctx = make_ctx(
            response=(
                "This investment offers guaranteed returns of 15% annually. "
                "You will definitely make money. Consider investing now. "
                "Past performance does not guarantee future results."
            ),
        )
        result = self.metric.score(ctx)
        assert result.score <= 0.4

    def test_forbidden_claim_detected_correctly(self):
        ctx = make_ctx(
            response="This is a 100% safe investment with guaranteed returns.",
        )
        result = self.metric.score(ctx)
        assert result.score <= 0.4
        assert any("forbidden" in e.lower() or "FORBIDDEN" in e for e in result.evidence)

    def test_custom_forbidden_claims_from_eval_case(self):
        ctx = make_ctx(
            response="This stock will moon to the moon!",
            eval_case=EvalCase(forbidden_claims=["will moon"]),
        )
        result = self.metric.score(ctx)
        assert result.score <= 0.4

    def test_custom_required_caveats_from_eval_case(self):
        ctx = make_ctx(
            response=(
                "You should consider index funds. "
                "This is only an educational overview."
            ),
            eval_case=EvalCase(required_caveats=["educational"]),
        )
        result = self.metric.score(ctx)
        # "educational" is present → caveat found
        assert result.score > 0.5


# ─────────────────────────────────────────────────────────────────────────────
# ClarityMetric
# ─────────────────────────────────────────────────────────────────────────────

class TestClarityMetric:

    metric = ClarityMetric()

    def test_structured_appropriate_length_no_filler(self):
        response = (
            "Here is your SIP analysis:\n"
            "- Monthly investment: ₹5,000\n"
            "- Annual rate: 12%\n"
            "- Duration: 10 years\n"
            "- Projected corpus: ₹11.6 lakh\n\n"
            "The compounding effect significantly amplifies your returns over time. "
            "Starting early is the most effective strategy for wealth creation. "
            "Please consult a financial advisor before making decisions."
        )
        ctx = make_ctx(tool_outputs=[sip_tool_output()], response=response)
        result = self.metric.score(ctx)
        assert result.score > 0.85

    def test_filler_phrases_reduce_score(self):
        response = (
            "Great question! As an AI, I would like to point out that "
            "certainly, of course, your investment performance depends on "
            "various factors. It depends on market conditions. "
            "I hope this helps you understand better. Feel free to ask more. "
            "The returns might be around 12% or so depending on conditions."
        )
        ctx = make_ctx(response=response)
        result = self.metric.score(ctx)
        assert result.score < 0.7

    def test_too_long_response_penalised(self):
        # 4 words per phrase × 180 repetitions = ~720 words
        very_long = " ".join(["word one two three"] * 180)
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response=very_long,
        )
        result = self.metric.score(ctx)
        # Length > 700 → sub_a = 0.4, which pulls total score down
        assert result.score < 0.85

    def test_very_short_response_with_tools_penalised(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response="It will grow.",
        )
        result = self.metric.score(ctx)
        assert result.score < 0.6

    def test_no_tools_short_response_not_penalised(self):
        ctx = make_ctx(
            tool_outputs=[],
            response="Hello! I'm FinSight. How can I help you today?",
        )
        result = self.metric.score(ctx)
        # sub_a should be 1.0 (no tools, no strict length requirement)
        assert result.score > 0.6


# ─────────────────────────────────────────────────────────────────────────────
# EvaluationOrchestrator
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluationOrchestrator:

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError, match="sum to 1.0"):
            EvaluationOrchestrator(weights={"correctness": 0.5, "grounding": 0.3})

    def test_all_metrics_run(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response=(
                "Your SIP of ₹5,000/month at 12% for 10 years will grow to "
                "₹11,61,695. Consider this a strong long-term strategy. "
                "Past performance does not guarantee future returns."
            ),
            eval_case=EvalCase(
                expected_numeric_values={"future_value": 1161695.0},
                required_topics=["sip"],
            ),
        )
        result = EvaluationOrchestrator().evaluate(ctx)
        assert set(result.metric_results.keys()) == {
            "correctness", "grounding", "completeness", "helpfulness", "clarity"
        }

    def test_weighted_total_in_range(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response="Your SIP will reach ₹11,61,695. Past performance is no guarantee.",
        )
        result = EvaluationOrchestrator().evaluate(ctx)
        assert 0.0 <= result.weighted_total <= 1.0

    def test_metric_exception_does_not_crash_orchestrator(self):
        """A buggy metric must not crash the entire evaluation run."""
        class BrokenMetric(ClarityMetric):
            name = "clarity"
            def score(self, ctx):
                raise RuntimeError("Simulated internal metric failure")

        orchestrator = EvaluationOrchestrator(
            metrics=[BrokenMetric()],
            weights={"clarity": 1.0},
        )
        ctx = make_ctx(response="Some response")
        result = orchestrator.evaluate(ctx)
        assert result.metric_results["clarity"].score == 0.0
        assert "exception" in result.metric_results["clarity"].reasoning.lower()

    def test_summary_output_contains_all_metrics(self):
        ctx = make_ctx(
            tool_outputs=[sip_tool_output()],
            response=(
                "Your SIP projection: ₹11,61,695. "
                "Consider starting early. Past performance does not guarantee returns."
            ),
        )
        result = EvaluationOrchestrator().evaluate(ctx)
        summary = result.summary()
        for name in ["correctness", "grounding", "completeness", "helpfulness", "clarity"]:
            assert name in summary

    def test_to_dict_structure(self):
        ctx = make_ctx(response="Simple response.")
        result = EvaluationOrchestrator().evaluate(ctx)
        d = result.to_dict()
        assert "weighted_total" in d
        assert "passed" in d
        assert "metrics" in d
        for name in ["correctness", "grounding", "completeness", "helpfulness", "clarity"]:
            assert name in d["metrics"]
            assert "score" in d["metrics"][name]
            assert "label" in d["metrics"][name]


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluateResponse:

    def test_minimal_call_no_eval_case(self):
        result = evaluate_response(
            query="What is a SIP?",
            tool_outputs=[],
            response="A SIP is a Systematic Investment Plan allowing monthly investments.",
        )
        assert result.weighted_total >= 0.0

    def test_full_call_cagr_scenario(self):
        result = evaluate_response(
            query="Calculate CAGR from ₹1L to ₹3.5L in 7 years",
            tool_outputs=[{
                "tool_name": "calculate_cagr",
                "success": True,
                "cagr_pct": 19.6,
                "summary": "CAGR ≈ 19.6% — strong growth",
            }],
            response=(
                "Your investment of ₹1,00,000 grew to ₹3,50,000 over 7 years, "
                "representing a CAGR of 19.6%. This is strong performance, "
                "above the Nifty 50 historical average of 12–14%. "
                "Past performance does not guarantee future returns. "
                "Consider consulting a SEBI-registered advisor before investing."
            ),
            eval_case=EvalCase(
                expected_numeric_values={"cagr_pct": 19.6},
                required_topics=["cagr", "growth"],
                required_caveats=["past performance"],
            ),
        )
        assert result.weighted_total > 0.7
        assert result.metric_results["correctness"].score == 1.0

    def test_stock_query_with_profile_query(self):
        """get_user_profile output should be accepted as a grounding source."""
        result = evaluate_response(
            query="What is my risk profile?",
            tool_outputs=[{
                "tool_name": "get_user_profile",
                "success": True,
                "risk_tolerance": "moderate",
                "age": 27,
                "monthly_income": 90000,
                "summary": "User profile: age=27, risk=moderate, income=90000",
            }],
            response=(
                "Based on your profile, your risk tolerance is moderate. "
                "At 27, with a monthly income of ₹90,000, you are well-positioned "
                "to consider a balanced portfolio. Consider index funds and hybrid "
                "funds for your investment horizon. "
                "This is educational guidance — please consult a professional."
            ),
        )
        assert result.weighted_total > 0.6


# ─────────────────────────────────────────────────────────────────────────────
# Edge case battery — determinism and boundary conditions
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_response_does_not_crash(self):
        result = evaluate_response("Query", [], "")
        assert result.weighted_total >= 0.0

    def test_unicode_response_does_not_crash(self):
        result = evaluate_response(
            "Query",
            [],
            "आपका निवेश ₹11,61,695 तक बढ़ेगा। Past performance does not guarantee returns.",
        )
        assert result.weighted_total >= 0.0

    def test_response_with_only_numbers(self):
        result = evaluate_response("What is 2+2?", [], "4")
        assert result.weighted_total >= 0.0

    def test_same_inputs_always_same_output(self):
        """Determinism check: identical inputs must produce identical scores."""
        kwargs = dict(
            query="Calculate SIP returns",
            tool_outputs=[sip_tool_output()],
            response=(
                "Your SIP will reach ₹11,61,695. "
                "Consider this a long-term strategy. "
                "Past performance is not a guarantee."
            ),
            eval_case=EvalCase(
                expected_numeric_values={"future_value": 1161695.0},
                required_topics=["sip"],
            ),
        )
        result_1 = evaluate_response(**kwargs)
        result_2 = evaluate_response(**kwargs)
        assert result_1.weighted_total == result_2.weighted_total
        for name in result_1.metric_results:
            assert result_1.metric_results[name].score == result_2.metric_results[name].score

    def test_news_tool_output_grounding(self):
        """get_financial_news should be accepted as grounding source."""
        result = evaluate_response(
            query="Any news about Infosys?",
            tool_outputs=[{
                "tool_name": "get_financial_news",
                "success": True,
                "headlines": ["Infosys Q3 results beat estimates"],
                "sentiment": "positive",
                "summary": "Infosys Q3 results beat estimates — positive sentiment",
            }],
            response=(
                "Recent news on Infosys shows positive sentiment. "
                "Q3 results beat market estimates, which could support the stock price. "
                "Consider reviewing your position. "
                "News sentiment does not guarantee price movement — please consult an advisor."
            ),
        )
        assert result.weighted_total > 0.5