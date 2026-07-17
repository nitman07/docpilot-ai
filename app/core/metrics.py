from prometheus_client import Counter, Histogram, Gauge, generate_latest

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

rag_retrieval_latency_seconds = Histogram(
    "rag_retrieval_latency_seconds", "RAG retrieval latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

rag_reranker_latency_seconds = Histogram(
    "rag_reranker_latency_seconds", "RAG reranker latency in seconds",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

rag_llm_latency_seconds = Histogram(
    "rag_llm_latency_seconds", "RAG LLM generation latency in seconds",
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

rag_chunks_retrieved = Histogram(
    "rag_chunks_retrieved", "Number of chunks retrieved per query",
    buckets=(1, 2, 3, 4, 5, 10, 20),
)

rag_zero_result = Counter(
    "rag_zero_result_total", "Total queries with zero chunks retrieved",
)

rag_avg_reranker_score = Histogram(
    "rag_avg_reranker_score", "Average reranker score per query",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

documents_count = Gauge("documents_total", "Total number of documents indexed")
chunks_count = Gauge("chunks_total", "Total number of chunks in Qdrant")
active_sessions = Gauge("active_sessions", "Number of active chat sessions")


def get_metrics():
    return generate_latest()
