"""Pluggable LLM provider.

Reads LLM_PROVIDER from the environment ("openai" or "ollama") and returns a
LangChain chat model instance accordingly. Both providers implement the same
LangChain `BaseChatModel` interface, so nothing downstream needs to care
which one is active.

Usage:
    from agent.llm import get_llm
    llm = get_llm()                    # uses env config
    llm = get_llm(provider="ollama")   # explicit override (e.g. from UI)
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "smollm:135m"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
):
    """Return a configured chat model for the requested provider.

    Args:
        provider: "openai" or "ollama". Defaults to LLM_PROVIDER env var,
            falling back to "ollama" if unset (safe default with no API key
            required).
        model: Override the model name. Defaults to provider-specific env
            var, then a sane built-in default.
        temperature: Sampling temperature.
    """
    provider = (provider or os.getenv("LLM_PROVIDER") or "ollama").lower().strip()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set. "
                "Add it to your .env file, or switch to 'ollama' to run "
                "locally without an API key."
            )
        return ChatOpenAI(
            model=model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            api_key=api_key,
            temperature=temperature,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use 'openai' or 'ollama'.")
