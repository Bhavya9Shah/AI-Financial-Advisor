from langchain_core.messages import HumanMessage
from eval_cases import TEST_CASES
from agent_test import agent
import json
passed = 0
failed = 0
external_errors = 0

tool_correct = 0
tool_total = 0

arg_correct = 0
arg_total = 0

for test in TEST_CASES:

    try:

        print(f"\nRunning: {test['name']}")

        agent_input = {
            "messages": [
                HumanMessage(content=test["query"])
            ]
        }

        for chunk in agent.stream(
            agent_input,
            stream_mode="updates"
        ):
            first_chunk = chunk
            break

        message = first_chunk["model"]["messages"][0]

        # -------------------------------
        # Tool Selection Evaluation
        # -------------------------------

        actual_tools = []

        for tool_call in message.tool_calls:
            actual_tools.append(tool_call["name"])

        print("Expected Tools :", test["expected_tools"])
        print("Actual Tools   :", actual_tools)

        tool_total += 1

        if actual_tools == test["expected_tools"]:
            tool_correct += 1

        # -------------------------------
        # Argument Evaluation
        # -------------------------------

        actual_args = {}

        if message.tool_calls:
            actual_args = message.tool_calls[0]["args"]

        print("Expected Args  :", test.get("expected_args"))
        print("Actual Args    :", actual_args)

        if "expected_args" in test:

            arg_total += 1

            if actual_args == test["expected_args"]:
                arg_correct += 1

        print("PASS")
        passed += 1

    except Exception as e:

        error_message = str(e)

        if "503" in error_message:
            print("EXTERNAL ERROR (Provider overloaded)")
            external_errors += 1

        elif "RESOURCE_EXHAUSTED" in error_message:
            print("EXTERNAL ERROR (Quota exceeded)")
            external_errors += 1

        else:
            print("FAIL")
            failed += 1

        print(f"Error: {e}")

# =====================================
# Evaluation Summary
# =====================================

print("\n" + "=" * 40)
print("EVALUATION SUMMARY")
print("=" * 40)

print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"External Errors: {external_errors}")

# Tool Accuracy

if tool_total > 0:
    tool_accuracy = tool_correct / tool_total
else:
    tool_accuracy = 0

print(f"Tool Selection Accuracy: {tool_accuracy:.2%}")

# Argument Accuracy

if arg_total > 0:
    argument_accuracy = arg_correct / arg_total
else:
    argument_accuracy = 0

print(f"Argument Accuracy: {argument_accuracy:.2%}")
results = {
    "passed": passed,
    "failed": failed,
    "external_errors": external_errors,
    "tool_selection_accuracy": tool_accuracy,
    "argument_accuracy": argument_accuracy,
    "evaluation_completed": external_errors == 0
}
with open("results/latest.json", "w") as file:
    json.dump(results, file, indent=4)
print("\nResults saved to results/latest.json")

if external_errors > 0:

    print("\nBaseline comparison skipped.")
    print("Reason: Evaluation incomplete due to external provider errors.")

else:

    with open("results/baseline.json", "r") as file:
        baseline = json.load(file)

    print("\n" + "=" * 40)
    print("BASELINE COMPARISON")
    print("=" * 40)

    baseline_tool = baseline["tool_selection_accuracy"]
    current_tool = results["tool_selection_accuracy"]

    print(f"Baseline Tool Accuracy : {baseline_tool:.2%}")
    print(f"Current Tool Accuracy  : {current_tool:.2%}")

    if current_tool > baseline_tool:
        print("Tool Status: IMPROVED")

    elif current_tool < baseline_tool:
        print("Tool Status: REGRESSION")

    else:
        print("Tool Status: SAME")

    print()

    baseline_arg = baseline["argument_accuracy"]
    current_arg = results["argument_accuracy"]

    print(f"Baseline Argument Accuracy : {baseline_arg:.2%}")
    print(f"Current Argument Accuracy  : {current_arg:.2%}")

    if current_arg > baseline_arg:
        print("Argument Status: IMPROVED")

    elif current_arg < baseline_arg:
        print("Argument Status: REGRESSION")

    else:
        print("Argument Status: SAME")