from uuid import UUID

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

COLLECTION_NAME = "documents"
EMBEDDING_SIZE = 1536


def get_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        grpc_port=settings.qdrant_grpc_port,
        api_key=settings.qdrant_api_key,
        prefer_grpc=settings.qdrant_prefer_grpc,
        https=False,
        check_compatibility=False,
    )


def ensure_collection() -> None:
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' created")


def upsert_chunks(
    document_id: UUID,
    doc_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    client = get_client()
    points = [
        PointStruct(
            id=hash(chunks[i]) % (2**63),
            vector=embeddings[i],
            payload={
                "chunk_text": chunks[i],
                "document_id": str(document_id),
                "doc_name": doc_name,
                "chunk_index": i,
            },
        )
        for i in range(len(chunks))
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"Upserted {len(points)} chunks for document {document_id}")
    return len(points)


def delete_document_chunks(document_id: UUID) -> None:
    client = get_client()
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=str(document_id)),
                )
            ]
        ),
    )
    logger.info(f"Deleted chunks for document {document_id}")


def count_points() -> int:
    client = get_client()
    return client.count(collection_name=COLLECTION_NAME).count
