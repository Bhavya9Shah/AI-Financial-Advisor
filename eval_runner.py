from langchain_core.messages import HumanMessage
from eval_cases import TEST_CASES
from agent_test import agent


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

    except Exception as e:

        print("FAIL")
        print(f"Error: {e}")