"""Day 07 demo: route eComBot queries to fast/deep model groups with fallback."""

import asyncio
import logging
import os
import textwrap

from dotenv import load_dotenv
from google.genai import types

load_dotenv()

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
os.environ.setdefault("LITELLM_LOG", "ERROR")

from agent import ecom_faq, ecom_planning
from routing import (
    BACKUP_MODEL,
    DEEP_MODEL,
    FAST_MODEL,
    classify_query,
    enable_routing_callbacks,
    fallback_demo_router,
    routing_log,
    timeout_demo_router,
)
from session import make_runner

enable_routing_callbacks()


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


async def _router_ask(router, prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are EcomAssist. Keep answers concise."},
        {"role": "user", "content": prompt},
    ]
    try:
        response = await router.acompletion(model="primary", messages=messages)
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        return f"[fallback chain failed: {exc}]"


def _print_events() -> None:
    for ev in routing_log:
        if ev["status"] == "success":
            print(f"  [gateway] SUCCESS model={ev['model']} latency={ev['latency_ms']}ms")
        else:
            print(f"  [gateway] FAILURE model={ev['model']} error={ev['error']}")


async def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is missing.")
        return

    faq_runner, faq_user, faq_session = await make_runner(ecom_faq)
    deep_runner, deep_user, deep_session = await make_runner(ecom_planning)

    print("Day07 eComBot routing demo")
    print(f"fast-faq model: {FAST_MODEL}")
    print(f"deep-planning model: {DEEP_MODEL}")
    print(f"backup model: {BACKUP_MODEL}\n")

    faq_prompt = "What is your return policy for electronics?"
    deep_prompt = "Compare Pixel 8a and Galaxy A55 under INR 40,000 with pros and cons."

    routing_log.clear()
    print(f"classify_query => {classify_query(faq_prompt)}")
    print(f"You: {faq_prompt}")
    faq_reply = await _ask(faq_runner, faq_user, faq_session, faq_prompt)
    print(f"\n[ecom_faq]\n{_wrap(faq_reply)}")
    _print_events()

    routing_log.clear()
    print(f"\nclassify_query => {classify_query(deep_prompt)}")
    print(f"You: {deep_prompt}")
    deep_reply = await _ask(deep_runner, deep_user, deep_session, deep_prompt)
    print(f"\n[ecom_planning]\n{_wrap(deep_reply)}")
    _print_events()

    print("\nFallback demo (primary model error):")
    routing_log.clear()
    fallback_reply = await _router_ask(fallback_demo_router, "Track order ORD-001")
    _print_events()
    print(_wrap(fallback_reply))

    print("\nTimeout fallback demo:")
    routing_log.clear()
    timeout_reply = await _router_ask(timeout_demo_router, "Recommend earbuds under INR 6000")
    _print_events()
    print(_wrap(timeout_reply))


if __name__ == "__main__":
    asyncio.run(main())
