"""
agent.py — Formal E-commerce Advisor
===================================
Example: day02/formal_support/

Concept:
  The same model answers the same e-commerce question — but with a completely
  different tone because the instruction is different.

  Compare this side-by-side with day02/friendly_support/ to see how the
  instruction (not the model) controls reply style.

ADK Web:
  Run from lab/demo/day02/:
      adk web day02/formal_support

  Send the same message you used in friendly_support and compare the replies.
"""

from pathlib import Path

import litellm
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

litellm.suppress_debug_info = True
load_dotenv()

# ── Instruction ────────────────────────────────────────────────────────────
# Same file-loading pattern as friendly_support — only the text inside differs.
_INSTRUCTION = (Path(__file__).parent / "instruction.txt").read_text().strip()

# ── Model ──────────────────────────────────────────────────────────────────
_MODEL = "openrouter/google/gemini-2.5-flash"

# ── Agent ──────────────────────────────────────────────────────────────────
# Note the name differs from friendly_support_agent — each agent has its own identity.
root_agent = LlmAgent(
    name="formal_support_agent",
    model=LiteLlm(model=_MODEL),
    instruction=_INSTRUCTION,
    description="A formal, professional store e-commerce advisor",
)
