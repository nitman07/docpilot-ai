from time import time

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.embeddings import embed_texts
from app.core.metrics import rag_reranker_latency_seconds, rag_retrieval_latency_seconds, rag_chunks_retrieved, rag_zero_result
from app.core.qdrant import hybrid_search
from app.core.reranker import rerank

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    chunk_text: str
    document_id: str
    doc_name: str
    chunk_index: int
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]


@router.post("", response_model=SearchResponse)
async def search(req: SearchRequest, user: dict = Depends(get_current_user)) -> SearchResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Search query: {req.query[:100]}")

    t0 = time()
    embeddings = embed_texts([req.query])
    query_vector = embeddings[0]

    scored_points = hybrid_search(req.query, query_vector, limit=20)
    retrieval_latency = time() - t0
    rag_retrieval_latency_seconds.observe(retrieval_latency)

    if not scored_points:
        rag_zero_result.inc()
        return SearchResponse(query=req.query, results=[])

    chunks = []
    for p in scored_points:
        payload = p.payload
        if payload is None:
            continue
        chunks.append({
            "chunk_text": payload["chunk_text"],
            "document_id": payload["document_id"],
            "doc_name": payload["doc_name"],
            "chunk_index": payload.get("chunk_index", 0),
            "score": p.score,
        })

    t1 = time()
    ranked = rerank(req.query, chunks, top_k=req.top_k)
    reranker_latency = time() - t1
    rag_reranker_latency_seconds.observe(reranker_latency)
    rag_chunks_retrieved.observe(len(ranked))

    return SearchResponse(
        query=req.query,
        results=[SearchResultItem(**r) for r in ranked],
    )
