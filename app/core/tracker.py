from datetime import datetime, timezone

import mlflow
from loguru import logger

from app.core.config import settings

_run_started = False


def start_tracking():
    global _run_started
    if _run_started:
        return
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    mlflow.start_run(run_name=f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}")
    mlflow.log_params({
        "ollama_model": settings.ollama_model,
        "reranker_model": settings.reranker_model,
        "embedding_model": "text-embedding-3-small",
        "chunk_size": 512,
        "chunk_overlap": 50,
        "top_k": 5,
        "hybrid_search_limit": 20,
    })
    _run_started = True
    logger.info("MLflow tracking started")


def stop_tracking():
    global _run_started
    if _run_started:
        mlflow.end_run()
        _run_started = False
        logger.info("MLflow tracking ended")


def log_query(query: str, rewritten: str | None, chunks: list[dict],
              retrieval_latency: float, reranker_latency: float, llm_latency: float,
              response: str):
    if not _run_started:
        return
    metrics = {
        "retrieval_latency_ms": retrieval_latency * 1000,
        "reranker_latency_ms": reranker_latency * 1000,
        "llm_latency_ms": llm_latency * 1000,
        "chunks_retrieved": len(chunks),
    }
    if chunks:
        avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
        metrics["avg_reranker_score"] = avg_score
    else:
        metrics["zero_result"] = 1

    mlflow.log_metrics(metrics)

    mlflow.log_text(
        f"Query: {query}\n"
        f"Rewritten: {rewritten or 'N/A'}\n"
        f"Response: {response}\n\n"
        f"Chunks:\n" + "\n---\n".join(
            f"[{c.get('chunk_index', '?')}] (score={c.get('score', 0):.3f}) {c.get('chunk_text', '')[:200]}"
            for c in chunks
        ),
        f"queries/query-{datetime.now(timezone.utc).timestamp()}.txt",
    )
