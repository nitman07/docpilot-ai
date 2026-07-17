import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from loguru import logger

from app.core.auth import get_current_user
from app.core.db import get_pool
from app.core.embeddings import embed_texts
from app.core.qdrant import ensure_collection, upsert_chunks, delete_document_chunks
from app.core.storage import extract_text_from_pdf, chunk_text, save_temp_file
from app.schemas.document import Document, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])


def _row_to_doc(row) -> dict:
    d = dict(row)
    if isinstance(d.get("doc_metadata"), str):
        d["doc_metadata"] = json.loads(d["doc_metadata"])
    return d


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)) -> DocumentUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    tmp_path = save_temp_file(file_bytes)

    try:
        raw_text = extract_text_from_pdf(tmp_path)
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="Extracted text is empty")

        chunks = chunk_text(raw_text)
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks generated")

        ensure_collection()

        embeddings = embed_texts(chunks)

        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO documents (filename, title, chunk_count, status)
                VALUES ($1, $2, $3, 'indexed')
                RETURNING id, filename, chunk_count, status
                """,
                file.filename,
                file.filename,
                len(chunks),
            )

        doc_id = row["id"]
        upsert_chunks(doc_id, file.filename, chunks, embeddings)

        logger.info(f"Document {doc_id} indexed with {len(chunks)} chunks")
        return DocumentUploadResponse(
            document_id=doc_id,
            filename=file.filename,
            chunk_count=len(chunks),
            status="indexed",
        )

    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        import os
        os.unlink(tmp_path)


@router.get("", response_model=list[Document])
async def list_documents(user: dict = Depends(get_current_user)) -> list[Document]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM documents ORDER BY created_at DESC"
        )
    return [_row_to_doc(row) for row in rows]


@router.get("/{doc_id}", response_model=Document)
async def get_document(doc_id: UUID, user: dict = Depends(get_current_user)) -> Document:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM documents WHERE id = $1", doc_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return _row_to_doc(row)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: UUID, user: dict = Depends(get_current_user)) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "DELETE FROM documents WHERE id = $1 RETURNING id", doc_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(doc_id)
    logger.info(f"Document {doc_id} deleted")
