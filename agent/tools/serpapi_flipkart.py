"""Real Flipkart product search via SerpAPI.

SerpAPI (https://serpapi.com) proxies Google Search results, which is a
practical way to get live-ish Flipkart listings without violating Flipkart's
own Terms of Service by scraping it directly. This uses the plain `google`
engine with a `site:flipkart.com` filter on the query, then extracts price
from each organic result's title/snippet text (Google's regular search
results don't carry structured price fields the way Shopping results do,
so this is best-effort parsing, not guaranteed-accurate pricing).

Requires a SERPAPI_KEY -- there is no keyless/anonymous tier; api_key is a
required parameter on every SerpAPI request regardless of engine.

This is intentionally isolated in its own module so it can be swapped out
later (e.g. for the google_shopping engine, a different aggregator, or a
licensed data feed) without touching the LangGraph node that calls it.
"""

from __future__ import annotations

import os
import re

import requests

from agent.state import ProductResult

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
_PRICE_RE = re.compile(r"(?:\u20b9|Rs\.?)\s?([\d,]+(?:\.\d+)?)", re.IGNORECASE)


def _parse_price(raw: str | float | int | None) -> float | None:
    """SerpAPI shopping results usually give price as a string like '₹1,299'."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    match = _PRICE_RE.search(str(raw))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_price_from_result(item: dict) -> float | None:
    """Google organic results don't have a structured price field -- pull the
    first price-looking figure out of the title, snippet, or rich snippet
    extensions, in that order."""
    candidates = [item.get("title", ""), item.get("snippet", "")]
    rich = item.get("rich_snippet", {}) or {}
    candidates.append(str(rich))  # cheap way to sweep any nested price text

    for text in candidates:
        price = _parse_price(text)
        if price is not None:
            return price
    return None


def search_flipkart_live(product_query: str, max_results: int = 5) -> list[ProductResult]:
    """Query SerpAPI's plain Google Search engine, filtered to flipkart.com
    via a `site:` query operator, and best-effort-parse prices out of the
    organic result text.

    Raises:
        RuntimeError: if SERPAPI_KEY is not configured.
        requests.RequestException: on network/API failure (let the caller
            decide how to handle/log it).
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError(
            "SERPAPI_KEY is not set. Add it to .env, or set "
            "USE_REAL_FLIPKART=false to keep using mock data."
        )

    params = {
        "engine": "google",
        "q": f"{product_query} site:flipkart.com",
        "api_key": api_key,
    }

    response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    results: list[ProductResult] = []
    for item in data.get("organic_results", [])[:max_results]:
        price = _extract_price_from_result(item)
        if price is None:
            continue  # skip results we can't pull a usable price out of
        results.append(
            ProductResult(
                title=item.get("title", "Unknown product"),
                price=price,
                url=item.get("link", ""),
                platform="flipkart",
                rating=None,  # not reliably available from plain search results
            )
        )
    return results
