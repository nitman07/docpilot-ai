from collections import Counter
from uuid import UUID

from loguru import logger
from qdrant_client import QdrantClient, models

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


def _compute_sparse_vector(text: str) -> models.SparseVector:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    freq = Counter(tokens)
    max_freq = max(freq.values()) if freq else 1
    indices = list(freq.keys())
    values = [freq[i] / max_freq for i in indices]
    return models.SparseVector(indices=indices, values=values)


def ensure_collection() -> None:
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in collections:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Qdrant collection '{COLLECTION_NAME}' deleted (recreating for hybrid search)")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=EMBEDDING_SIZE,
            distance=models.Distance.COSINE,
        ),
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                index=models.SparseIndexParams(
                    full_scan_threshold=10000,
                ),
            ),
        },
    )
    logger.info(f"Qdrant collection '{COLLECTION_NAME}' created with hybrid search")


def upsert_chunks(
    document_id: UUID,
    doc_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> int:
    client = get_client()
    ensure_collection()

    points = [
        models.PointStruct(
            id=hash(chunks[i]) % (2**63),
            vector={
                "": embeddings[i],
                "bm25": _compute_sparse_vector(chunks[i]),
            },
            payload={
                "chunk_text": chunks[i],
                "document_id": str(document_id),
                "doc_name": doc_name,
                "chunk_index": i,
            },
        )
        for i in range(len(chunks))
    ]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    logger.info(f"Upserted {len(points)} chunks for document {document_id}")
    return len(points)


def hybrid_search(
    query_text: str,
    query_embedding: list[float],
    limit: int = 20,
) -> list[models.ScoredPoint]:
    import httpx
    sparse_query = _compute_sparse_vector(query_text)

    base_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"

    dense_body = {
        "vector": query_embedding,
        "limit": 50,
        "with_payload": True,
    }
    sparse_body = {
        "vector": models.NamedSparseVector(
            name="bm25",
            vector=sparse_query,
        ).model_dump(),
        "limit": 50,
        "with_payload": True,
    }

    with httpx.Client(base_url=base_url) as h:
        dense_resp = h.post(
            f"/collections/{COLLECTION_NAME}/points/search",
            json=dense_body,
        )
        dense_resp.raise_for_status()
        dense_results = [models.ScoredPoint(**p) for p in dense_resp.json()["result"]]

        sparse_resp = h.post(
            f"/collections/{COLLECTION_NAME}/points/search",
            json=sparse_body,
        )
        sparse_resp.raise_for_status()
        sparse_results = [models.ScoredPoint(**p) for p in sparse_resp.json()["result"]]

    rrf_k = 60
    dense_rank = {p.id: i + 1 for i, p in enumerate(dense_results)}
    sparse_rank = {p.id: i + 1 for i, p in enumerate(sparse_results)}

    all_ids = set(dense_rank) | set(sparse_rank)
    scored = []
    for pid in all_ids:
        dr = dense_rank.get(pid, 999)
        sr = sparse_rank.get(pid, 999)
        rrf_score = 1 / (rrf_k + dr) + 1 / (rrf_k + sr)

        result = next(p for p in dense_results + sparse_results if p.id == pid)
        result.score = rrf_score
        scored.append(result)

    scored.sort(key=lambda p: p.score, reverse=True)
    return scored[:limit]


def delete_document_chunks(document_id: UUID) -> None:
    client = get_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(document_id)),
                )
            ]
        ),
    )
    logger.info(f"Deleted chunks for document {document_id}")


def count_points() -> int:
    client = get_client()
    return client.count(collection_name=COLLECTION_NAME).count
