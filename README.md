# DocPilot — Enterprise AI Knowledge Assistant

AI-powered assistant that answers questions from internal company documents (technical manuals, SOPs, reports) with natural language and source citations.

## Architecture

```
User → FastAPI → LangGraph (agent orchestration)
                    ├── Qdrant (vector search — hybrid dense + BM25)
                    ├── PostgreSQL (document metadata)
                    └── Redis (cache / session state)
```

Two-stage retrieval: **hybrid search** (semantic + keyword) returns top 20 chunks → **cross-encoder reranker** narrows to top 5 → LLM generates answer with citations.

## Tech Stack

| Component | Choice |
|-----------|--------|
| API | FastAPI |
| Vector DB | Qdrant (self-hosted, open-source) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Reranking | BAAI/bge-reranker-v2-m3 |
| LLM | Ollama (dev) / vLLM (prod) |
| Orchestration | LangGraph |
| Relational DB | PostgreSQL |
| Cache / Queue | Redis |
| Containerization | Docker Compose / Kubernetes |

## Quick Start

```bash
docker compose up --build
curl http://localhost:8000/health
```

See [`docker-compose.yml`](docker-compose.yml) for service configuration.

## Milestones

| # | Status | Feature |
|---|--------|---------|
| M1 | ✅ Done | Foundation — FastAPI, Docker Compose, Qdrant, PostgreSQL, Redis, health checks |
| M2 | 🔄 Next | Document ingestion — upload, extract, chunk, embed, store |
| M3 | ❌ | Core RAG pipeline — hybrid search + reranker |
| M4 | ❌ | Chat API with streaming LLM + citations |
| M5 | ❌ | Agentic layer (LangGraph) |
| M6 | ❌ | Auth (OAuth2, JWT, RBAC) |
| M7 | ❌ | Observability (MLflow, Prometheus, Grafana) |
| M8 | ❌ | Production deployment (K8s, Helm, CI/CD) |

## Project Structure

```
app/
├── main.py              # FastAPI entrypoint
├── core/
│   ├── config.py        # pydantic-settings (env-based config)
│   └── logging.py       # loguru (structured JSON logging)
└── api/
    └── health.py        # /health endpoint (checks all services)
```

## License

MIT
