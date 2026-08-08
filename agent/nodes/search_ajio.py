"""Node: search Ajio for matching products.

Currently backed by mock data (agent/tools/mock_products.py). Swap the body
of this function for a real API/scraper call later -- keep the same return
shape: {"ajio_results": [...], "errors": [...]}.
"""

from __future__ import annotations

from agent.state import AgentState
from agent.tools.mock_products import search_platform


def search_ajio_node(state: AgentState) -> dict:
    filters = state.get("parsed_filters", {})
    product = filters.get("product", state.get("query", ""))

    try:
        results = search_platform("ajio", product)
        return {"ajio_results": results}
    except Exception as exc:  # noqa: BLE001
        return {"ajio_results": [], "errors": [f"ajio search failed: {exc}"]}
