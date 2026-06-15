# Day 02 — Prompt Refinement, Intent Modeling, and Manual Testing

Google ADK · Gemini 2.5 Flash via OpenRouter · ADK Web

---

## What this demo shows

| Example | Concept |
|---|---|
| `friendly_support` | Warm tone driven by system prompt |
| `formal_support` | Same query, formal tone — shows tone is prompt-controlled |
| `scope_limited_support` | Scope enforcement and polite refusal |
| `unknown_data` | Honest fallback when live data is unavailable |
| `session_memory` | Multi-turn context within a single session |

Each example lives in its own folder under `day02/`.
The **folder structure is deliberate** — it makes prompt differences visible
and lets you open two folders side-by-side to compare them.

---

## Setup

```bash
# 1. Activate the shared virtual environment (from repo root)
source .venv/bin/activate

# 2. Copy the env file and add your OpenRouter key
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY

# 3. Install dependencies (if not already installed)
pip install -r requirements.txt
```

---

## Running in ADK Web

### All examples at once (pick one from the left panel)

```bash
cd lab/demo/day02
adk web day02/
```

### One example at a time

```bash
cd lab/demo/day02
adk web day02/friendly_support
adk web day02/formal_support
adk web day02/scope_limited_support
adk web day02/unknown_data
adk web day02/session_memory
```

Open `http://localhost:8000` in your browser.

---

## Suggested test messages per example

### friendly_support
```
I'm looking to buy a laptop. What should I consider before purchasing?
```

### formal_support
```
I need to modify my recent order and apply a discount code. What's the procedure?
```

### scope_limited_support
```
Can you help me track my order status?
```
Then try an out-of-scope question:
```
What is the capital of France?
```

### unknown_data
```
What is the current price of the iPhone 15 Pro in stock?
```

### session_memory
```
Turn 1: I'm shopping for a gaming setup with a budget of $2000 and interested in RTX 4090 GPUs.
Turn 2: What monitor resolution would you recommend for that GPU?
```

---

## How to experiment

1. Open `instruction.txt` in any example folder.
2. Change a word — e.g., swap "warm" for "concise" in `friendly_support`.
3. Restart `adk web` (Ctrl-C, then re-run).
4. Send the same message and observe the difference in reply style.

This is the core learning: **the instruction is the lever.**
