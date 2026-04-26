"""
RAG Router
──────────
Endpoints for book ingestion and retrieval-augmented generation queries.
"""
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from database.db import get_session
from schemas.rag import (
    IngestionRequest,
    IngestionStatusResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from services.rag.rag_service import RAGService
from services.supabase_storage import SupabaseStorageService, get_storage_service

router = APIRouter(prefix="/rag", tags=["RAG"])


# ── Dependency ───────────────────────────────────────────────────────

def get_rag_service(
    session: Session = Depends(get_session),
    storage: SupabaseStorageService = Depends(get_storage_service),
) -> RAGService:
    return RAGService(session, storage)


# ── Ingestion ────────────────────────────────────────────────────────

@router.post(
    "/ingest",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a book's PDF into the vector store",
)
def ingest_book(
    request: IngestionRequest,
    service: RAGService = Depends(get_rag_service),
) -> IngestionStatusResponse:
    """
    Download the book's PDF from Supabase Storage, extract text,
    chunk it, generate embeddings, and store the vectors in
    Supabase pgvector for later retrieval.

    Set ``force=true`` to re-ingest a book that was already processed.
    """
    return service.ingest_book(request.book_id, force=request.force)


@router.get(
    "/ingest/{book_id}/status",
    response_model=IngestionStatusResponse,
    summary="Check ingestion status for a book",
)
def get_ingestion_status(
    book_id: int,
    service: RAGService = Depends(get_rag_service),
) -> IngestionStatusResponse:
    return service.get_ingestion_status(book_id)


# ── Query ────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Ask a question against ingested books",
)
async def query_books(
    request: RAGQueryRequest,
    service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    """
    Embed the question, retrieve the most relevant book chunks via
    cosine similarity, and pass them as context to the LLM for a
    grounded answer.

    Optionally filter by ``book_id`` and tune ``top_k``,
    ``similarity_threshold``, or LLM parameters per request.
    """
    return await service.query(request)
