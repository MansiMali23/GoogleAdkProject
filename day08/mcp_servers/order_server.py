"""
order_server.py — Order MCP tool server
==============================================
A FastMCP server exposing eComBot's shipment-order tools over
Streamable HTTP. agent.py starts this as a background subprocess and
connects to it with McpToolset/StreamableHTTPConnectionParams — unlike
product_server.py, which is spawned per-toolset over stdio. The two
transports are deliberately different so the demo shows both styles of
MCP tool server.

Tools:
  get_order_status(order_id)   -> quick status lookup
  get_order_details(order_id)  -> full order record
  list_orders(email)             -> all orders for a customer
  cancel_order(order_id, confirm=False)
                                    -> cancel ONE order; requires an
                                       explicit confirm=True. There is
                                       deliberately no "cancel all
                                       orders" tool.

Run directly for local testing:
    python order_server.py
    # serves on http://127.0.0.1:8765/mcp by default
"""

import os

from mcp.server.fastmcp import FastMCP

# WARNING level — keep the demo's console output free of per-request
# "Processing request of type ..." noise (and uvicorn's access log).
mcp = FastMCP(
    "ecombot-order",
    log_level="WARNING",
    host=os.getenv("BOOKING_SERVER_HOST", "127.0.0.1"),
    port=int(os.getenv("BOOKING_SERVER_PORT", "8765")),
)

# ── Mock order data ───────────────────────────────────────────────────────
_BOOKINGS: dict[str, dict] = {
    "TB-2001": {
        "order_id": "TB-2001",
        "passenger_name": "Ravi Kumar",
        "email": "ravi.kumar@example.com",
        "origin": "Bengaluru (BLR)",
        "destination": "Delhi (DEL)",
        "departure_date": "2026-06-12",
        "shipment_number": "TB-401",
        "cabin_class": "Economy",
        "status": "Confirmed",
    },
    "TB-2002": {
        "order_id": "TB-2002",
        "passenger_name": "Meera Nair",
        "email": "meera.nair@example.com",
        "origin": "Mumbai (BOM)",
        "destination": "Dubai (DXB)",
        "departure_date": "2026-06-19",
        "shipment_number": "TB-512",
        "cabin_class": "Business",
        "status": "Confirmed",
    },
    "TB-2003": {
        "order_id": "TB-2003",
        "passenger_name": "John Mathews",
        "email": "john@example.com",
        "origin": "Bengaluru (BLR)",
        "destination": "Singapore (SIN)",
        "departure_date": "2026-06-04",
        "shipment_number": "TB-330",
        "cabin_class": "Economy",
        "status": "Completed",
    },
    "TB-2004": {
        "order_id": "TB-2004",
        "passenger_name": "John Mathews",
        "email": "john@example.com",
        "origin": "Delhi (DEL)",
        "destination": "Singapore (SIN)",
        "departure_date": "2026-06-18",
        "shipment_number": "TB-345",
        "cabin_class": "Economy",
        "status": "Confirmed",
    },
    "TB-2005": {
        "order_id": "TB-2005",
        "passenger_name": "John Mathews",
        "email": "john@example.com",
        "origin": "Mumbai (BOM)",
        "destination": "Dubai (DXB)",
        "departure_date": "2026-06-19",
        "shipment_number": "TB-512",
        "cabin_class": "Premium Economy",
        "status": "Confirmed",
    },
}


def _not_found(order_id: str) -> dict:
    return {
        "found": False,
        "order_id": order_id,
        "message": (
            f"No order found with ID '{order_id}'. Double-check the "
            "reference (it looks like TB-XXXX) or look it up by email instead."
        ),
    }


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """Look up the status of a single shipment order by its reference.

    Args:
        order_id: Order reference, e.g. "TB-2001".

    Returns:
        A dict with order_id, route, departure_date and status if found,
        or {"found": False, ...} with a guidance message if not.
    """
    order = _BOOKINGS.get(order_id.strip().upper())
    if order is None:
        return _not_found(order_id)

    return {
        "found": True,
        "order_id": order["order_id"],
        "route": f"{order['origin']} -> {order['destination']}",
        "departure_date": order["departure_date"],
        "status": order["status"],
    }


@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """Fetch the full record for a single shipment order.

    Args:
        order_id: Order reference, e.g. "TB-2002".

    Returns:
        The full order record (passenger, route, dates, cabin class,
        status) if found, or {"found": False, ...} if not.
    """
    order = _BOOKINGS.get(order_id.strip().upper())
    if order is None:
        return _not_found(order_id)

    return {"found": True, **order}


@mcp.tool()
def list_orders(email: str) -> dict:
    """List all orders for a customer, identified by email address.

    Use this when the user does not know (or did not provide) a order
    reference, or when a request could affect more than one order.

    Args:
        email: Ecommerceler's email address, e.g. "john@example.com".

    Returns:
        A dict with the email and a list of orders (order_id, route,
        departure_date, cabin_class, status). The list is empty if no
        orders match.
    """
    email_norm = email.strip().lower()
    matches = [
        {
            "order_id": b["order_id"],
            "route": f"{b['origin']} -> {b['destination']}",
            "departure_date": b["departure_date"],
            "cabin_class": b["cabin_class"],
            "status": b["status"],
        }
        for b in _BOOKINGS.values()
        if b["email"].lower() == email_norm
    ]

    result: dict = {"email": email, "orders": matches}
    if not matches:
        result["message"] = f"No orders found for {email}."
    return result


@mcp.tool()
def cancel_order(order_id: str, confirm: bool = False) -> dict:
    """Cancel a single shipment order. Requires explicit confirmation.

    This tool only ever accepts ONE order_id - there is intentionally no
    way to cancel multiple orders in one call. If a user asks to cancel
    "all" orders, or every order matching some criteria, use
    list_orders to find the candidates and ask the user to choose a
    specific order_id before calling this tool.

    Args:
        order_id: Order reference to cancel, e.g. "TB-2004".
        confirm: Must be True to actually cancel. Call this tool first with
            confirm=False (or omitted) to preview what will be cancelled,
            then call again with confirm=True only after the user agrees.

    Returns:
        A dict describing the order to be cancelled (when confirm=False),
        confirmation that it was cancelled (when confirm=True), or
        {"found": False, ...} if the order_id does not exist.
    """
    order = _BOOKINGS.get(order_id.strip().upper())
    if order is None:
        return _not_found(order_id)

    route = f"{order['origin']} -> {order['destination']}"

    if not confirm:
        return {
            "found": True,
            "order_id": order["order_id"],
            "status": "cancellation_pending",
            "message": (
                f"This will cancel order {order['order_id']} "
                f"({route} on {order['departure_date']}). "
                "Call cancel_order again with confirm=True to proceed."
            ),
        }

    order["status"] = "Cancelled"
    return {
        "found": True,
        "order_id": order["order_id"],
        "status": "Cancelled",
        "message": f"Order {order['order_id']} ({route}) has been cancelled.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
