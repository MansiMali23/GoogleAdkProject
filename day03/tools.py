"""Day 03 tools: order and product mock tools with in-memory session state."""

from typing import Any

from google.adk.tools import ToolContext

_ORDER_DB: dict[str, dict[str, Any]] = {
    "ORD-001": {
        "order_id": "ORD-001",
        "status": "Shipped",
        "eta": "2026-06-20",
        "carrier": "BlueDart",
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "status": "Processing",
        "eta": "2026-06-22",
        "carrier": "DTDC",
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "status": "Delivered",
        "eta": "Delivered",
        "carrier": "FedEx",
    },
}

_PRODUCT_DB: dict[str, list[dict[str, Any]]] = {
    "phone": [
        {"sku": "PRD-101", "name": "Pixel 8a", "price_inr": 39999, "stock": 14},
        {"sku": "PRD-102", "name": "Galaxy A55", "price_inr": 35999, "stock": 20},
    ],
    "earbuds": [
        {"sku": "PRD-201", "name": "Pixel Buds A", "price_inr": 8999, "stock": 31},
        {"sku": "PRD-202", "name": "OnePlus Buds 3", "price_inr": 5499, "stock": 18},
    ],
}


def get_order_status(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    key = order_id.strip().upper()
    tool_context.state["last_order_id"] = key
    order = _ORDER_DB.get(key)
    if order:
        return {"found": True, **order}
    return {"found": False, "order_id": key, "error": f"Order '{key}' not found."}


def lookup_product(product_name: str, tool_context: ToolContext) -> dict[str, Any]:
    key = product_name.strip().lower()
    tool_context.state["last_product_query"] = key
    products = _PRODUCT_DB.get(key)
    if products:
        return {"found": True, "product_name": product_name, "products": products}
    return {
        "found": False,
        "product_name": product_name,
        "error": f"No products found for '{product_name}'. Try phone or earbuds.",
    }


def save_customer_name(name: str, tool_context: ToolContext) -> dict[str, Any]:
    clean = name.strip()
    if not clean:
        return {"saved": False, "error": "Name cannot be empty."}
    tool_context.state["customer_name"] = clean
    return {"saved": True, "customer_name": clean}


def get_session_summary(tool_context: ToolContext) -> dict[str, Any]:
    return {
        "customer_name": tool_context.state.get("customer_name", "unknown"),
        "last_order_id": tool_context.state.get("last_order_id", "none"),
        "last_product_query": tool_context.state.get("last_product_query", "none"),
    }
