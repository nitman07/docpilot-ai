import uuid
from time import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from app.core.agent import build_agent
from app.core.auth import get_current_user
from app.core.db import save_chat_turn
from app.core.llm import generate_stream
from app.core.metrics import rag_avg_reranker_score, rag_chunks_retrieved, rag_llm_latency_seconds, rag_zero_result
from app.core.tracker import log_query

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None
    top_k: int = 5


@router.post("")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())
    is_new = req.session_id is None

    logger.info(f"Chat [{session_id[:8]}]: {req.query[:100]}")

    t0 = time()
    agent = build_agent()

    result = await agent.ainvoke({
        "session_id": session_id,
        "query": req.query,
        "history": [],
        "rewritten_query": None,
        "chunks": [],
        "quality_ok": False,
        "retry_count": 0,
    })
    retrieval_latency = time() - t0

    chunks = result.get("chunks", [])
    rewritten = result.get("rewritten_query")

    if chunks:
        rag_chunks_retrieved.observe(len(chunks))
        avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
        rag_avg_reranker_score.observe(avg_score)
    else:
        rag_zero_result.inc()

    async def response_stream():
        yield f"__session__:{session_id}\n"
        if is_new:
            yield f"__new__:true\n"
        if rewritten and rewritten != req.query:
            yield f"__rewrite__:{rewritten}\n"
        yield f"__chunks__:{len(chunks)}\n"

        if not chunks:
            yield "I don't have enough information to answer this question."
            await save_chat_turn(session_id, req.query, "I don't have enough information to answer this question.")
            return

        full_response = []
        llm_start = time()
        async for token in generate_stream(rewritten or req.query, chunks):
            full_response.append(token)
            yield token

        llm_latency = time() - llm_start
        rag_llm_latency_seconds.observe(llm_latency)

        response_text = "".join(full_response)
        await save_chat_turn(session_id, req.query, response_text)

        log_query(req.query, rewritten, chunks, retrieval_latency, 0, llm_latency, response_text)

    return StreamingResponse(
        response_stream(),
        media_type="text/plain",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
    )
