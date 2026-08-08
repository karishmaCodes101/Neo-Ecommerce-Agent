"""Node: parse the user's free-text query into structured filters."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm
from agent.state import AgentState, ParsedFilters

SYSTEM_PROMPT = """You are a query parser for a shopping assistant.
Given a user's shopping request, extract structured filters as JSON with
EXACTLY these keys and nothing else:

{
  "product": "<short product search phrase, e.g. 'wireless earbuds'>",
  "max_price": <number or null>,
  "min_price": <number or null>,
  "category": "<one of: electronics, fashion, home, other>"
}

Rules:
- Respond with ONLY the JSON object, no markdown fences, no commentary.
- If no budget is mentioned, use null for max_price/min_price.
- Prices are in Indian Rupees (assume no currency symbol needed).
"""


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction in case the model wraps it in prose/fences."""
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON in model output: {text!r}")
    return json.loads(match.group(0))


def query_parser_node(state: AgentState) -> dict:
    query = state["query"]
    llm = get_llm()

    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=query)]
    )

    try:
        parsed = _extract_json(response.content)
    except (ValueError, json.JSONDecodeError):
        # Fall back to a permissive default so the graph can still proceed
        parsed = {"product": query, "max_price": None, "min_price": None, "category": "other"}

    filters: ParsedFilters = {
        "product": parsed.get("product") or query,
        "max_price": parsed.get("max_price"),
        "min_price": parsed.get("min_price"),
        "category": parsed.get("category"),
        "raw_query": query,
    }
    return {"parsed_filters": filters}
