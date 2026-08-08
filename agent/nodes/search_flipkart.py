"""Node: search Flipkart for matching products.

Currently backed by mock data (agent/tools/mock_products.py). Swap the body
of this function for a real API/scraper call later -- keep the same return
shape: {"flipkart_results": [...], "errors": [...]}.
"""

from __future__ import annotations

from agent.state import AgentState
from agent.tools.mock_products import search_platform


def search_flipkart_node(state: AgentState) -> dict:
    filters = state.get("parsed_filters", {})
    product = filters.get("product", state.get("query", ""))

    try:
        results = search_platform("flipkart", product)
        return {"flipkart_results": results}
    except Exception as exc:  # noqa: BLE001
        return {"flipkart_results": [], "errors": [f"flipkart search failed: {exc}"]}
