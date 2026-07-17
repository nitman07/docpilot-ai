from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from app.core.embeddings import embed_texts
from app.core.llm import generate_stream
from app.core.qdrant import hybrid_search
from app.core.reranker import rerank

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("")
async def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Chat query: {req.query[:100]}")

    embeddings = embed_texts([req.query])
    query_vector = embeddings[0]

    scored_points = hybrid_search(req.query, query_vector, limit=20)

    if not scored_points:
        async def empty_stream():
            yield "I don't have enough information to answer this question."

        return StreamingResponse(empty_stream(), media_type="text/plain")

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

    return StreamingResponse(
        generate_stream(req.query, ranked),
        media_type="text/plain",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )
