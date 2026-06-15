"""
demo.py — Day 01: What is an AI Agent?
=======================================
Google ADK · LiteLLM · OpenRouter · In-memory sessions

Orchestrates all six scenarios in sequence.
Each scenario is in its own file (scenario_01.py … scenario_06.py).
Shared helpers and configuration live in common.py.

Run:
    python demo.py

Run a single scenario:
    python scenario_01.py
"""

import asyncio
import os

import common  # triggers load_dotenv() + asyncio logging suppression at module level

import scenario_01
import scenario_02
import scenario_03
import scenario_04
import scenario_05
import scenario_06
from common import FRIENDLY_SYSTEM_PROMPT, FORMAL_SYSTEM_PROMPT, ask, divider, make_runner, wrap


DECISION_SUPPORT_PROMPT = """
You are a e-commerce decision-support assistant.
When a customer asks for a recommendation, comparison, or choice,
reason step by step and give structured, actionable guidance.
""".strip()


def choose_system_prompt(question: str) -> tuple[str, str]:
    """Pick the best-fit agent persona for a user question."""
    normalized = question.lower()

    decision_keywords = {
        "decide",
        "recommend",
        "recommendation",
        "compare",
        "comparison",
        "choose",
        "which",
        "better",
        "best",
        "versus",
        "vs",
    }
    formal_keywords = {
        "policy",
        "refund",
        "return",
        "warranty",
        "terms",
        "invoice",
        "billing",
        "compliance",
        "procedure",
    }

    if any(keyword in normalized for keyword in decision_keywords):
        return DECISION_SUPPORT_PROMPT, "decision-support"
    if any(keyword in normalized for keyword in formal_keywords):
        return FORMAL_SYSTEM_PROMPT, "formal"
    return FRIENDLY_SYSTEM_PROMPT, "friendly"


async def interactive_mode() -> None:
    """Allow user to type custom prompts after the scripted demo."""
    divider("CUSTOM PROMPTS")
    print("""
  The scripted demo is complete.
  You can now enter your own prompts.
  The demo will automatically choose the most suitable agent style.
    """)

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Session ended]")
            break

        if not user_input:
            continue

        system_prompt, agent_style = choose_system_prompt(user_input)
        runner, user_id, session_id = await make_runner(system_prompt)
        reply = await ask(runner, user_id, session_id, user_input)

        print(f"\n  [Using {agent_style} agent]")
        print(f"  Agent: {wrap(reply, indent=10)}\n")

        continue_choice = input("  Continue? (y/n): ").strip().lower()
        if continue_choice not in {"y", "yes"}:
            print("  [Session ended]\n")
            break


async def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print(
            "\n[ERROR] OPENROUTER_API_KEY is not set.\n"
            "Create a .env file in this directory with:\n"
            "  OPENROUTER_API_KEY=your-key-here\n"
        )
        return

    print("""
+======================================================================+
|           DAY 01 -- What Is an AI Agent?  (Google ADK Demo)         |
|   Model  : google/gemini-2.5-flash      via OpenRouter + LiteLLM   |
+======================================================================+

  This demo walks through six scenarios that illustrate how an AI agent
  differs from a chatbot.  Each scenario is self-contained.
    """)

    await scenario_01.run()
    await scenario_02.run()
    await scenario_03.run()
    await scenario_04.run()
    await scenario_05.run()
    await scenario_06.run()

    print("\n" + "=" * 70)
    print("  Demo complete.")
    print("=" * 70)

    custom_prompt_choice = input(
        "\n  Do you want to try your own prompts? (y/n): "
    ).strip().lower()
    if custom_prompt_choice in {"y", "yes"}:
            await interactive_mode()
    else:
        print("  [Goodbye!]\n")


if __name__ == "__main__":
    asyncio.run(main())
