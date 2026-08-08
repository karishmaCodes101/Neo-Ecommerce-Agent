from agent.tools.duckduckgo_flipkart import _parse_price


def test_parses_rupee_symbol_price():
    assert _parse_price("Buy now for ₹1,299 - Flipkart") == 1299.0


def test_parses_rs_prefix_price():
    assert _parse_price("Price: Rs. 4,990.00") == 4990.0


def test_returns_none_when_no_price_present():
    assert _parse_price("Best wireless earbuds review 2026") is None
