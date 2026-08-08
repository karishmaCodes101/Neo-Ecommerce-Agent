"""Node: search Amazon for matching products.

Currently backed by mock data (agent/tools/mock_products.py). Swap the body
of this function for a real PA-API call or scraper later -- keep the same
return shape: {"amazon_results": [...], "errors": [...]}.
"""

from __future__ import annotations

from agent.state import AgentState
from agent.tools.mock_products import search_platform


def search_amazon_node(state: AgentState) -> dict:
    filters = state.get("parsed_filters", {})
    product = filters.get("product", state.get("query", ""))

    try:
        results = search_platform("amazon", product)
        return {"amazon_results": results}
    except Exception as exc:  # noqa: BLE001 - node-level isolation by design
        return {"amazon_results": [], "errors": [f"amazon search failed: {exc}"]}
