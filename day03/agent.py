"""Day 03 agent wiring for eComBot tool calling and in-memory state."""

import logging
import os

import litellm
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
os.environ.setdefault("LITELLM_LOG", "ERROR")
for _name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
    _log = logging.getLogger(_name)
    _log.setLevel(logging.CRITICAL)
    _log.propagate = False

litellm.suppress_debug_info = True
load_dotenv()

from tools import get_order_status, get_session_summary, lookup_product, save_customer_name

_MODEL = "openrouter/google/gemini-2.5-flash"

_INSTRUCTION = """
You are EcomAssist, an e-commerce support assistant.

Capabilities:
- Use get_order_status for order tracking requests.
- Use lookup_product for catalog discovery requests.
- Use save_customer_name when users introduce themselves.
- Use get_session_summary when users ask what context you remember.

Rules:
- Never invent order details or product data.
- Ask for an order ID if missing.
- Keep answers concise, clear, and customer-friendly.
""".strip()

ecom_assist = LlmAgent(
    name="ecom_assist",
    model=LiteLlm(model=_MODEL),
    instruction=_INSTRUCTION,
    description="Day 03 eComBot assistant with order/product tools and session memory.",
    tools=[get_order_status, lookup_product, save_customer_name, get_session_summary],
)

root_agent = ecom_assist
