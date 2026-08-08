# Ecom Price Agent

An AI shopping assistant that compares product prices across Amazon, Flipkart,
Myntra, and Ajio, and recommends the best value option.

Built with **Streamlit** (UI), **LangGraph** (agent orchestration), and a
pluggable LLM backend — switch between **OpenAI** and a **local Ollama**
model with one config flag, no code changes.

> **Status:** Scaffold stage. Platform search nodes currently return **mock
> data** so you can validate the agent graph and UI end-to-end before wiring
> up real scrapers or paid APIs (see "Next steps" below).

---

## Architecture

```
Streamlit UI (user query)
   -> LangGraph agent
        -> query_parser        (LLM: query -> structured filters)
        -> search_amazon   \
        -> search_flipkart  \  (run in parallel, currently mock data)
        -> search_myntra    /
        -> search_ajio     /
        -> aggregator          (merge, dedupe, sort by price, apply filters)
        -> recommender         (LLM: explain the best pick)
   -> Streamlit renders comparison table + recommendation
```

See `agent/graph.py` for the graph wiring and `agent/state.py` for the shared
state schema.

## Repo structure

```
ecom-price-agent/
├── app.py                     # Streamlit entrypoint
├── agent/
│   ├── state.py                # Shared LangGraph state (TypedDict)
│   ├── graph.py                 # StateGraph definition & compilation
│   ├── llm.py                    # Pluggable LLM provider (OpenAI / Ollama)
│   ├── nodes/
│   │   ├── query_parser.py
│   │   ├── search_amazon.py
│   │   ├── search_flipkart.py
│   │   ├── search_myntra.py
│   │   ├── search_ajio.py
│   │   ├── aggregator.py
│   │   └── recommender.py
│   └── tools/
│       └── mock_products.py      # Stub product catalog used by search nodes
├── tests/
│   └── test_aggregator.py
├── .env.example
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd ecom-price-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure your LLM provider

Copy the example env file:

```bash
cp .env.example .env
```

**Option A — OpenAI** (when you have a working API key):

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Option B — Local Ollama** (no API key needed, runs on your machine):

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

Install Ollama (https://ollama.com), then pull a model:

```bash
ollama pull llama3
ollama serve   # usually starts automatically after install
```

Any Ollama-supported model works — try `llama3.1`, `mistral`, or `qwen2.5`
if you want to compare quality/speed. Update `OLLAMA_MODEL` accordingly.

### 3. Run the app

```bash
streamlit run app.py
```

You can also switch providers live from the sidebar dropdown in the app —
it overrides the `.env` setting for that session.

## Next steps (real data sources)

The four `search_*` nodes in `agent/nodes/` currently return filtered mock
data from `agent/tools/mock_products.py`. To go live:

- **Amazon**: apply for Product Advertising API (PA-API) access via an
  Amazon Associates account.
- **Flipkart / Myntra / Ajio**: no public product-search APIs exist. Options:
  a paid aggregator (e.g. SerpAPI shopping results, a RapidAPI marketplace
  proxy), or a scraper (e.g. Playwright) — note scraping these sites is
  against their Terms of Service, so treat this as educational/personal use
  only, add rate-limiting, and cache aggressively.
- Keep the normalized output schema (`title`, `price`, `url`, `platform`,
  `rating`) the same so `aggregator.py` and `recommender.py` don't need to
  change when you swap mock data for real data.

## Testing

```bash
pytest tests/
```
