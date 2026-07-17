from loguru import logger
from sentence_transformers import CrossEncoder

from app.core.config import settings

_model: CrossEncoder | None = None


def get_model() -> CrossEncoder:
    global _model
    if _model is None:
        logger.info(f"Loading reranker: {settings.reranker_model}")
        _model = CrossEncoder(
            settings.reranker_model,
            device=settings.reranker_device,
        )
        logger.info("Reranker loaded")
    return _model


def rerank(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    model = get_model()
    texts = [c["chunk_text"] for c in chunks]
    pairs = [(query, text) for text in texts]
    scores = model.predict(pairs)

    scored = [
        {**chunks[i], "score": float(scores[i])}
        for i in range(len(chunks))
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)

    logger.info(f"Reranked {len(scored)} chunks, top score: {scored[0]['score']:.4f}")
    return scored[:top_k]
