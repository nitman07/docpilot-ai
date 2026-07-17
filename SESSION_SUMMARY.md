# DocPilot — Enterprise AI Knowledge Assistant

## Project
AI-powered enterprise assistant for querying internal company documents (technical manuals, SOPs, reports, etc.) using natural language with citations.

## Repo Name
`docpilot` or `docpilot-ai`

## Tech Stack
| Component | Choice |
|-----------|--------|
| Vector DB | Qdrant |
| Embeddings | OpenAI text-embedding-3-small |
| Reranking | Cross-encoder (BAAI/bge-reranker-v2-m3) |
| LLM | Self-hosted via Ollama (dev) / vLLM (prod) |
| API Framework | FastAPI |
| Agent Orchestration | LangGraph |
| Relational DB | PostgreSQL |
| Cache / Queue | Redis |
| Experiment Tracking | MLflow |
| Monitoring | Prometheus + Grafana |
| Tracing | OpenTelemetry |
| Containerization | Docker + Kubernetes |
| CI/CD | GitHub Actions |

## Key Architecture Decisions

### Qdrant Stores Both Vectors AND Chunk Text
- Each Qdrant point has: vector + payload with chunk_text, document_id, page, doc_name
- Avoids N+1 query — no extra PostgreSQL lookup per chunk
- PostgreSQL stores document-level metadata only

### Embeddings vs LLM
- OpenAI for embeddings (safe — can't reverse embeddings to text, cheap, high quality)
- Self-hosted LLM for generation (data sovereignty)

### RAG Two-Stage Retrieval
1. Qdrant hybrid search (dense + BM25) on all chunks → top 20
2. Cross-encoder reranker → top 5

## Milestones

### M1: Foundation & Infrastructure
Docker Compose with FastAPI, Qdrant, PostgreSQL, Redis. Health checks, config, logging.

### M2: Document Ingestion Pipeline
Upload → extract → chunk → embed → store. APIs for document CRUD.

### M3: Core RAG Pipeline (Retrieval Only)
Hybrid search → reranker → ranked results with scores.

### M4: Chat API with LLM
Streaming chat with RAG + citations, conversation history.

### M5: Agentic Layer (LangGraph)
Supervisor agent, sub-agents, multi-hop retrieval, tool calling.

### M6: Authentication & Authorization
OAuth2, JWT, RBAC, document-level permissions, audit logging.

### M7: Observability, Monitoring & Evaluation
MLflow tracking, Prometheus/Grafana, RAG evaluation suite.

### M8: Production Hardening & Deployment
Kubernetes, Helm, CI/CD, load testing, security hardening.

## Other Files
- `architecture.mmd` — Mermaid flowchart source
- `SESSION_SUMMARY.md` — This file
