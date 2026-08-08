"""Real-ish Flipkart product search via DuckDuckGo's HTML endpoint -- no API
key required.

DuckDuckGo's lightweight HTML results page (html.duckduckgo.com/html/) can be
queried directly with `requests` and parsed with BeautifulSoup, without any
authentication. This is lighter-weight than SerpAPI and needs zero
credentials, at the cost of being less structured/reliable: we're parsing
search-result snippet text for a price, not reading a documented JSON field.

Note: this queries a search engine's results page rather than a sanctioned,
rate-limit-guaranteed API. It's a reasonable fit for a scaffold or personal
project; for anything production-scale, a proper API (SerpAPI, a licensed
data feed, etc.) is the sturdier choice.

Isolated in its own module so it can be swapped out later without touching
the LangGraph node that calls it.
"""

from __future__ import annotations

import logging
import re

import requests
from bs4 import BeautifulSoup

from agent.state import ProductResult

logger = logging.getLogger(__name__)

DDG_HTML_ENDPOINT = "https://html.duckduckgo.com/html/"
_PRICE_RE = re.compile(r"(?:\u20b9|Rs\.?)\s?([\d,]+(?:\.\d+)?)", re.IGNORECASE)
_HEADERS = {
    # A plain browser-like UA avoids some basic bot-blocking; still may get
    # rate-limited under heavy use since there's no API key/quota involved.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _parse_price(text: str) -> float | None:
    match = _PRICE_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def search_flipkart_duckduckgo(product_query: str, max_results: int = 5) -> list[ProductResult]:
    """Query DuckDuckGo HTML results filtered to flipkart.com and best-effort
    parse a price out of each result's title/snippet text.

    Raises:
        requests.RequestException: on network failure (let the caller decide
            how to handle/log it).
    """
    query = f"{product_query} site:flipkart.com"
    logger.info("DDG Flipkart search: querying %r", query)

    params = {"q": query}
    try:
        response = requests.post(
            DDG_HTML_ENDPOINT, data=params, headers=_HEADERS, timeout=15
        )
    except requests.RequestException:
        logger.exception("DDG Flipkart search: request failed (network/timeout)")
        raise

    logger.info("DDG Flipkart search: HTTP %s from %s", response.status_code, DDG_HTML_ENDPOINT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    result_blocks = soup.select("div.result")[:max_results * 2]  # grab extra, filter below
    logger.info("DDG Flipkart search: found %d raw result blocks in HTML", len(result_blocks))

    results: list[ProductResult] = []
    skipped_no_link = 0
    skipped_no_price = 0

    for block in result_blocks:
        if len(results) >= max_results:
            break

        link_el = block.select_one("a.result__a")
        snippet_el = block.select_one("a.result__snippet, div.result__snippet")
        if not link_el:
            skipped_no_link += 1
            continue

        title = link_el.get_text(strip=True)
        url = link_el.get("href", "")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        price = _parse_price(title) or _parse_price(snippet)
        if price is None:
            skipped_no_price += 1
            continue  # skip results we can't pull a usable price out of

        results.append(
            ProductResult(
                title=title or "Unknown product",
                price=price,
                url=url,
                platform="flipkart",
                rating=None,  # not available from search snippet text
            )
        )

    logger.info(
        "DDG Flipkart search: parsed %d usable results "
        "(skipped %d with no link, %d with no parseable price)",
        len(results), skipped_no_link, skipped_no_price,
    )
    if not results:
        logger.warning(
            "DDG Flipkart search: 0 usable results for query %r -- "
            "caller will likely fall back to mock data", query
        )

    return results