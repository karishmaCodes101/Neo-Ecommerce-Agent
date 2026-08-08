"""Node: merge results from all platforms, dedupe, filter, and rank by price."""

from __future__ import annotations

from difflib import SequenceMatcher

from agent.state import AgentState, ProductResult

_TITLE_SIMILARITY_THRESHOLD = 0.85


def _is_duplicate(a: ProductResult, b: ProductResult) -> bool:
    return SequenceMatcher(None, a["title"].lower(), b["title"].lower()).ratio() >= _TITLE_SIMILARITY_THRESHOLD


def _dedupe(results: list[ProductResult]) -> list[ProductResult]:
    """Keep the cheapest entry among near-duplicate titles across platforms."""
    kept: list[ProductResult] = []
    for item in results:
        dup_index = next((i for i, k in enumerate(kept) if _is_duplicate(item, k)), None)
        if dup_index is None:
            kept.append(item)
        elif item["price"] < kept[dup_index]["price"]:
            kept[dup_index] = item
    return kept


def aggregator_node(state: AgentState) -> dict:
    all_results: list[ProductResult] = [
        *state.get("amazon_results", []),
        *state.get("flipkart_results", []),
        *state.get("myntra_results", []),
        *state.get("ajio_results", []),
    ]

    filters = state.get("parsed_filters", {})
    max_price = filters.get("max_price")
    min_price = filters.get("min_price")

    if max_price is not None:
        all_results = [r for r in all_results if r["price"] <= max_price]
    if min_price is not None:
        all_results = [r for r in all_results if r["price"] >= min_price]

    deduped = _dedupe(all_results)
    ranked = sorted(deduped, key=lambda r: r["price"])

    return {"ranked_results": ranked}
