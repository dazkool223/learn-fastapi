"""
Chunking Service
────────────────
Splits per-page Documents into smaller, overlapping chunks using
LangChain's RecursiveCharacterTextSplitter.

Design choices
--------------
* **chunk_size = 1000 chars** (~200-250 words): large enough to retain
  paragraph-level semantics, small enough for precise retrieval.
* **chunk_overlap = 200 chars**: prevents information loss at boundaries.
* **Separators**: paragraphs → sentences → words (recursive fallback).
* Each chunk inherits the parent Document's metadata *plus*
  ``chunk_index`` and ``chunk_size`` for traceability.
"""
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings

logger = logging.getLogger(__name__)


class ChunkingService:
    """Stateless chunker – one instance can be shared across requests."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self._chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        Split *documents* (typically one per page) into smaller chunks.

        Returns a flat list where every chunk carries the original
        page-level metadata extended with ``chunk_index`` and
        ``chunk_size``.
        """
        all_chunks: list[Document] = []
        global_index = 0

        for doc in documents:
            page_chunks = self._splitter.split_documents([doc])
            for chunk in page_chunks:
                chunk.metadata["chunk_index"] = global_index
                chunk.metadata["chunk_size"] = len(chunk.page_content)
                global_index += 1
                all_chunks.append(chunk)

        logger.info(
            "Split %d pages into %d chunks (size=%d, overlap=%d)",
            len(documents),
            len(all_chunks),
            self._chunk_size,
            self._chunk_overlap,
        )
        return all_chunks
