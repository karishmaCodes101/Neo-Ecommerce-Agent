"""Build and compile the LangGraph agent.

Flow:
    query_parser
        -> (parallel) search_amazon, search_flipkart, search_myntra, search_ajio
        -> aggregator
        -> recommender
        -> END
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.nodes.aggregator import aggregator_node
from agent.nodes.query_parser import query_parser_node
from agent.nodes.recommender import recommender_node
from agent.nodes.search_ajio import search_ajio_node
from agent.nodes.search_amazon import search_amazon_node
from agent.nodes.search_flipkart import search_flipkart_node
from agent.nodes.search_myntra import search_myntra_node
from agent.state import AgentState

_SEARCH_NODES = {
    "search_amazon": search_amazon_node,
    "search_flipkart": search_flipkart_node,
    "search_myntra": search_myntra_node,
    "search_ajio": search_ajio_node,
}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("query_parser", query_parser_node)
    for name, fn in _SEARCH_NODES.items():
        graph.add_node(name, fn)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("recommender", recommender_node)

    graph.set_entry_point("query_parser")

    # Fan out from query_parser to all four platform searches in parallel
    for name in _SEARCH_NODES:
        graph.add_edge("query_parser", name)

    # Fan in: aggregator waits for all four search nodes to complete
    for name in _SEARCH_NODES:
        graph.add_edge(name, "aggregator")

    graph.add_edge("aggregator", "recommender")
    graph.add_edge("recommender", END)

    return graph.compile()


# Module-level compiled graph, built once and reused across Streamlit reruns.
compiled_graph = build_graph()


def run_agent(query: str) -> AgentState:
    """Convenience entrypoint: run the full graph for a user query."""
    initial_state: AgentState = {"query": query, "errors": []}
    return compiled_graph.invoke(initial_state)
