"""
PDF Loader Service
──────────────────
Downloads a book's PDF from Supabase Storage and extracts text
page-by-page using PyPDF.  Each page becomes a LangChain Document
with rich metadata that travels through the rest of the pipeline.
"""
import io
import logging

from langchain_core.documents import Document
from pypdf import PdfReader

from services.storage import StorageService

logger = logging.getLogger(__name__)


class PDFLoaderService:
    """Download a PDF from object storage and return per-page Documents."""

    def __init__(self, storage: StorageService):
        self._storage = storage

    def load(
        self,
        storage_path: str,
        book_id: int,
        book_title: str,
    ) -> list[Document]:
        """
        Download the PDF identified by *storage_path* and return one
        ``Document`` per page that contains extractable text.

        Metadata attached to every document:
        - book_id, book_title, page_number, total_pages, source
        """
        logger.info("Downloading PDF for book %d from %s", book_id, storage_path)
        pdf_bytes: bytes = self._storage.download(storage_path)

        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        documents: list[Document] = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                logger.debug("Page %d of book %d is empty, skipping", page_num, book_id)
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "book_id": book_id,
                        "book_title": book_title,
                        "page_number": page_num,
                        "total_pages": total_pages,
                        "source": storage_path,
                    },
                )
            )

        logger.info(
            "Extracted %d non-empty pages out of %d for book %d",
            len(documents),
            total_pages,
            book_id,
        )
        return documents
