from agent.nodes.aggregator import aggregator_node


def _product(title, price, platform, rating=4.0):
    return {"title": title, "price": price, "url": f"https://{platform}.example.com", "platform": platform, "rating": rating}


def test_sorts_by_price_ascending():
    state = {
        "amazon_results": [_product("Wireless Earbuds X1", 1500, "amazon")],
        "flipkart_results": [_product("Wireless Earbuds X1", 1200, "flipkart")],
        "myntra_results": [],
        "ajio_results": [],
        "parsed_filters": {},
    }
    out = aggregator_node(state)
    prices = [r["price"] for r in out["ranked_results"]]
    assert prices == sorted(prices)


def test_dedupes_near_identical_titles_keeping_cheapest():
    state = {
        "amazon_results": [_product("Sony WF-C500 Truly Wireless Earbuds", 5200, "amazon")],
        "flipkart_results": [_product("Sony WF-C500 Truly Wireless Earbuds", 4800, "flipkart")],
        "myntra_results": [],
        "ajio_results": [],
        "parsed_filters": {},
    }
    out = aggregator_node(state)
    assert len(out["ranked_results"]) == 1
    assert out["ranked_results"][0]["price"] == 4800
    assert out["ranked_results"][0]["platform"] == "flipkart"


def test_applies_max_price_filter():
    state = {
        "amazon_results": [_product("Cheap Item", 500, "amazon"), _product("Pricey Item", 5000, "amazon")],
        "flipkart_results": [],
        "myntra_results": [],
        "ajio_results": [],
        "parsed_filters": {"max_price": 1000},
    }
    out = aggregator_node(state)
    assert len(out["ranked_results"]) == 1
    assert out["ranked_results"][0]["title"] == "Cheap Item"
