"""
product_server.py — Product search MCP tool server
=================================================
A FastMCP server exposing eComBot's product-search tool over stdio.
ADK spawns this as a subprocess via MCPToolset/StdioConnectionParams —
see ../agent.py.

Tools:
    find_products(city, max_price_inr=None, near=None)

Scenario 3A (timeout demo) sets PRODUCT_SEARCH_DELAY_SECONDS to simulate a
slow upstream product-search provider. agent.py pairs that with a short
MCPToolset timeout, so the tool call times out and ADK's graceful MCP
error handling returns {"error": ...} to the agent instead of hanging.

Run directly for local testing:
    python product_server.py
"""

import asyncio
import os

from mcp.server.fastmcp import FastMCP

# WARNING level — keep the demo's console output free of per-request
# "Processing request of type ..." noise from the MCP server loop.
mcp = FastMCP("ecombot-products", log_level="WARNING")

# ── Mock product catalog, grouped by city ─────────────────────────────────────
_PRODUCTS: dict[str, list[dict]] = {
    "dubai": [
        {"name": "Galaxy S24 256GB", "area": "Downtown Dubai", "rating": 4.6, "price_inr": 69999},
        {"name": "Sony WH-1000XM5", "area": "Bur Dubai", "rating": 4.5, "price_inr": 28999},
        {"name": "Anker 67W Charger", "area": "Palm Jumeirah", "rating": 4.4, "price_inr": 3999},
    ],
    "bangkok": [
        {"name": "iPad Air 11-inch", "area": "Silom", "rating": 4.7, "price_inr": 57999},
        {"name": "Kindle Paperwhite", "area": "Central Market", "rating": 4.6, "price_inr": 13999},
        {"name": "Logitech MX Master 3S", "area": "Central Market", "rating": 4.8, "price_inr": 9999},
        {"name": "TP-Link AX55 Router", "area": "Central Market", "rating": 4.4, "price_inr": 7499},
    ],
    "mumbai": [
        {"name": "MacBook Air M3", "area": "Bandra", "rating": 4.8, "price_inr": 114900},
        {"name": "Nothing Phone (2)", "area": "Bandra", "rating": 4.3, "price_inr": 39999},
    ],
    "delhi": [
        {"name": "Dell XPS 13", "area": "Connaught Place", "rating": 4.5, "price_inr": 99999},
        {"name": "OnePlus Buds 3", "area": "Karol Bagh", "rating": 4.4, "price_inr": 5499},
        {"name": "Samsung T7 SSD 1TB", "area": "Paharganj", "rating": 4.7, "price_inr": 8999},
    ],
}


@mcp.tool()
async def find_products(
    city: str,
    max_price_inr: float | None = None,
    near: str | None = None,
) -> dict:
    """Search for products in a city, optionally filtered by price and area.

    Args:
        city: City name, e.g. "Dubai" or "Bangkok".
        max_price_inr: Optional upper bound on product price in INR.
        near: Optional landmark or neighbourhood to prefer, e.g.
            "Central Market" or "Downtown". Matched against each product's area;
            ignored if nothing matches.

    Returns:
        A dict with the city, the filters applied, and a list of matching
        products (name, area, rating, price_inr). The list is empty
        if no product data is available for the city or nothing matches the
        price filter.
    """
    delay = float(os.getenv("PRODUCT_SEARCH_DELAY_SECONDS", "0"))
    if delay > 0:
        await asyncio.sleep(delay)

    products = _PRODUCTS.get(city.strip().lower())
    if products is None:
        return {
            "city": city,
            "filters": {"max_price_inr": max_price_inr, "near": near},
            "products": [],
            "message": f"No product data available for '{city}' yet.",
        }

    results = products
    if max_price_inr is not None:
        results = [p for p in results if p["price_inr"] <= max_price_inr]

    if near:
        near_lower = near.strip().lower()
        near_matches = [p for p in results if near_lower in p["area"].lower()]
        if near_matches:
            results = near_matches

    return {
        "city": city,
        "filters": {"max_price_inr": max_price_inr, "near": near},
        "products": results,
    }


if __name__ == "__main__":
    mcp.run()
