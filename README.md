# DocPilot — Enterprise AI Knowledge Assistant

AI-powered assistant that answers questions from internal company documents (technical manuals, SOPs, reports) with natural language and source citations.

## Architecture

```
   ┌────────────────── INGESTION ──────────────────┐
   │ PDF Upload → Text Extract → Chunk → Embed →  │
   │           Qdrant (vectors + text)             │
   │           PostgreSQL (doc metadata)           │
   └───────────────────────────────────────────────┘

   ┌─────────────────── SEARCH ────────────────────┐
   │ Query → OpenAI Embed → Qdrant Hybrid Search  │
   │         (dense + BM25, RRF fusion)            │
   │              → Cross-Encoder Reranker         │
   │              → Top 5 ranked chunks            │
   └───────────────────────────────────────────────┘

   ┌────────────────── CHAT (M4) ──────────────────┐
   │ Top chunks + query → LLM → answer + citations │
   └───────────────────────────────────────────────┘
```

**Two-stage retrieval:** hybrid search (semantic + BM25) returns top 20 → cross-encoder reranker narrows to top 5. Why? Stage 1 is fast and casts a wide net (high recall). Stage 2 is slower but far more accurate (high precision). Together they beat either approach alone.

## Tech Stack

| Component | Choice |
|-----------|--------|
| API | FastAPI |
| Vector DB | Qdrant (self-hosted, open-source) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Reranking | BAAI/bge-reranker-v2-m3 |
| LLM | Ollama (local, self-hosted) |
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
| M2 | ✅ Done | Document ingestion — PDF upload, extract, chunk, embed, store |
| M3 | ✅ Done | Core RAG pipeline — hybrid search + reranker |
| M4 | ✅ Done | Chat API with streaming LLM (Ollama) + citations |
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
│   ├── logging.py       # loguru (structured JSON logging)
│   ├── db.py            # PostgreSQL connection pool + schema
│   ├── qdrant.py        # Qdrant client (collection, upsert, delete)
│   ├── storage.py       # PDF extraction + text chunking
│   ├── embeddings.py    # OpenAI embedding client
│   ├── llm.py           # Ollama streaming client + prompt builder
│   └── reranker.py      # Cross-encoder reranker (sentence-transformers)
├── api/
│   ├── health.py        # /health endpoint (checks all services)
│   ├── documents.py     # Document CRUD + upload endpoints
│   ├── search.py        # POST /search — hybrid search + reranker
│   └── chat.py          # POST /chat — streaming LLM with citations
├── schemas/
│   └── document.py      # Pydantic models
└── docs/
    ├── architecture.mmd  # Mermaid architecture diagram
    └── docpilot-flow.mmd # Full M1-M2-M3 flow diagram
```

## License

MIT
