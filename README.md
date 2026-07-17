# DocPilot — Enterprise AI Knowledge Assistant

AI-powered assistant that answers questions from internal company documents (technical manuals, SOPs, reports) with natural language, source citations, and multi-turn conversation.

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

   ┌──────────────── CHAT (M4) ───────────────────┐
   │ Top chunks + query → Ollama → answer + cites │
   └───────────────────────────────────────────────┘

   ┌─────────── LANGGRAPH AGENT (M5) ─────────────┐
   │ Load history → Rewrite query (if follow-up)  │
   │ → Retrieve → Stream answer → Save history    │
   └───────────────────────────────────────────────┘
```

**Two-stage retrieval:** hybrid search (semantic + BM25) returns top 20 → cross-encoder reranker narrows to top 5. Why? Stage 1 is fast and casts a wide net (high recall). Stage 2 is slower but far more accurate (high precision). Together they beat either approach alone.

**Agentic orchestration:** LangGraph wraps the RAG pipeline with conversation state — loads chat history, rewrites ambiguous follow-ups as standalone queries, retrieves, streams the answer, and persists the turn to PostgreSQL.

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
| M5 | ✅ Done | Agentic layer (LangGraph) — multi-turn chat, query rewriting, session management |
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
│   ├── reranker.py      # Cross-encoder reranker (sentence-transformers)
│   └── agent.py         # LangGraph agent (history, rewrite, orchestrate)
├── api/
│   ├── health.py        # /health endpoint (checks all services)
│   ├── documents.py     # Document CRUD + upload endpoints
│   ├── search.py        # POST /search — hybrid search + reranker
│   └── chat.py          # POST /chat — streaming LLM with citations
├── schemas/
│   └── document.py      # Pydantic models
└── docs/
    ├── architecture.mmd  # Mermaid architecture diagram
    └── complete-flow.mmd # Full M1-M5 flow diagram
```

## License

MIT
