# Signal 📡

Autonomous market intelligence agent that continuously monitors AI/ML and Fintech domains, reasons over live signals, and produces scored intelligence reports — with zero human intervention.

## What it does
- Ingests signals every 6 hours from RSS feeds, GitHub API, and arXiv (150+ signals/run)
- Runs a LangGraph agent: Supervisor → Researcher → Analyst → Judge
- Generates structured intelligence reports scored by an LLM-as-judge
- Stores everything in DuckDB, queryable and searchable

## Stack
| Layer | Tools |
|---|---|
| Ingestion | `dlt` · `DuckDB` · RSS · GitHub API · arXiv |
| Agent | `LangGraph` · `Pydantic AI` · `Mistral` (local via Ollama) |
| Storage | `DuckDB` · `dbt` · `Qdrant` · `PostgreSQL` |
| Serving | `Next.js` · `FastAPI` |
| Observability | `LangSmith` |
| Deploy | `Modal` |

## Architecture

ngestion (dlt) → DuckDB → LangGraph Agent → Reports
↓
Supervisor → Researcher → Analyst → Judge
↑_______↓ (retry if score < 0.6)

## Running locally
```bash
# Install
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-packages

# Run ingestion
uv run python -m ingestion.pipeline

# Run agent
uv run python -m agent.runner
```

## Status
🚧 Active development — Day 3/32