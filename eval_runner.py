from langchain_core.messages import HumanMessage
from eval_cases import TEST_CASES
from agent_test import agent
from metrics import evaluate_response
import json
import time
passed = 0
failed = 0
external_errors = 0

tool_correct = 0
tool_total = 0

arg_correct = 0
arg_total = 0

latencies = []

for test in TEST_CASES[:1]:

    try:

        print(f"\nRunning: {test['name']}")

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
        print("\n====================")
        print("ALL CHUNKS")
        print("====================")

        for i, chunk in enumerate(all_chunks):
            print(f"\nChunk {i + 1}")
            print(chunk)
        end = time.time()

        latency = end - start
        latencies.append(latency)

        print(f"Latency: {latency:.2f} sec")
        tool_message = all_chunks[0]["model"]["messages"][0]

        tool_message = None
        tool_output = None
        final_message = None

        for chunk in all_chunks:

            # Tool execution result
            if "tools" in chunk:
                tool_output = chunk["tools"]["messages"][0]

            # AI messages
            elif "model" in chunk:

                message = chunk["model"]["messages"][0]

                # First AI message → tool call
                if message.tool_calls:
                    tool_message = message

                # Final AI message → natural language response
                else:
                    final_message = message

        if isinstance(final_message.content, list):
            final_response = final_message.content[0]["text"]
        else:
            final_response = final_message.content
        # Extract plain text from the final AI response
        if isinstance(final_message.content, list):
            final_response = ""

            for item in final_message.content:
                if item.get("type") == "text":
                    final_response += item.get("text", "")

        else:
            final_response = final_message.content
        response_score = evaluate_response(final_response)

        print("\nResponse Evaluation")
        print(response_score)
        print("\n========================")
        print("PARSED EXECUTION")
        print("========================")

        print("\nTool Call:")
        print(tool_message.tool_calls)

        print("\nTool Output:")
        print(tool_output.content)

        print("\nFinal Response:")
        print(final_response)
        # -------------------------------
        # Tool Selection Evaluation
        # -------------------------------

        actual_tools = []

        for tool_call in tool_message.tool_calls:
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

        if tool_message.tool_calls:
            actual_args = tool_message.tool_calls[0]["args"]

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

    if latencies:
        avg_latency = sum(latencies) / len(latencies)

        print(f"Average Latency: {avg_latency:.2f} sec")
        print(f"Fastest: {min(latencies):.2f} sec")
        print(f"Slowest: {max(latencies):.2f} sec")
    else:
        avg_latency = 0
        print("Latency metrics unavailable.")

    print(f"Average Latency: {avg_latency:.2f} sec")
    print(f"Fastest: {min(latencies):.2f} sec")
    print(f"Slowest: {max(latencies):.2f} sec")