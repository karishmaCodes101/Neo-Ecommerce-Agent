"""Streamlit entrypoint for the Ecom Price Agent."""

from __future__ import annotations

import logging
import os

import streamlit as st
from dotenv import load_dotenv

from agent.graph import compiled_graph

load_dotenv()

# Configure logging so DDG/SerpAPI request logs from agent/nodes/*.py show up
# in your terminal (Streamlit runs your script in a normal Python process --
# these logs print wherever you launched `streamlit run app.py` from, not in
# the browser). Set LOG_LEVEL=DEBUG in .env for more verbose output.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

st.set_page_config(page_title="NEO - Ecom Price Agent", page_icon="🛒", layout="wide")

# --- Sidebar: LLM provider selection -----------------------------------
st.sidebar.header("Settings")

default_provider = os.getenv("LLM_PROVIDER", "ollama")
provider = st.sidebar.selectbox(
    "LLM provider",
    options=["ollama", "openai"],
    index=0 if default_provider == "ollama" else 1,
    help="Ollama runs locally, no API key needed. OpenAI needs OPENAI_API_KEY in your .env.",
)
# Override env var for this session so agent/llm.py picks it up
os.environ["LLM_PROVIDER"] = provider

if provider == "ollama":
    st.sidebar.caption(
        f"Using local model: `{os.getenv('OLLAMA_MODEL', 'llama3')}` "
        f"via {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}. "
        "Make sure `ollama serve` is running."
    )
else:
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    st.sidebar.caption(f"Using model: `{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}`")
    if not has_key:
        st.sidebar.warning("OPENAI_API_KEY not set in .env — add it or switch to Ollama.")

st.sidebar.divider()
st.sidebar.caption(
    "Platform search is currently backed by mock data for development. "
    "See README.md 'Next steps' to wire up real sources."
)

# --- Main UI --------------------------------------------------------------
st.title("🛒 NEO - Ecom Price Agent")
st.write(
    "Ask for a product and I'll compare mock listings across Amazon, Flipkart, "
    "Myntra, and Ajio, then recommend the best value."
)

query = st.text_input(
    "What are you shopping for?",
    placeholder="e.g. wireless earbuds under 2000",
)
search_clicked = st.button("Search", type="primary")

if search_clicked:
    if not query.strip():
        st.warning("Enter a product to search for.")
    else:
        with st.spinner("Comparing prices across platforms..."):
            try:
                result = compiled_graph.invoke({"query": query, "errors": []})
            except Exception as exc:  # noqa: BLE001
                st.error(f"Something went wrong: {exc}")
                result = None

        if result:
            errors = result.get("errors", [])
            for err in errors:
                st.warning(err)

            ranked = result.get("ranked_results", [])
            if ranked:
                st.subheader("Comparison")
                st.dataframe(
                    [
                        {
                            "Platform": r["platform"].title(),
                            "Product": r["title"],
                            "Price (₹)": r["price"],
                            "Rating": r["rating"],
                            "Link": r["url"],
                        }
                        for r in ranked
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                cheapest = ranked[0]
                st.success(
                    f"Lowest price: **{cheapest['title']}** on "
                    f"**{cheapest['platform'].title()}** for **₹{cheapest['price']:,.2f}**"
                )

                st.subheader("Recommendation")
                st.write(result.get("final_recommendation", ""))
            else:
                st.info("No matching products found. Try a different search or budget.")