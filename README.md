# DocPilot — Enterprise AI Knowledge Assistant

> **An end-to-end production-grade RAG system** — upload PDFs, ask questions in natural language, get cited answers with streaming. Built from scratch across 8 milestones: from a FastAPI prototype to a Kubernetes-deployed, monitored, and hardened AI platform.

---

## What It Does

DocPilot ingests enterprise documents (technical manuals, SOPs, reports) and lets users ask natural-language questions. The system retrieves relevant chunks via hybrid search, re-ranks them for precision, and streams a cited answer from a local LLM — all with multi-turn conversation, authentication, and full observability.

```
User: "What is the procedure for O-ring replacement on the Falcon 9?"
AI:   "The O-ring replacement procedure is outlined in Section 4.2 [1]. 
       Steps include: depressurize the pneumatic system [2], remove the 
       retaining clip [3], and inspect the seal surface for cracks [4]."
```

---

## Architecture (M1–M8)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INGRESS (nginx)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                            FastAPI (Uvicorn)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ /health  │  │ /auth/*  │  │ /documents│  │ /search  │  │   /chat      │ │
│  │          │  │ JWT+bcryp│  │   upload  │  │ hybrid   │  │ LangGraph    │ │
│  │          │  │ RBAC     │  │   list    │  │ +reranker│  │ Agent + SS   │E│
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └───────┬───────┘ │
│                                                                    │         │
│  Prometheus ◄──── /metrics (middleware on every request)           │         │
└────────────────────────────────────────────────────────────────────┼─────────┘
                                    │
                           ┌────────┼────────┬──────────────────┐
                           ▼        ▼        ▼                  ▼
                     ┌──────────┐ ┌──────┐ ┌──────┐     ┌──────────────┐
                     │  Qdrant  │ │Postgr│ │ Redis│     │    Ollama    │
                     │ vectors+ │ │meta, │ │cache,│     │ llama3.2:3b  │
                     │  payload │ │users,│ │rate  │     │  (streaming) │
                     │          │ │ hist │ │limit │     │              │
                     └──────────┘ └──────┘ └──────┘     └──────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  Observability: Prometheus + Grafana (real-time) │ MLflow (offline eval)   │
│  Deployment: Docker Compose (dev) → Helm on K8s (prod)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Problem | Solution | Why |
|---|---|---|
| **Retrieval quality** | Hybrid search (dense + BM25) + Cross-encoder reranker | Stage 1 casts a wide net (recall), Stage 2 re-ranks (precision). Together beats either alone by 15-20% |
| **Data privacy** | Self-hosted LLM (Ollama) + local reranker | Sensitive documents never leave the infrastructure |
| **Multi-turn chat** | LangGraph agent with query rewriting | Ambiguous follow-ups ("what about the experience?") get rewritten as standalone queries before retrieval |
| **Auth** | JWT (access + refresh tokens) + bcrypt + RBAC | Stateless, secure, no external IdP needed |
| **Production readiness** | Multi-stage Docker → Kind → Helm → CI/CD | From local dev to K8s with auto-healing, HPA, rolling updates |
| **Monitoring** | Prometheus + Grafana (real-time) + MLflow (offline eval) | Track latency/quality live; compare experiment runs to tune parameters |

---

## Tech Stack

| Category | Choice | Why |
|---|---|---|
| **API** | FastAPI (Python 3.12) | Async, auto-docs, fast |
| **Vector DB** | Qdrant 1.9 (self-hosted) | Open-source, Rust, built-in hybrid search, no vendor lock-in |
| **Embeddings** | OpenAI `text-embedding-3-small` | 1536d, $0.13/1M tokens, state-of-the-art |
| **Reranker** | `BAAI/bge-reranker-v2-m3` | Cross-encoder, runs locally (no API cost) |
| **LLM** | Ollama + `llama3.2:3b` | Self-hosted, 30+ tok/s on M-series, data stays on-prem |
| **Orchestration** | LangGraph | Stateful DAG with conditional routing and checkpointing |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | Stateless, RBAC-ready (admin/user) |
| **Databases** | PostgreSQL 16 + Redis 7 | Metadata/history + caching/rate-limiting |
| **Observability** | Prometheus + Grafana + MLflow | Real-time dashboards + offline experiment tracking |
| **Containerization** | Docker Compose → Kubernetes (Kind) → Helm | Dev-to-prod pipeline |
| **CI/CD** | GitHub Actions | Lint → test → build → deploy |

---

## Milestones

| # | Milestone | What Was Built |
|---|-----------|----------------|
| M1 | **Foundation** | FastAPI app, Docker Compose, Qdrant + PostgreSQL + Redis, health checks |
| M2 | **Ingestion Pipeline** | PDF upload (`pdfplumber`), tiktoken chunking (512/50), OpenAI embed, store in Qdrant + PG |
| M3 | **Core RAG Pipeline** | Hybrid search (dense + BM25, RRF fusion), cross-encoder reranker, top-5 retrieval |
| M4 | **Chat API** | Streaming from Ollama, citation prompting, `StreamingResponse` |
| M5 | **LangGraph Agent** | StateGraph with history loading, query rewriting, retrieval, session persistence |
| M6 | **Auth & RBAC** | JWT access/refresh tokens, bcrypt hashing, `Depends(get_current_user)`, admin seeding |
| M7 | **Observability** | Prometheus metrics (RAG latency, chunk counts, zero-result rate), Grafana dashboard, MLflow tracking |
| M8 | **Production Deployment** | Multi-stage Dockerfile, K8s manifests (7 services), Helm chart, GitHub Actions CI/CD, rate limiting, backups |

> Each milestone is tagged (`M1`–`M8`) — explore the evolution commit by commit.

---

## Quick Start

### Local (Docker Compose)

```bash
docker compose up --build
curl http://localhost:8000/health
```

Requires: Docker, an OpenAI API key, and Ollama running locally with `llama3.2:3b`.

### Kubernetes (Kind)

```bash
kind create cluster --config kind-config.yaml
kubectl apply -k k8s/
```

Or via Helm:

```bash
helm dependency update helm/docpilot
helm install docpilot ./helm/docpilot
```

---

## Project Structure

```
app/
├── main.py                 # FastAPI entry point, middleware, lifespan
├── core/
│   ├── config.py           # pydantic-settings (env-based config)
│   ├── logging.py          # loguru structured logging
│   ├── db.py               # PostgreSQL pool, schema, queries, Redis client
│   ├── auth.py             # JWT create/verify, bcrypt, get_current_user
│   ├── qdrant.py           # Qdrant client, hybrid search, upsert/delete
│   ├── storage.py          # PDF extraction (pdfplumber), tiktoken chunking
│   ├── embeddings.py       # OpenAI embedding client
│   ├── llm.py              # Ollama streaming client + prompt builder
│   ├── reranker.py         # Cross-encoder reranker (sentence-transformers)
│   ├── agent.py            # LangGraph agent (load_history → rewrite → retrieve)
│   ├── metrics.py          # Prometheus metric definitions
│   ├── tracker.py          # MLflow logging (params, metrics, artifacts)
│   └── ratelimit.py        # Redis-backed token bucket rate limiter
├── api/
│   ├── auth.py             # /auth/register, /login, /refresh, /me
│   ├── health.py           # /health (Qdrant, PG, Redis checks)
│   ├── documents.py        # /documents CRUD + upload
│   ├── search.py           # /search (hybrid search + reranker)
│   └── chat.py             # /chat (LangGraph agent + streaming)
├── schemas/
│   └── document.py         # Pydantic models
├── k8s/                    # Kubernetes manifests (all services)
├── helm/docpilot/          # Helm chart (values.yaml, 10 templates)
├── prometheus/             # Prometheus scrape config
├── grafana/                # Grafana auto-provisioning + dashboard
└── .github/workflows/      # CI/CD pipelines
```

---

## What Makes This Project Stand Out

- **Production-grade** — not a toy. Includes auth, rate limiting, CORS hardening, health probes, HPA, backups, and a Helm chart for real deployment.
- **Eight milestones** — each building on the last, from a basic API to a full K8s-deployed platform. Shows ability to scope, plan, and execute iteratively.
- **Deep trade-off reasoning** — every choice (Qdrant vs Pinecone, hybrid vs pure dense, LangGraph vs chain, JWT vs OAuth2) has documented rationale. Not cargo-culted.
- **Observability from day one** — Prometheus metrics on every request, Grafana dashboards, MLflow experiment tracking. Built to be operated, not just developed.
- **Interview-ready** — 350+ lines of interview Q&A in [`INTERVIEW_QA.md`](INTERVIEW_QA.md) covering architecture, ingestion, retrieval, chat, agents, auth, and production deployment.

---

## License

MIT
