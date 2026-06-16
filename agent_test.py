"""
agent_test.py — Financial Agent Test Harness
=============================================
Uses the CURRENT (non-deprecated) LangChain 1.3.1 / LangGraph 1.x API.

Key API facts verified against installed packages:
  - langchain      1.3.1   → use langchain.agents.create_agent  (NOT create_react_agent)
  - langgraph      1.2.4   → create_react_agent is DEPRECATED here; create_agent is the successor
  - langchain_core 1.4.1
  - langchain_google_genai 4.2.4

Run:
    python agent_test.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Standard library imports
# ─────────────────────────────────────────────────────────────────────────────

import os          # Reading environment variables (API keys)
import json        # Pretty-printing dict outputs in the trace

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Third-party imports (LangChain ecosystem)
# ─────────────────────────────────────────────────────────────────────────────

from dotenv import load_dotenv
# python-dotenv reads a .env file and puts its contents into os.environ.
# This is the standard way to handle API keys — never hardcode them.

from langchain.agents import create_agent
# THIS IS THE CORRECT IMPORT FOR LANGCHAIN 1.3.1.
# Do NOT use: from langgraph.prebuilt import create_react_agent
#   → That is deprecated as of LangGraph v1.
# create_agent is the new canonical agent factory. It:
#   1. Takes a model + tools + system prompt
#   2. Compiles a LangGraph StateGraph internally
#   3. Returns a runnable graph that loops: model → tools → model → ... → answer

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
# These are the three message types that flow through the agent loop:
#   HumanMessage → what the user said
#   AIMessage    → what the LLM said (may include tool_calls)
#   ToolMessage  → the result returned by a tool after execution
# Understanding these three types IS understanding how agents work.

from langchain_google_genai import ChatGoogleGenerativeAI
# The LangChain-native wrapper for Google's Gemini models.
# Under the hood it handles: auth, request formatting, retries, streaming.
# It conforms to the BaseChatModel interface, so create_agent treats it
# identically to GPT-4o or Claude — that's the power of LangChain's abstraction.

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Your tools (built in the previous exercise)
# ─────────────────────────────────────────────────────────────────────────────

from tools import FINANCIAL_TOOLS
# FINANCIAL_TOOLS is the list defined at the bottom of tools.py:
#   FINANCIAL_TOOLS = [get_stock_info, calculate_sip_returns, calculate_cagr]
# create_agent will inspect each tool's name + docstring to decide
# when and how to call them. This is why good docstrings matter so much.

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Environment setup
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()
# Reads your .env file (must be in the same folder as this script).
# Your .env should contain exactly one line:
#   GOOGLE_API_KEY=AIza...your_key_here

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# os.getenv returns None if the key is missing — we check for that below.

if not GOOGLE_API_KEY:
    # Fail early with a clear message rather than getting a cryptic auth error
    # three steps later inside the agent loop.
    raise EnvironmentError(
        "GOOGLE_API_KEY not found. "
        "Create a .env file in this folder with: GOOGLE_API_KEY=your_key_here\n"
        "Get a free key at: https://aistudio.google.com"
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — The LLM (the "brain" of the agent)
# ─────────────────────────────────────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    # gemini-2.0-flash: fast, free-tier friendly, strong at tool-calling.
    # You can also try "gemini-1.5-pro" for deeper reasoning.

    google_api_key=GOOGLE_API_KEY,
    # Explicit key passing — more robust than relying on env detection.

    temperature=0.1,
    # Scale: 0.0 (deterministic/focused) → 1.0 (creative/random).
    # For financial advice, low temperature = more consistent, factual answers.
    # Never use 0.0 exactly — some models require a tiny amount of stochasticity.
)
# At this point, `llm` is just a configured object. No API call has been made yet.
# The LLM itself has NO awareness of your tools yet — that comes in create_agent.

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — The system prompt (the agent's "identity and instructions")
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are FinSight, an expert AI financial advisor focused on the Indian market.

Your role:

* Help users make informed financial decisions using data, calculations, and reasoning
* Always think step by step before giving a recommendation
* Use your tools to fetch real data rather than relying on memory for prices or figures
* Be transparent about uncertainty — financial markets are unpredictable
* Always add a disclaimer that your advice is educational, not certified financial advice

How to use your tools:

* get_stock_info: Use when the user asks about a specific stock's price, valuation, or market position
* calculate_sip_returns: Use when the user asks about monthly investment projections or mutual fund SIPs
* calculate_cagr: Use when comparing growth rates or evaluating historical investment performance
* get_user_profile: Use before giving personalised financial advice
* update_user_profile: Use whenever the user reveals new personal financial information

Profile Instructions:

* ALWAYS call get_user_profile() before giving personalised financial advice
* Use the user's profile to personalise every recommendation
* If the user reveals information about themselves (income, age, expenses, goals, investments, loans, risk tolerance, etc.), immediately call update_user_profile()
* Do not announce profile updates to the user; update silently and continue the conversation naturally
* If profile_complete is False, ask for the most important missing information before giving detailed advice
* Prioritise asking for:

  1. age
  2. monthly_income
  3. risk_tolerance
* Do not ask for all missing fields at once

Risk Tolerance Guidelines:

* conservative:

  * fixed deposits
  * debt funds
  * low-volatility investments
  * capital preservation

* moderate:

  * index funds
  * balanced funds
  * diversified portfolios

* aggressive:

  * direct equity
  * mid-cap funds
  * small-cap funds
  * higher growth opportunities

Investment Horizon Guidelines:

* Less than 3 years:

  * avoid high equity exposure
  * focus on capital preservation

* Between 3 and 7 years:

  * balanced allocation is appropriate

* More than 7 years:

  * equity-heavy allocation can be considered

Reasoning style:

* Show your work
* Explain WHY you're calling a tool before calling it
* After getting tool results, explain what the numbers mean in plain English
* When making a recommendation, name the trade-offs explicitly
* Personalise recommendations using profile information whenever available

Constraints:

* Never recommend specific stocks as guaranteed investments
* Always mention that past returns do not guarantee future performance
* If a calculation seems off, say so rather than presenting wrong numbers confidently
* Educational use only; not certified financial advice
  """

# The system prompt is your most powerful lever for reasoning quality.
# It defines: persona, tool usage strategy, reasoning style, and guardrails.
# This directly affects 35% of your hackathon score (Reasoning Quality).
#
# Key design decisions here:
#   1. Named the agent "FinSight" — gives it a persona
#   2. Explicit tool usage instructions — the LLM reads this to decide when to call tools
#   3. "Think step by step" — classic chain-of-thought prompt engineering
#   4. Constraints section — financial agents MUST have guardrails

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — Creating the agent
# ─────────────────────────────────────────────────────────────────────────────

agent = create_agent(
    model=llm,
    # The brain. create_agent will call llm.bind_tools(FINANCIAL_TOOLS)
    # internally — this is what gives the LLM "knowledge" of the tools.

    tools=FINANCIAL_TOOLS,
    # The hands. create_agent registers these so the LLM can invoke them.
    # Each tool's name + docstring gets embedded in the LLM's context.

    system_prompt=SYSTEM_PROMPT,
    # The personality and rules. Prepended to every conversation as a
    # SystemMessage before the user's first message.
)
# What create_agent actually builds (simplified):
#
#   ┌─────────────────────────────────────────────────────┐
#   │                  StateGraph (compiled)               │
#   │                                                      │
#   │  START → [model node] ──has tool_calls?──► [tools node]
#   │                ▲                                  │
#   │                └──────────────────────────────────┘
#   │          [model node] ──no tool_calls?──► END
#   └─────────────────────────────────────────────────────┘
#
# This IS the ReAct loop:
#   - model node  = LLM decides what to do next (Reason + Act)
#   - tools node  = executes the chosen tool, returns ToolMessage (Observe)
#   - loop repeats until the LLM produces an answer with no tool calls

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — Trace printer (makes the ReAct loop visible)
# ─────────────────────────────────────────────────────────────────────────────

def print_trace(chunk: dict) -> None:
    """
    Pretty-print one streaming chunk from the agent loop.

    The agent streams updates as dicts like:
        {"model": {"messages": [AIMessage(...)]}}
        {"tools": {"messages": [ToolMessage(...)]}}

    Each key is a node name in the graph. Each value contains the messages
    that node produced during this step.
    """
    for node_name, node_output in chunk.items():
        # node_name: which graph node produced this output ("model" or "tools")
        # node_output: dict with key "messages" containing a list of messages

        messages = node_output.get("messages", [])

        for message in messages:

            if isinstance(message, AIMessage):
                # ── The LLM just produced output ──────────────────────────
                print(f"\n{'─'*55}")
                print(f"  🧠  MODEL NODE  (LLM is thinking/deciding)")
                print(f"{'─'*55}")

                if message.tool_calls:
                    # The LLM decided to call one or more tools.
                    # This is the "Act" part of ReAct.
                    for tc in message.tool_calls:
                        print(f"  → Tool selected : {tc['name']}")
                        print(f"  → Arguments     : {json.dumps(tc['args'], indent=6)}")
                    # Note: message.content may be empty here — the LLM's
                    # "thought" is implicit in its choice of tool + args.
                    if message.content:
                        print(f"  → Reasoning     : {message.content}")

                else:
                    # No tool calls → this is the FINAL answer.
                    # The LLM has finished reasoning and is responding to the user.
                    print(f"  ✓ Final answer ready (no more tool calls)")

            elif isinstance(message, ToolMessage):
                # ── A tool just returned a result ──────────────────────────
                # This is the "Observe" part of ReAct.
                print(f"\n{'─'*55}")
                print(f"  🔧  TOOLS NODE  (tool executed, result returned)")
                print(f"{'─'*55}")
                print(f"  → Tool name  : {message.name}")

                # Tool results are JSON strings — parse for pretty display
                try:
                    result_data = json.loads(message.content)
                    # Show the key result fields, not the entire dict
                    if isinstance(result_data, dict):
                        success = result_data.get("success", "?")
                        print(f"  → Success    : {success}")
                        # Print the human-readable summary if available
                        summary_key = next(
                            (k for k in ("summary", "analyst_summary", "interpretation")
                             if k in result_data),
                            None
                        )
                        if summary_key:
                            print(f"  → Summary    : {result_data[summary_key]}")
                        elif not success:
                            print(f"  → Error      : {result_data.get('error', 'unknown')}")
                except (json.JSONDecodeError, TypeError):
                    # If tool returned a plain string (not JSON), show it directly
                    print(f"  → Result     : {message.content[:200]}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — Main execution loop
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "═"*55)
    print("  FinSight — AI Financial Advisor")
    print("  Powered by Gemini + LangChain 1.3.1")
    print("═"*55)
    print("\nExample questions to try:")
    print("  • What is the current price of INFY.NS?")
    print("  • If I invest ₹8,000/month for 15 years at 13%, how much will I get?")
    print("  • My investment grew from ₹50,000 to ₹2,10,000 in 8 years. What's the CAGR?")
    print("  • Should I invest in RELIANCE.NS or do an SIP of ₹5,000/month?\n")

    conversation_history = []
    while True:

        user_question = input("\nYou: ").strip()

        if user_question.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        if not user_question:
            continue

    # ── Build the input the agent expects ────────────────────────────────────
        conversation_history.append(
            HumanMessage(content=user_question)
        )

        agent_input = {
            "messages": conversation_history
        }
        # Why a dict and not just a string?
        # The agent is a StateGraph. Its state is always a dict (AgentState).
        # Passing a plain string would cause a validation error.

        # ── Stream the agent execution ────────────────────────────────────────────
        print("\n" + "═"*55)
        print("  AGENT REASONING TRACE")
        print("═"*55)

        final_answer = None

        for chunk in agent.stream(agent_input, stream_mode="updates"):
            # agent.stream() is the key method here.
            #
            # stream_mode="updates" means: yield one chunk per graph node update.
            # Each chunk = {"node_name": {"messages": [...]}}
            # Alternative: stream_mode="values" yields full state after each step.
            # "updates" is better for tracing because it isolates each node's output.
            #
            # The loop runs once per node execution:
            #   Iteration 1: {"model": {...}}   ← LLM decided to call a tool
            #   Iteration 2: {"tools": {...}}   ← tool executed, result ready
            #   Iteration 3: {"model": {...}}   ← LLM reads result, makes final answer
            #
            # If the question needs multiple tools, you'll see more iterations.

            print_trace(chunk)

            # Capture the final AIMessage (the one with no tool_calls)
            for node_output in chunk.values():
                for message in node_output.get("messages", []):
                    if isinstance(message, AIMessage) and not message.tool_calls:
                        final_answer = message.content

        # ── Print the final answer cleanly ───────────────────────────────────────
        print("\n" + "═"*55)
        print("  FINAL ANSWER")
        print("═"*55)

        if final_answer:
            conversation_history.append(
                AIMessage(content=str(final_answer))
            )

            print(f"\n{final_answer}\n")
        else:
            print("\n[Agent produced no final text response — check the trace above]\n")

        print("═"*55)
        print("  Disclaimer: This is educational output, not certified financial advice.")
        print("═"*55 + "\n")


    # ─────────────────────────────────────────────────────────────────────────────
    # SECTION 10 — Entry point
    # ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
        # This guard means: only run main() when you execute this file directly.
        # If another file imports agent_test.py, main() won't auto-run.
        # It's a Python best practice for all runnable scripts.
        main()