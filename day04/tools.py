"""Day 04 tools backed by PostgreSQL for eComBot."""

import logging
import re
from typing import Any

from google.adk.tools import ToolContext

from db import execute, query_all, query_one

log = logging.getLogger(__name__)
_ORDER_ID_RE = re.compile(r"^ORD-\d{3}$")


def _valid_order_id(order_id: str) -> bool:
    return bool(_ORDER_ID_RE.match(order_id.strip().upper()))


def get_order_status(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    if not order_id or not order_id.strip():
        return {"found": False, "error": "Order ID cannot be empty."}

    oid = order_id.strip().upper()
    if not _valid_order_id(oid):
        return {"found": False, "order_id": oid, "error": "Invalid order ID format. Use ORD-001 style."}

    try:
        row = query_one("SELECT * FROM orders WHERE order_id = %s", (oid,))
    except Exception as exc:
        log.error("DB error in get_order_status: %s", exc)
        return {"found": False, "error": "Order lookup is temporarily unavailable."}

    if row is None:
        return {"found": False, "order_id": oid, "error": f"Order '{oid}' not found."}

    tool_context.state["current_order_id"] = oid
    tool_context.state["current_customer_name"] = row["customer_name"]

    return {
        "found": True,
        "order_id": row["order_id"],
        "customer_name": row["customer_name"],
        "status": row["status"],
        "eta": str(row["eta"]),
        "carrier": row["carrier"],
    }


def cancel_order(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    if not order_id or order_id.strip().lower() in ("", "current"):
        order_id = tool_context.state.get("current_order_id", "")

    if not order_id:
        return {"cancelled": False, "error": "No order ID provided or found in this session."}

    oid = order_id.strip().upper()
    if not _valid_order_id(oid):
        return {"cancelled": False, "order_id": oid, "error": "Invalid order ID format. Use ORD-001 style."}

    try:
        row = query_one("SELECT status, customer_name FROM orders WHERE order_id = %s", (oid,))
    except Exception as exc:
        log.error("DB error in cancel_order lookup: %s", exc)
        return {"cancelled": False, "error": "Cancellation service is temporarily unavailable."}

    if row is None:
        return {"cancelled": False, "order_id": oid, "error": f"Order '{oid}' not found."}

    if row["status"].lower() in ("cancelled", "delivered"):
        return {
            "cancelled": False,
            "order_id": oid,
            "error": f"Order '{oid}' cannot be cancelled in status '{row['status']}'.",
        }

    try:
        execute("UPDATE orders SET status = 'Cancelled' WHERE order_id = %s", (oid,))
    except Exception as exc:
        log.error("DB error updating order: %s", exc)
        return {"cancelled": False, "error": "Cancellation could not be saved."}

    tool_context.state["current_order_id"] = oid
    return {
        "cancelled": True,
        "order_id": oid,
        "customer_name": row["customer_name"],
        "message": f"Order {oid} for {row['customer_name']} has been cancelled.",
    }


def lookup_product(product_name: str, tool_context: ToolContext) -> dict[str, Any]:
    if not product_name or not product_name.strip():
        return {"found": False, "error": "Product name is required."}

    pname = product_name.strip()
    tool_context.state["last_lookup_key"] = pname

    try:
        rows = query_all(
            """
            SELECT product_id, name, category, price_inr, in_stock
            FROM products
            WHERE LOWER(name) LIKE LOWER(%s)
               OR LOWER(category) LIKE LOWER(%s)
            ORDER BY price_inr ASC
            """,
            (f"%{pname}%", f"%{pname}%"),
        )
    except Exception as exc:
        log.error("DB error in lookup_product: %s", exc)
        return {"found": False, "error": "Product lookup is temporarily unavailable."}

    if not rows:
        return {"found": False, "product_name": pname, "error": f"No products found for '{pname}'."}

    first_id = rows[0]["product_id"]
    tool_context.state["current_product_id"] = first_id

    return {
        "found": True,
        "product_name": pname,
        "products": [
            {
                "product_id": r["product_id"],
                "name": r["name"],
                "category": r["category"],
                "price_inr": float(r["price_inr"]),
                "in_stock": bool(r["in_stock"]),
            }
            for r in rows
        ],
    }


def save_customer_name(name: str, tool_context: ToolContext) -> dict[str, Any]:
    if not name or not name.strip():
        return {"saved": False, "error": "Name cannot be empty."}
    clean = name.strip()
    tool_context.state["current_customer_name"] = clean
    return {"saved": True, "customer_name": clean}


def get_session_summary(tool_context: ToolContext) -> dict[str, Any]:
    return {
        "current_customer_name": tool_context.state.get("current_customer_name", "unknown"),
        "current_order_id": tool_context.state.get("current_order_id", "none"),
        "current_product_id": tool_context.state.get("current_product_id", "none"),
        "last_lookup_key": tool_context.state.get("last_lookup_key", "not set"),
    }


TOOLS = [
    get_order_status,
    cancel_order,
    lookup_product,
    save_customer_name,
    get_session_summary,
]
