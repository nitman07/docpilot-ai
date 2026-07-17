import json

import httpx
from loguru import logger

from app.core.config import settings


def build_prompt(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return f"""You are DocPilot, an AI assistant for enterprise documents.

The knowledge base returned no relevant information for this question.

Question: {query}

Answer: I don't have enough information to answer this question."""

    context_parts = []
    for i, c in enumerate(chunks, 1):
        source = c.get("doc_name", "Unknown")
        text = c["chunk_text"].strip()
        context_parts.append(f"[{i}] ({source}) {text}")

    context = "\n\n".join(context_parts)

    return f"""You are DocPilot, an AI assistant for enterprise documents.
Answer the question using ONLY the provided context chunks below.
Cite each claim using the bracketed number like [1], [2] etc.
If the context doesn't contain enough information, say "I don't have enough information."

Context:
{context}

Question: {query}

Answer:"""


async def generate_stream(query: str, chunks: list[dict]):
    prompt = build_prompt(query, chunks)

    body = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            async with client.stream(
                "POST",
                f"{settings.ollama_host}/api/generate",
                json=body,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        return
        except httpx.ConnectError:
            yield f"\n\n⚠️ Error: Cannot connect to Ollama at {settings.ollama_host}. Is Ollama running?"
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"\n\n⚠️ Error: {str(e)}"
