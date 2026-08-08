"""Mock product catalog.

Stands in for real scrapers / API clients so the LangGraph flow and Streamlit
UI can be built and tested end-to-end before real data sources are wired up.
Replace `search_platform()` internals (or the individual search_* nodes) with
real API/scraper calls later -- keep the same return schema.
"""

from __future__ import annotations

import random

from agent.state import ProductResult

# A small fake catalog. Each entry defines a base price; per-platform price
# variance is applied at query time so results differ across platforms, like
# real life.
_CATALOG = [
    {"title": "Boat Airdopes 141 Wireless Earbuds", "category": "electronics", "base_price": 1299, "keywords": ["wireless", "earbuds", "boat", "airdopes", "headphones"]},
    {"title": "Sony WF-C500 Truly Wireless Earbuds", "category": "electronics", "base_price": 4990, "keywords": ["wireless", "earbuds", "sony", "headphones"]},
    {"title": "OnePlus Nord Buds 2", "category": "electronics", "base_price": 1799, "keywords": ["wireless", "earbuds", "oneplus", "headphones"]},
    {"title": "Noise ColorFit Pulse Smartwatch", "category": "electronics", "base_price": 1599, "keywords": ["smartwatch", "watch", "noise", "fitness"]},
    {"title": "Fire-Boltt Phoenix Smartwatch", "category": "electronics", "base_price": 1899, "keywords": ["smartwatch", "watch", "fire-boltt", "fitness"]},
    {"title": "Levi's Men's Slim Fit Jeans", "category": "fashion", "base_price": 1999, "keywords": ["jeans", "levis", "men", "pants"]},
    {"title": "Roadster Men's Casual Shirt", "category": "fashion", "base_price": 799, "keywords": ["shirt", "roadster", "men", "casual"]},
    {"title": "Puma Men's Running Shoes", "category": "fashion", "base_price": 2499, "keywords": ["shoes", "puma", "running", "sports"]},
    {"title": "Nike Air Max Sneakers", "category": "fashion", "base_price": 6999, "keywords": ["shoes", "nike", "sneakers", "sports"]},
    {"title": "HP 15s Laptop (i5, 8GB, 512GB SSD)", "category": "electronics", "base_price": 48990, "keywords": ["laptop", "hp", "computer"]},
    {"title": "Dell Inspiron 15 Laptop (i5, 16GB, 512GB SSD)", "category": "electronics", "base_price": 54990, "keywords": ["laptop", "dell", "computer"]},
    {"title": "Samsung Galaxy M14 5G", "category": "electronics", "base_price": 12999, "keywords": ["phone", "samsung", "smartphone", "mobile"]},
    {"title": "Redmi Note 13", "category": "electronics", "base_price": 14999, "keywords": ["phone", "redmi", "xiaomi", "smartphone", "mobile"]},
]

# Rough per-platform price variance and a fixed pseudo-random seed offset so
# results are stable-ish across a single run but still differ by platform.
_PLATFORM_VARIANCE = {
    "amazon": (0.95, 1.05),
    "flipkart": (0.93, 1.08),
    "myntra": (0.97, 1.15),   # myntra skews fashion/lifestyle, less discount on electronics
    "ajio": (0.96, 1.12),
}


def search_platform(platform: str, product_query: str, max_results: int = 5) -> list[ProductResult]:
    """Return mock ProductResult entries matching `product_query` for `platform`.

    Matching is a simple keyword overlap against the mock catalog -- good
    enough to exercise the full agent graph and UI.
    """
    query_terms = {t.lower() for t in product_query.split() if len(t) > 2}
    if not query_terms:
        return []

    scored = []
    for item in _CATALOG:
        overlap = query_terms & set(item["keywords"])
        title_hit = any(term in item["title"].lower() for term in query_terms)
        if overlap or title_hit:
            scored.append((len(overlap) + (1 if title_hit else 0), item))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    low, high = _PLATFORM_VARIANCE.get(platform, (0.95, 1.10))
    results: list[ProductResult] = []
    for _, item in scored[:max_results]:
        price_multiplier = random.uniform(low, high)
        price = round(item["base_price"] * price_multiplier, 2)
        results.append(
            ProductResult(
                title=item["title"],
                price=price,
                url=f"https://{platform}.example.com/product/{item['title'].replace(' ', '-').lower()}",
                platform=platform,
                rating=round(random.uniform(3.5, 4.8), 1),
            )
        )
    return results
