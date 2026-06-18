from langchain_core.messages import HumanMessage
from eval_cases import TEST_CASES
from agent_test import agent

passed = 0
failed = 0
external_errors = 0

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
            print(chunk)
            break

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

print("\n" + "="*40)
print("EVALUATION SUMMARY")
print("="*40)

print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"External Errors: {external_errors}")