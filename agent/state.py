"""Shared state schema passed between LangGraph nodes."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class ParsedFilters(TypedDict, total=False):
    product: str          # normalized product name / keywords, e.g. "wireless earbuds"
    max_price: float | None
    min_price: float | None
    category: str | None  # e.g. "electronics", "fashion"
    raw_query: str


class ProductResult(TypedDict):
    title: str
    price: float
    url: str
    platform: str          # "amazon" | "flipkart" | "myntra" | "ajio"
    rating: float | None


class AgentState(TypedDict, total=False):
    # input
    query: str

    # after query_parser
    parsed_filters: ParsedFilters

    # after search_* nodes (each node writes to its own key so they can
    # run in parallel without clobbering each other)
    amazon_results: list[ProductResult]
    flipkart_results: list[ProductResult]
    myntra_results: list[ProductResult]
    ajio_results: list[ProductResult]

    # after aggregator
    ranked_results: list[ProductResult]

    # after recommender
    final_recommendation: str

    # collected non-fatal errors, e.g. one platform search failing.
    # Annotated with operator.add so parallel nodes can each append to this
    # list without LangGraph raising a concurrent-write conflict.
    errors: Annotated[list[str], operator.add]
