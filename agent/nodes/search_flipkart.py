"""Node: search Flipkart for matching products.

Data source is controlled by FLIPKART_DATA_SOURCE in .env:
    - "duckduckgo" (default) -- keyless, scrapes DuckDuckGo HTML results
      filtered to flipkart.com. No API key needed.
    - "serpapi"    -- uses SerpAPI (requires SERPAPI_KEY), more structured
      but needs a paid/free-tier key.
    - "mock"       -- always use local mock data.

Whatever the setting, any failure falls back to mock data automatically so
the app never breaks -- a warning is surfaced in state["errors"] instead.

Logging: set LOG_LEVEL=INFO (or DEBUG) to see whether each Flipkart call
succeeded, how many results it returned, and whether/why it fell back to
mock data. See app.py for where logging is configured.
"""

from __future__ import annotations

import logging
import os

from agent.state import AgentState
from agent.tools.duckduckgo_flipkart import search_flipkart_duckduckgo
from agent.tools.mock_products import search_platform
from agent.tools.serpapi_flipkart import search_flipkart_live

logger = logging.getLogger(__name__)

_VALID_SOURCES = ("mock", "duckduckgo", "serpapi")


def _data_source() -> str:
    source = os.getenv("FLIPKART_DATA_SOURCE", "duckduckgo").lower().strip()
    return source if source in _VALID_SOURCES else "duckduckgo"


def search_flipkart_node(state: AgentState) -> dict:
    filters = state.get("parsed_filters", {})
    product = filters.get("product", state.get("query", ""))
    source = _data_source()
    logger.info("Flipkart node: source=%s product=%r", source, product)

    if source == "serpapi":
        try:
            results = search_flipkart_live(product)
            logger.info("Flipkart node: serpapi SUCCEEDED, %d results", len(results))
            return {"flipkart_results": results}
        except Exception as exc:  # noqa: BLE001 - fall back rather than fail the whole run
            logger.warning("Flipkart node: serpapi FAILED (%s), falling back to mock data", exc)
            fallback = search_platform("flipkart", product)
            return {
                "flipkart_results": fallback,
                "errors": [f"flipkart (serpapi) search failed, used mock data instead: {exc}"],
            }

    if source == "duckduckgo":
        try:
            results = search_flipkart_duckduckgo(product)
            if not results:
                logger.warning(
                    "Flipkart node: duckduckgo returned 0 usable results, falling back to mock data"
                )
                return {
                    "flipkart_results": search_platform("flipkart", product),
                    "errors": ["flipkart (duckduckgo) returned no usable results, used mock data instead"],
                }
            logger.info("Flipkart node: duckduckgo SUCCEEDED, %d results", len(results))
            return {"flipkart_results": results}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Flipkart node: duckduckgo FAILED (%s), falling back to mock data", exc)
            fallback = search_platform("flipkart", product)
            return {
                "flipkart_results": fallback,
                "errors": [f"flipkart (duckduckgo) search failed, used mock data instead: {exc}"],
            }

    # source == "mock"
    try:
        results = search_platform("flipkart", product)
        logger.info("Flipkart node: mock data, %d results", len(results))
        return {"flipkart_results": results}
    except Exception as exc:  # noqa: BLE001
        logger.error("Flipkart node: mock data generation FAILED (%s)", exc)
        return {"flipkart_results": [], "errors": [f"flipkart search failed: {exc}"]}