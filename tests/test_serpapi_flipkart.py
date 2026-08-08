from agent.tools.serpapi_flipkart import _parse_price


def test_parses_rupee_symbol_price():
    assert _parse_price("₹1,299") == 1299.0


def test_parses_plain_number():
    assert _parse_price(4990) == 4990.0


def test_parses_decimal_price():
    assert _parse_price("Rs. 1,999.50") == 1999.50


def test_returns_none_for_unparseable():
    assert _parse_price("Contact for price") is None


def test_returns_none_for_none():
    assert _parse_price(None) is None
