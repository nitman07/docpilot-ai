from typing import Literal, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.core.config import settings
from app.core.db import get_chat_history
from app.core.embeddings import embed_texts
from app.core.qdrant import hybrid_search
from app.core.reranker import rerank


class AgentState(TypedDict):
    session_id: str
    query: str
    history: list[dict]
    rewritten_query: str | None
    chunks: list[dict]


async def load_history(state: AgentState) -> dict:
    history = await get_chat_history(state["session_id"])
    return {"history": history}


def should_rewrite(state: AgentState) -> Literal["rewrite_query", "retrieve"]:
    if state["history"] and len(state["query"].split()) < 10:
        return "rewrite_query"
    return "retrieve"


async def rewrite_query(state: AgentState) -> dict:
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in state["history"]
    )
    prompt = f"""Rewrite the latest query as a standalone question using conversation history.
Return ONLY the rewritten question, nothing else.

History:
{history_text}

Latest query: {state['query']}

Rewritten query:"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.ollama_host}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
        )
        rewritten = resp.json()["response"].strip()

    logger.info(f"Query rewritten: '{state['query']}' → '{rewritten}'")
    return {"rewritten_query": rewritten}


async def retrieve(state: AgentState) -> dict:
    query = state.get("rewritten_query") or state["query"]
    embeddings = embed_texts([query])
    scored_points = hybrid_search(query, embeddings[0], limit=20)

    if not scored_points:
        return {"chunks": []}

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

    ranked = rerank(query, chunks, top_k=5)

    logger.info(f"Retrieved {len(ranked)} chunks")
    return {"chunks": ranked}


def build_agent() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("load_history", load_history)
    builder.add_node("rewrite_query", rewrite_query)
    builder.add_node("retrieve", retrieve)

    builder.add_edge(START, "load_history")
    builder.add_conditional_edges("load_history", should_rewrite)
    builder.add_edge("rewrite_query", "retrieve")
    builder.add_edge("retrieve", END)

    return builder.compile()
