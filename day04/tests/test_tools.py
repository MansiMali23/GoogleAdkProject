"""Unit tests for day04 PostgreSQL-backed tools (mocked DB calls)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import (
    cancel_order,
    get_order_status,
    get_session_summary,
    lookup_product,
    save_customer_name,
)


def _ctx(initial: dict | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.state = initial or {}
    return ctx


def test_get_order_status_empty_id():
    result = get_order_status("", _ctx())
    assert result["found"] is False


def test_get_order_status_invalid_id():
    result = get_order_status("ABC-1", _ctx())
    assert result["found"] is False


def test_get_order_status_not_found():
    with patch("tools.query_one", return_value=None):
        result = get_order_status("ORD-999", _ctx())
    assert result["found"] is False


def test_get_order_status_success_writes_state():
    row = {
        "order_id": "ORD-001",
        "customer_name": "Priya",
        "status": "Shipped",
        "eta": "2026-06-20",
        "carrier": "BlueDart",
    }
    ctx = _ctx()
    with patch("tools.query_one", return_value=row):
        result = get_order_status("ord-001", ctx)
    assert result["found"] is True
    assert ctx.state["current_order_id"] == "ORD-001"


def test_cancel_order_from_current_state():
    ctx = _ctx({"current_order_id": "ORD-004"})
    with patch("tools.query_one", return_value={"status": "Confirmed", "customer_name": "James"}), patch(
        "tools.execute", return_value=1
    ):
        result = cancel_order("current", ctx)
    assert result["cancelled"] is True


def test_cancel_order_cannot_cancel_terminal_status():
    with patch("tools.query_one", return_value={"status": "Delivered", "customer_name": "Aisha"}):
        result = cancel_order("ORD-003", _ctx())
    assert result["cancelled"] is False


def test_lookup_product_found_sets_current_product():
    rows = [{"product_id": "PRD-101", "name": "Pixel 8a", "category": "phone", "price_inr": "39999", "in_stock": True}]
    ctx = _ctx()
    with patch("tools.query_all", return_value=rows):
        result = lookup_product("phone", ctx)
    assert result["found"] is True
    assert ctx.state["current_product_id"] == "PRD-101"


def test_lookup_product_not_found():
    with patch("tools.query_all", return_value=[]):
        result = lookup_product("drone", _ctx())
    assert result["found"] is False


def test_save_customer_name():
    ctx = _ctx()
    result = save_customer_name("  Priya  ", ctx)
    assert result["saved"] is True
    assert ctx.state["current_customer_name"] == "Priya"


def test_get_session_summary_defaults():
    result = get_session_summary(_ctx())
    assert result["current_order_id"] == "none"
