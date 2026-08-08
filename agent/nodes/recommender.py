"""Node: generate a human-readable recommendation from the ranked results."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import get_llm
from agent.state import AgentState

SYSTEM_PROMPT = """You are a helpful shopping assistant having a conversation
with a user. You will be given the user's original request and a ranked list
of matching products (cheapest first) with their platform, price, and rating.

Write a short (3-5 sentence) recommendation in plain conversational English:
- Name the best overall pick, not necessarily the absolute cheapest if a
  slightly pricier option has a notably better rating.
- Mention the price and platform of your pick.
- Briefly note one or two cheaper or notable alternatives if relevant.

STRICT RULES:
- Respond ONLY with plain prose sentences. Do not write any code, functions,
  pseudocode, or code blocks under any circumstances.
- Do not use markdown headers, bullet points, or backticks.
- This is a conversational answer for a shopping app UI, not a programming
  task -- there is no code to write here, only a recommendation to explain
  in words.

Example of the expected style:
"The Roadster Men's Casual Shirt on Amazon is the best pick at ₹823.92 -- it's
the cheapest option and still has a solid 4.2 rating. If you don't mind
paying a bit more, the Flipkart listing at ₹899 has slightly faster delivery
reviews. Everything else in the results was priced notably higher for a
similar product."
"""

_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_CODE_SIGNAL_RE = re.compile(r"\b(def |class |import |return\s)", re.IGNORECASE)

_FALLBACK_TEMPLATE = (
    "Based on the comparison, **{title}** on **{platform}** is the lowest-priced "
    "match at ₹{price:,.2f}. Check the table above for other platform options."
)


def _looks_like_code(text: str) -> bool:
    return bool(_CODE_BLOCK_RE.search(text) or _CODE_SIGNAL_RE.search(text))


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

    llm = get_llm(temperature=0.2)
    payload = json.dumps(ranked[:10], indent=2)
    user_msg = (
        f"User request: {query}\n\n"
        f"Ranked results (cheapest first):\n{payload}\n\n"
        "Remember: respond with a short plain-English recommendation only. "
        "No code."
    )

    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)]
    )
    text = response.content.strip()

    # Safety net: some local models ignore the "no code" instruction on
    # certain prompts. If the response still looks like code, fall back to a
    # simple templated sentence instead of showing code in the UI.
    if _looks_like_code(text):
        cheapest = ranked[0]
        text = _FALLBACK_TEMPLATE.format(
            title=cheapest["title"], platform=cheapest["platform"].title(), price=cheapest["price"]
        )

    return {"final_recommendation": text}