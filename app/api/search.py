from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.core.embeddings import embed_texts
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
async def search(req: SearchRequest) -> SearchResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Search query: {req.query[:100]}")

    embeddings = embed_texts([req.query])
    query_vector = embeddings[0]

    scored_points = hybrid_search(req.query, query_vector, limit=20)

    if not scored_points:
        return SearchResponse(query=req.query, results=[])

    chunks = [
        {
            "chunk_text": p.payload["chunk_text"],
            "document_id": p.payload["document_id"],
            "doc_name": p.payload["doc_name"],
            "chunk_index": p.payload.get("chunk_index", 0),
            "score": p.score,
        }
        for p in scored_points
    ]

    ranked = rerank(req.query, chunks, top_k=req.top_k)

    return SearchResponse(
        query=req.query,
        results=[SearchResultItem(**r) for r in ranked],
    )
