"""Node: generate a human-readable recommendation from the ranked results."""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm
from agent.state import AgentState

SYSTEM_PROMPT = """You are a helpful shopping assistant. You will be given a
user's original request and a ranked list of matching products (cheapest
first) with their platform, price, and rating. Write a short (3-5 sentence)
recommendation:
- Name the best overall pick, not necessarily the absolute cheapest if a
  slightly pricier option has a notably better rating.
- Mention the price and platform of your pick.
- Briefly note one or two cheaper or notable alternatives if relevant.
Keep it conversational and concise. Do not use markdown headers.
"""


def recommender_node(state: AgentState) -> dict:
    ranked = state.get("ranked_results", [])
    query = state.get("query", "")

    if not ranked:
        return {
            "final_recommendation": (
                "No matching products were found across the connected platforms. "
                "Try broadening your search terms or budget."
            )
        }

    llm = get_llm()
    payload = json.dumps(ranked[:10], indent=2)
    user_msg = f"User request: {query}\n\nRanked results (cheapest first):\n{payload}"

    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)]
    )

    return {"final_recommendation": response.content}
