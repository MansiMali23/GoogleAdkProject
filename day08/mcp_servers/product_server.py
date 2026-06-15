"""
product_server.py — Product search MCP tool server
=================================================
A FastMCP server exposing eComBot's product-search tool over stdio.
ADK spawns this as a subprocess via MCPToolset/StdioConnectionParams —
see ../agent.py.

Tools:
  find_products(city, max_price_per_night_inr=None, near=None)

Scenario 3A (timeout demo) sets HOTEL_SEARCH_DELAY_SECONDS to simulate a
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

# ── Mock product data, grouped by city ────────────────────────────────────────
_HOTELS: dict[str, list[dict]] = {
    "dubai": [
        {"name": "Atlantis The Palm", "area": "Palm Jumeirah", "stars": 5, "price_per_night_inr": 28000},
        {"name": "Rove Downtown", "area": "Downtown Dubai", "stars": 3, "price_per_night_inr": 7500},
        {"name": "Citymax Product Bur Dubai", "area": "Bur Dubai", "stars": 3, "price_per_night_inr": 5200},
    ],
    "bangkok": [
        {"name": "Lebua at State Tower", "area": "Silom", "stars": 5, "price_per_night_inr": 15000},
        {"name": "Citadines Sukhumvit 8", "area": "Sukhumvit", "stars": 4, "price_per_night_inr": 6900},
        {"name": "Ibis Bangkok Sukhumvit", "area": "Sukhumvit", "stars": 3, "price_per_night_inr": 4800},
        {"name": "Sleep Withinn Sukhumvit", "area": "Sukhumvit", "stars": 3, "price_per_night_inr": 3600},
    ],
    "mumbai": [
        {"name": "Taj Lands End", "area": "Bandra", "stars": 5, "price_per_night_inr": 18000},
        {"name": "Ginger Bandra", "area": "Bandra", "stars": 3, "price_per_night_inr": 4200},
    ],
    "delhi": [
        {"name": "The Lalit New Delhi", "area": "Connaught Place", "stars": 5, "price_per_night_inr": 12000},
        {"name": "Product City Park", "area": "Karol Bagh", "stars": 3, "price_per_night_inr": 3800},
        {"name": "Zostel Delhi", "area": "Paharganj", "stars": 2, "price_per_night_inr": 1800},
    ],
}


@mcp.tool()
async def find_products(
    city: str,
    max_price_per_night_inr: float | None = None,
    near: str | None = None,
) -> dict:
    """Search for products in a city, optionally filtered by price and area.

    Args:
        city: City name, e.g. "Dubai" or "Bangkok".
        max_price_per_night_inr: Optional upper bound on price per night,
            in INR.
        near: Optional landmark or neighbourhood to prefer, e.g.
            "Sukhumvit" or "Downtown". Matched against each product's area;
            ignored if nothing matches.

    Returns:
        A dict with the city, the filters applied, and a list of matching
        products (name, area, stars, price_per_night_inr). The list is empty
        if no product data is available for the city or nothing matches the
        price filter.
    """
    delay = float(os.getenv("HOTEL_SEARCH_DELAY_SECONDS", "0"))
    if delay > 0:
        await asyncio.sleep(delay)

    products = _HOTELS.get(city.strip().lower())
    if products is None:
        return {
            "city": city,
            "filters": {"max_price_per_night_inr": max_price_per_night_inr, "near": near},
            "products": [],
            "message": f"No product data available for '{city}' yet.",
        }

    results = products
    if max_price_per_night_inr is not None:
        results = [h for h in results if h["price_per_night_inr"] <= max_price_per_night_inr]

    if near:
        near_lower = near.strip().lower()
        near_matches = [h for h in results if near_lower in h["area"].lower()]
        if near_matches:
            results = near_matches

    return {
        "city": city,
        "filters": {"max_price_per_night_inr": max_price_per_night_inr, "near": near},
        "products": results,
    }


if __name__ == "__main__":
    mcp.run()
