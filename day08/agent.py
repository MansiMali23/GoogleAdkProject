"""
agent.py — Day 08 eComBot: MCP tool servers via FastMCP
============================================================
Concept: Agents call out to small, well-scoped tool servers over MCP
instead of having tool functions baked into the agent process. This demo
deliberately mixes two MCP transports:

  order_toolset — mcp_servers/order_server.py, run ONCE as a
                     background Streamable HTTP server (its own process,
                     listening on http://127.0.0.1:8765/mcp). A single
                     McpToolset/HTTP client session is shared by both agents
                     below via StreamableHTTPConnectionParams.
                     Tools: get_order_status, get_order_details,
                     list_orders, cancel_order

  product_toolset   — mcp_servers/product_server.py, spawned per-toolset as a
                     stdio subprocess via StdioConnectionParams.
                     Tools: find_products (normal speed)

root_agent combines both toolsets for scenarios 1A, 2A, 3B and 4A.

timeout_demo_agent (Scenario 3A) uses a second product toolset whose server
process is started with PRODUCT_SEARCH_DELAY_SECONDS set higher than the
toolset's own MCP timeout, so the find_products call times out and ADK's
graceful MCP error handling returns {"error": ...} instead of hanging.

ADK Web:
    adk web .          ← discovers root_agent automatically
"""

import atexit
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import litellm
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

# ── Silence noisy loggers (same pattern as previous days) ─────────────────
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
os.environ.setdefault("LITELLM_LOG", "ERROR")
for _name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
    _log = logging.getLogger(_name)
    _log.setLevel(logging.CRITICAL)
    _log.propagate = False

litellm.suppress_debug_info = True
load_dotenv()

_MODEL = "openrouter/google/gemini-2.5-flash"

_SERVERS_DIR = Path(__file__).parent / "mcp_servers"
_BOOKING_SERVER = str(_SERVERS_DIR / "order_server.py")
_PRODUCT_SERVER = str(_SERVERS_DIR / "product_server.py")

# Scenario 3A tuning — see .env.example
_SLOW_PRODUCT_DELAY_SECONDS = os.getenv(
  "PRODUCT_SEARCH_DELAY_SECONDS",
  "8",
)
_SLOW_PRODUCT_TIMEOUT_SECONDS = float(
  os.getenv("PRODUCT_TOOL_TIMEOUT_SECONDS", "3")
)

# ── Order server: Streamable HTTP, started once as a background process ──
_ORDER_HOST = os.getenv("ORDER_SERVER_HOST", "127.0.0.1")
_ORDER_PORT = int(os.getenv("ORDER_SERVER_PORT", "8765"))
_ORDER_URL = f"http://{_ORDER_HOST}:{_ORDER_PORT}/mcp"


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"order_server.py did not start on {host}:{port} within {timeout}s")


def _start_order_server() -> subprocess.Popen:
  proc = subprocess.Popen(
    [sys.executable, _BOOKING_SERVER],
    env={
      **os.environ,
      "ORDER_SERVER_HOST": _ORDER_HOST,
      "ORDER_SERVER_PORT": str(_ORDER_PORT),
    },
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  _wait_for_port(_ORDER_HOST, _ORDER_PORT)
  return proc


_order_server_process = _start_order_server()


def shutdown_order_server() -> None:
    """Stop the background order MCP server. Safe to call more than once."""
    if _order_server_process.poll() is None:
        _order_server_process.terminate()
        _order_server_process.wait(timeout=5)


atexit.register(shutdown_order_server)


_PERSONA = """
You are EcomAssist, eComBot's ecommerce assistant. You help ecommercelers check
shipment orders, look up order details, and find products near their
delivery city.

You have access to these tools, provided by MCP tool servers:

Order tools:
  - get_order_status(order_id): quick status check for one order
  - get_order_details(order_id): full details for one order
    (route, dates, service tier, status)
  - list_orders(email): all orders for a customer's email address
  - cancel_order(order_id, confirm): cancel ONE order

Product tools:
  - find_products(city, max_price_inr, near): search products by
    city, with optional price ceiling and area/landmark preference

General rules:
  - If you need a order reference or email to look something up and the
    user hasn't given you one, ask for it before calling a tool. Never
    guess or invent a order ID.
  - Tool results are structured data, not conversation text. Read them
    carefully and summarise the relevant parts in plain language - don't
    dump raw JSON at the user.
  - Never invent order details, statuses, or product listings. Only report
    what the tools return.
  - If a tool result has "found": false, or contains an "error" field,
    explain plainly what happened (for example, the order reference
    wasn't found, or the product search is temporarily unavailable) and
    suggest a next step (double-check the reference, try again shortly, or
    adjust the search). Don't pretend the call succeeded, and don't retry
    the same tool call again - report the issue instead.

Multi-step flows:
  - If a request involves both a order and a product (for example, "confirm
    my shipment and suggest a product"), first call a order tool to confirm
    the shipment details, then use the delivery city from that result for
    find_products. Don't ask the user to repeat information your tools
    already gave you.

Cancellations (safety-critical):
  - cancel_order only ever cancels ONE specific order_id. There is no
    tool to cancel multiple orders at once, on purpose.
  - If a user asks to cancel "all" orders, every order for an email, or
    every order matching some criteria, do NOT try to loop over
    cancel_order yourself. Instead call list_orders to show the
    candidates and ask the user which single order_id they want to
    cancel.
  - Before cancelling, always confirm the specific order with the user.
    Call cancel_order with confirm=False (or omitted) first to preview,
    then call it again with confirm=True only after the user explicitly
    agrees.
""".strip()


def _order_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
      url=_ORDER_URL,
            timeout=10,
        ),
    )


def _product_toolset(*, delay_seconds: str, timeout: float) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
              args=[_PRODUCT_SERVER],
              env={
                "PRODUCT_SEARCH_DELAY_SECONDS": delay_seconds,
              },
            ),
            timeout=timeout,
        ),
    )


# ── Main agent — order + product tools at normal speed ─────────────────────
order_toolset = _order_toolset()
product_toolset = _product_toolset(delay_seconds="0", timeout=10)

root_agent = LlmAgent(
    name="ecom_assist",
    model=LiteLlm(model=_MODEL),
    instruction=_PERSONA,
    description="EcomAssist — eComBot assistant backed by order and product MCP tool servers.",
    tools=[order_toolset, product_toolset],
)


# ── Timeout-demo agent (Scenario 3A) ────────────────────────────────────────
# Reuses the shared order_toolset (one HTTP client session per process is
# enough — opening a second concurrent session against the same order
# server here led to MCP session-setup errors). Only the product toolset
# differs: its own stdio subprocess, started with PRODUCT_SEARCH_DELAY_SECONDS
# higher than its own MCP timeout so find_products times out.
slow_product_toolset = _product_toolset(
  delay_seconds=_SLOW_PRODUCT_DELAY_SECONDS,
  timeout=_SLOW_PRODUCT_TIMEOUT_SECONDS,
)

timeout_demo_agent = LlmAgent(
    name="ecom_timeout_demo",
    model=LiteLlm(model=_MODEL),
    instruction=_PERSONA,
    description="EcomAssist with a slow product MCP server, for demonstrating tool-call timeout fallback.",
    tools=[order_toolset, slow_product_toolset],
)
