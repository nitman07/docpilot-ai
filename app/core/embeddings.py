from openai import OpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def get_client() -> OpenAI:
    return OpenAI()


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]
