import json

import httpx
from loguru import logger

from app.core.config import settings


def build_prompt(query: str, chunks: list[dict]) -> tuple[str, str]:
    if not chunks:
        return (
            "You are DocPilot. Answer using ONLY the provided context. Never make up information.",
            f"The knowledge base returned no relevant information.\n\nQuestion: {query}",
        )

    context_parts = []
    for i, c in enumerate(chunks, 1):
        source = c.get("doc_name", "Unknown")
        text = c["chunk_text"].strip()
        context_parts.append(f"[{i}] ({source}) {text}")

    context = "\n\n".join(context_parts)

    system_prompt = (
        "Answer concisely using ONLY the context below. "
        "Cite sources like [1], [2]. "
        "Be confident and direct — never hedge with 'it appears' or 'based on the context'. "
        "If the context doesn't contain relevant information, say so and stop."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    return system_prompt, user_prompt


async def generate_stream(query: str, chunks: list[dict]):
    system_prompt, user_prompt = build_prompt(query, chunks)

    body = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": user_prompt,
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
