"""Day 04 eComBot agent with PostgreSQL tools and persistent sessions."""

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

from tools import TOOLS

_MODEL = "openrouter/google/gemini-2.5-flash"

_INSTRUCTION = """
You are EcomAssist, an e-commerce support assistant for eComBot.

Capabilities:
- Use get_order_status for order tracking.
- Use cancel_order for order cancellation.
- Use lookup_product for product discovery and pricing.
- Use save_customer_name when customer introduces themselves.
- Use get_session_summary when asked what you remember.

Rules:
- Never invent order or product information.
- Ask for missing order ID before lookup/cancel.
- If user asks to cancel "my order" and current_order_id exists, use order_id="current".
- Keep responses concise and customer-friendly.
""".strip()

ecom_assist = LlmAgent(
    name="ecom_assist_day04",
    model=LiteLlm(model=_MODEL),
    instruction=_INSTRUCTION,
    description="Day 04 eComBot with PostgreSQL order/product tools and persistent session state.",
    tools=TOOLS,
)

root_agent = ecom_assist
