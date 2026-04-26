"""
RAG Service  –  main orchestrator
──────────────────────────────────
Two public entry points:

1. **ingest_book(book_id)**
   PDF → pages → chunks → embeddings → vector store

2. **query(RAGQueryRequest)**
   question → embed → similarity search → build prompt → LLM → answer

All heavy lifting is delegated to specialised sub-services; this
module only handles coordination and error handling.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from core.config import settings
from core.exceptions import (
    BookFileNotFoundException,
    BookNotFoundException,
    BookNotIngestedException,
    RAGIngestionException,
    RAGQueryException,
)
from models.book import Book
from models.book_embedding import BookIngestion, IngestionStatus
from schemas.chat import ChatMessage
from schemas.rag import (
    IngestionStatusResponse,
    RAGChunkSource,
    RAGQueryRequest,
    RAGQueryResponse,
)
from services.langchain_llm_provider import build_llm_provider
from services.rag.chunking_service import ChunkingService
from services.rag.embedding_service import EmbeddingService
from services.rag.pdf_loader import PDFLoaderService
from services.rag.vector_store_service import VectorStoreService
from services.storage import StorageService

logger = logging.getLogger(__name__)

# ── RAG system prompt ────────────────────────────────────────────────

RAG_SYSTEM_PROMPT = """\
You are a knowledgeable assistant that answers questions based on the \
provided book excerpts.

Instructions:
- Answer the question based ONLY on the provided context from the book(s).
- If the context doesn't contain enough information to answer, say so clearly.
- Cite the specific book title and page number(s) when referencing information.
- Be precise and factual in your answers.
- If multiple sources provide relevant information, synthesize them coherently.

Context from books:
{context}
"""


class RAGService:
    """Facade that exposes ingestion + query to the router layer."""

    def __init__(
        self,
        session: Session,
        storage: StorageService,
    ) -> None:
        self._session = session
        self._storage = storage
        self._embedding_svc = EmbeddingService()
        self._pdf_loader = PDFLoaderService(storage)
        self._chunker = ChunkingService()
        self._vector_store = VectorStoreService(self._embedding_svc)

    # ── Ingestion ────────────────────────────────────────────────────

    def ingest_book(
        self,
        book_id: int,
        force: bool = False,
    ) -> IngestionStatusResponse:
        """
        Full ingestion pipeline:
        1. Validate book & file existence
        2. Download PDF from Supabase Storage
        3. Extract text per page (PyPDF)
        4. Chunk pages with RecursiveCharacterTextSplitter
        5. Batch-embed & store in pgvector via SupabaseVectorStore
        """
        # 1 ── validate
        book = self._session.get(Book, book_id)
        if not book:
            raise BookNotFoundException()
        if not book.file_path:
            raise BookFileNotFoundException(
                f"Book '{book.title}' has no PDF file uploaded"
            )

        # 2 ── idempotency check
        ingestion = self._get_ingestion(book_id)
        if (
            ingestion
            and ingestion.status == IngestionStatus.COMPLETED
            and not force
        ):
            return IngestionStatusResponse.model_validate(ingestion)

        # 3 ── upsert tracking row
        if not ingestion:
            ingestion = BookIngestion(
                book_id=book_id,
                status=IngestionStatus.PROCESSING,
            )
            self._session.add(ingestion)
        else:
            ingestion.status = IngestionStatus.PROCESSING
            ingestion.error_message = None
            ingestion.updated_at = datetime.now(timezone.utc)
        self._session.commit()
        self._session.refresh(ingestion)

        try:
            # 4 ── drop stale chunks on re-ingest
            if force:
                self._vector_store.delete_by_book_id(book_id)

            # 5 ── load → chunk → store
            pages = self._pdf_loader.load(
                book.file_path, book_id, book.title,
            )
            chunks = self._chunker.chunk_documents(pages)
            total_stored = self._vector_store.add_documents(chunks)

            # 6 ── mark success
            ingestion.status = IngestionStatus.COMPLETED
            ingestion.total_chunks = total_stored
            ingestion.total_pages = len(pages)
            ingestion.updated_at = datetime.now(timezone.utc)
            self._session.commit()
            self._session.refresh(ingestion)

            logger.info(
                "Ingested book %d: %d chunks from %d pages",
                book_id,
                total_stored,
                len(pages),
            )
            return IngestionStatusResponse.model_validate(ingestion)

        except Exception as exc:
            ingestion.status = IngestionStatus.FAILED
            ingestion.error_message = str(exc)[:500]
            ingestion.updated_at = datetime.now(timezone.utc)
            self._session.commit()
            logger.error("Ingestion failed for book %d: %s", book_id, exc)
            raise RAGIngestionException(f"Ingestion failed: {exc}")

    # ── Query ────────────────────────────────────────────────────────

    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        RAG query pipeline:
        1. Embed the user question
        2. Cosine-similarity search in pgvector
        3. Filter by threshold
        4. Assemble prompt with retrieved context
        5. Send to LLM (OpenRouter) and return answer + sources
        """
        try:
            # 1 ── optional book filter
            filter_dict: dict = {}
            if request.book_id is not None:
                ingestion = self._get_ingestion(request.book_id)
                if not ingestion or ingestion.status != IngestionStatus.COMPLETED:
                    raise BookNotIngestedException(
                        f"Book {request.book_id} has not been ingested yet"
                    )
                filter_dict["book_id"] = request.book_id

            # 2 ── retrieve
            results = self._vector_store.similarity_search(
                query=request.query,
                top_k=request.top_k,
                filter=filter_dict if filter_dict else None,
            )

            # 3 ── threshold filter
            filtered = [
                (doc, score)
                for doc, score in results
                if score >= request.similarity_threshold
            ]

            if not filtered:
                return RAGQueryResponse(
                    answer=(
                        "I couldn't find relevant information in the "
                        "ingested books to answer your question."
                    ),
                    sources=[],
                    model=request.model or settings.LLM_MODEL,
                    provider=settings.LLM_PROVIDER,
                )

            # 4 ── build context
            context_parts: list[str] = []
            sources: list[RAGChunkSource] = []

            for doc, score in filtered:
                meta = doc.metadata
                context_parts.append(
                    f"[Book: {meta.get('book_title', 'Unknown')}, "
                    f"Page: {meta.get('page_number', 'N/A')}]\n"
                    f"{doc.page_content}"
                )
                sources.append(
                    RAGChunkSource(
                        content=doc.page_content,
                        book_id=meta.get("book_id", 0),
                        book_title=meta.get("book_title", "Unknown"),
                        page_number=meta.get("page_number"),
                        chunk_index=meta.get("chunk_index", 0),
                        similarity=score,
                    )
                )

            context = "\n\n---\n\n".join(context_parts)

            # 5 ── LLM call
            system_prompt = RAG_SYSTEM_PROMPT.format(context=context)
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=request.query),
            ]

            llm = build_llm_provider(
                model=request.model,
                temperature=(
                    request.temperature
                    if request.temperature is not None
                    else 0.3
                ),
                max_tokens=request.max_tokens,
            )
            ai_message = await llm.ainvoke(messages)

            return RAGQueryResponse(
                answer=str(ai_message.content),
                sources=sources,
                model=llm.model_name,
                provider=llm.provider_name,
            )

        except (BookNotIngestedException, RAGQueryException):
            raise
        except Exception as exc:
            logger.error("RAG query failed: %s", exc)
            raise RAGQueryException(f"Query failed: {exc}")

    # ── Status ───────────────────────────────────────────────────────

    def get_ingestion_status(self, book_id: int) -> IngestionStatusResponse:
        ingestion = self._get_ingestion(book_id)
        if not ingestion:
            raise BookNotIngestedException(
                f"Book {book_id} has not been ingested"
            )
        return IngestionStatusResponse.model_validate(ingestion)

    # ── Private helpers ──────────────────────────────────────────────

    def _get_ingestion(self, book_id: int) -> Optional[BookIngestion]:
        stmt = select(BookIngestion).where(BookIngestion.book_id == book_id)
        return self._session.exec(stmt).first()
