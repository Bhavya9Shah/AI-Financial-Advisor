from langchain_core.messages import HumanMessage
from eval_cases import TEST_CASES
from agent_test import agent
from metrics import evaluate_response, EvalCase

import json
import time

# ==========================================================
# Evaluation Statistics
# ==========================================================

passed = 0
failed = 0
external_errors = 0

tool_correct = 0
tool_total = 0

arg_correct = 0
arg_total = 0

latencies = []

response_scores = []

# ==========================================================
# Run Evaluation
# ==========================================================

for test in TEST_CASES[:1]:

    try:

        print("\n" + "=" * 70)
        print(f"Running Test : {test['name']}")
        print("=" * 70)

        agent_input = {
            "messages": [
                HumanMessage(content=test["query"])
            ]
        }

        start = time.time()

        all_chunks = []

        for chunk in agent.stream(
            agent_input,
            stream_mode="updates"
        ):
            all_chunks.append(chunk)

        end = time.time()

        latency = end - start
        latencies.append(latency)

        # =====================================================
        # Parse execution
        # =====================================================

        tool_message = None
        tool_output = None
        final_message = None

        for chunk in all_chunks:

            if "tools" in chunk:
                tool_output = chunk["tools"]["messages"][0]

            elif "model" in chunk:

                message = chunk["model"]["messages"][0]

                if message.tool_calls:
                    tool_message = message

                else:
                    final_message = message

        # =====================================================
        # Extract final response text
        # =====================================================

        if isinstance(final_message.content, list):

            final_response = ""

            for item in final_message.content:

                if item.get("type") == "text":
                    final_response += item.get("text", "")

        else:

            final_response = final_message.content

        # =====================================================
        # Tool Outputs
        # =====================================================

        tool_outputs = []

        if tool_output is not None:

            try:
                parsed_output = json.loads(tool_output.content)
            except Exception:
                parsed_output = {
                    "summary": tool_output.content
                }

            parsed_output["success"] = True
            parsed_output["tool_name"] = tool_output.name

            tool_outputs.append(parsed_output)
        print("\nParsed Tool Output:")
        print(tool_outputs)
        # =====================================================
        # EvalCase
        # =====================================================

        eval_case = EvalCase(

            expected_tools=test.get("expected_tools", []),

            expected_numeric_values=test.get(
                "expected_numeric_values", {}
            ),

            required_topics=test.get(
                "required_topics", []
            ),

            required_caveats=test.get(
                "required_caveats", []
            ),

            forbidden_claims=test.get(
                "forbidden_claims", []
            )

        )

        # =====================================================
        # Response Evaluation
        # =====================================================

        evaluation = evaluate_response(

            query=test["query"],

            tool_outputs=tool_outputs,

            response=final_response,

            eval_case=eval_case

        )

        response_scores.append(evaluation)

        # =====================================================
        # Pretty Print
        # =====================================================

        print("\nLatency")
        print("-" * 40)
        print(f"{latency:.2f} sec")

        print("\nTool Call")
        print("-" * 40)

        if tool_message:
            print(tool_message.tool_calls)

        print("\nTool Output")
        print("-" * 40)

        if tool_output:
            print(tool_output.content)

        print("\nFinal Response")
        print("-" * 40)
        print(final_response)

        print("\nResponse Evaluation")
        print("-" * 40)
        print(evaluation.summary())

        # =====================================================
        # Tool Selection Accuracy
        # =====================================================

        actual_tools = []

        if tool_message:

            for tool_call in tool_message.tool_calls:

                actual_tools.append(tool_call["name"])

        print("\nExpected Tools :", test["expected_tools"])
        print("Actual Tools   :", actual_tools)

        tool_total += 1

        if actual_tools == test["expected_tools"]:

            tool_correct += 1

        # =====================================================
        # Argument Accuracy
        # =====================================================

        actual_args = {}

        if tool_message and tool_message.tool_calls:

            actual_args = tool_message.tool_calls[0]["args"]

        print("\nExpected Args :", test.get("expected_args"))
        print("Actual Args   :", actual_args)

        if "expected_args" in test:

            arg_total += 1

            if actual_args == test["expected_args"]:

                arg_correct += 1

        print("\nPASS")

        passed += 1

    except Exception as e:

        error = str(e)

        if (
            "503" in error
            or
            "RESOURCE_EXHAUSTED" in error
        ):

            print("\nExternal Provider Error")
            print(error)

            external_errors += 1

        else:

            print("\nFAIL")
            print(error)

            failed += 1
        # ==========================================================
        # Evaluation Summary
        # ==========================================================

        print("\n" + "=" * 70)
        print("EVALUATION SUMMARY")
        print("=" * 70)

        print(f"Passed           : {passed}")
        print(f"Failed           : {failed}")
        print(f"External Errors  : {external_errors}")

        # ==========================================================
        # Tool Accuracy
        # ==========================================================

        if tool_total > 0:
            tool_accuracy = tool_correct / tool_total
        else:
            tool_accuracy = 0.0

        print(f"\nTool Selection Accuracy : {tool_accuracy:.2%}")

        # ==========================================================
        # Argument Accuracy
        # ==========================================================

        if arg_total > 0:
            argument_accuracy = arg_correct / arg_total
        else:
            argument_accuracy = 0.0

        print(f"Argument Accuracy       : {argument_accuracy:.2%}")

        # ==========================================================
        # Average Response Metrics
        # ==========================================================

        if response_scores:

            metric_names = [
                "correctness",
                "grounding",
                "completeness",
                "helpfulness",
                "clarity"
            ]

            metric_average = {}

            for metric in metric_names:

                total = 0

                for score in response_scores:
                    total += score.metric_results[metric].score

                metric_average[metric] = total / len(response_scores)

            weighted_total = (
                sum(score.weighted_total for score in response_scores)
                / len(response_scores)
            )

        else:

            metric_average = {
                "correctness": 0,
                "grounding": 0,
                "completeness": 0,
                "helpfulness": 0,
                "clarity": 0
            }

            weighted_total = 0

        print("\n" + "=" * 70)
        print("RESPONSE QUALITY")
        print("=" * 70)

        print(f"Correctness   : {metric_average['correctness']:.2f}")
        print(f"Grounding     : {metric_average['grounding']:.2f}")
        print(f"Completeness  : {metric_average['completeness']:.2f}")
        print(f"Helpfulness   : {metric_average['helpfulness']:.2f}")
        print(f"Clarity       : {metric_average['clarity']:.2f}")
        print(f"\nOverall Score : {weighted_total:.2f}")

        # ==========================================================
        # Latency
        # ==========================================================

        if latencies:

            avg_latency = sum(latencies) / len(latencies)

            fastest = min(latencies)

            slowest = max(latencies)

        else:

            avg_latency = 0

            fastest = 0

            slowest = 0

        print("\n" + "=" * 70)
        print("LATENCY")
        print("=" * 70)

        print(f"Average : {avg_latency:.2f} sec")
        print(f"Fastest : {fastest:.2f} sec")
        print(f"Slowest : {slowest:.2f} sec")

        # ==========================================================
        # Save Results
        # ==========================================================

        results = {

            "passed": passed,

            "failed": failed,

            "external_errors": external_errors,

            "tool_selection_accuracy": tool_accuracy,

            "argument_accuracy": argument_accuracy,

            "response_score": weighted_total,

            "correctness": metric_average["correctness"],

            "grounding": metric_average["grounding"],

            "completeness": metric_average["completeness"],

            "helpfulness": metric_average["helpfulness"],

            "clarity": metric_average["clarity"],

            "average_latency": avg_latency,

            "fastest_latency": fastest,

            "slowest_latency": slowest,

            "evaluation_completed": external_errors == 0
        }

        with open("results/latest.json", "w") as file:

            json.dump(results, file, indent=4)

        print("\nResults saved to results/latest.json")

        # ==========================================================
        # Baseline Comparison
        # ==========================================================

        if external_errors > 0:

            print("\nBaseline comparison skipped.")
            print("Reason: Evaluation incomplete due to provider errors.")

        else:

            try:

                with open("results/baseline.json", "r") as file:

                    baseline = json.load(file)

                print("\n" + "=" * 70)
                print("BASELINE COMPARISON")
                print("=" * 70)

                metrics_to_compare = [

                    ("tool_selection_accuracy", "Tool Accuracy"),

                    ("argument_accuracy", "Argument Accuracy"),

                    ("response_score", "Overall Response"),

                    ("correctness", "Correctness"),

                    ("grounding", "Grounding"),

                    ("completeness", "Completeness"),

                    ("helpfulness", "Helpfulness"),

                    ("clarity", "Clarity")

                ]

                for key, label in metrics_to_compare:

                    if key not in baseline:
                        continue

                    current = results[key]

                    previous = baseline[key]

                    print(f"\n{label}")

                    print(f"Baseline : {previous:.2f}")

                    print(f"Current  : {current:.2f}")

                    if current > previous:

                        print("Status   : IMPROVED")

                    elif current < previous:

                        print("Status   : REGRESSION")

                    else:

                        print("Status   : SAME")

            except FileNotFoundError:

                print("\nNo baseline.json found.")

                print("Create one after a successful evaluation.")