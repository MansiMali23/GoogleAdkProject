"""
agent.py — Friendly E-commerce Assistant
=====================================
Example: day02/friendly_support/

Concept:
  A system prompt defines the agent's persona and tone.
  Here the assistant is warm, conversational, and enthusiastic.

ADK Web:
  Run from lab/demo/day02/:
      adk web day02/friendly_support

  Then open http://localhost:8000 and send a e-commerce question.
  Try editing instruction.txt and restarting to see the tone change.
"""

from pathlib import Path

import litellm
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Silence LiteLLM debug noise in the ADK Web console
litellm.suppress_debug_info = True

# Load OPENROUTER_API_KEY from .env (looks upward from cwd)
load_dotenv()

# ── Instruction ────────────────────────────────────────────────────────────
# Loaded from the companion text file so it can be edited without touching code.
# This is the key design point: the instruction is the only thing that differs
# between examples.
_INSTRUCTION = (Path(__file__).parent / "instruction.txt").read_text().strip()

# ── Model ──────────────────────────────────────────────────────────────────
# Gemini 2.5 Flash via OpenRouter, using ADK's LiteLlm adapter.
_MODEL = "openrouter/google/gemini-2.5-flash"

# ── Agent ──────────────────────────────────────────────────────────────────
# ADK Web discovers `root_agent` automatically when pointed at this folder.
root_agent = LlmAgent(
    name="friendly_support_agent",
    model=LiteLlm(model=_MODEL),
    instruction=_INSTRUCTION,
    description="A warm, friendly e-commerce support assistant",
)
