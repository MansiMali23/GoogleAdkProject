"""Day 03 demo for tool calling and session memory."""

import asyncio
import os
import textwrap

from google.genai import types

from agent import ecom_assist
from session import make_runner


def _wrap(text: str) -> str:
    return textwrap.fill(text, width=74, initial_indent="    ", subsequent_indent="    ")


def _msg(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


async def _ask(runner, user_id: str, session_id: str, prompt: str) -> str:
    reply = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=_msg(prompt)):
        if event.is_final_response() and event.content and event.content.parts:
            reply = event.content.parts[0].text or ""
    return reply.strip()


async def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is missing in environment.")
        return

    runner, user_id, session_id = await make_runner(ecom_assist)
    print("Day03 eComBot demo. Type q to quit.")
    print("Examples: Where is my order ORD-001? | show phone products | my name is Priya")

    while True:
        prompt = input("You: ").strip()
        if prompt.lower() == "q":
            break
        if not prompt:
            continue
        reply = await _ask(runner, user_id, session_id, prompt)
        print(f"\n[EcomAssist]\n{_wrap(reply)}\n")


if __name__ == "__main__":
    asyncio.run(main())
