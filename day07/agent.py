"""Day 07 eComBot agents for fast/deep model routing."""

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

from routing import DEEP_MODEL, FAST_MODEL

_PERSONA = """
You are EcomAssist, eComBot's customer support and sales assistant.
Keep responses concise and practical.
For quick policy/order queries, answer directly.
For comparisons or recommendations, provide structured reasoning.
""".strip()

ecom_faq = LlmAgent(
    name="ecom_faq",
    model=LiteLlm(model=FAST_MODEL),
    instruction=_PERSONA,
    description="Fast route for FAQ/order policy queries.",
)

ecom_planning = LlmAgent(
    name="ecom_planning",
    model=LiteLlm(model=DEEP_MODEL),
    instruction=_PERSONA,
    description="Deep route for product comparison and recommendation flows.",
)

root_agent = ecom_planning
