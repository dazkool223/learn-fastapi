# RAG Pipeline — Architecture & Design Document

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Ingestion Pipeline](#ingestion-pipeline)
   - [PDF Loading](#1-pdf-loading)
   - [Chunking Strategy](#2-chunking-strategy)
   - [Embedding Generation](#3-embedding-generation)
   - [Vector Storage](#4-vector-storage)
4. [Query Pipeline](#query-pipeline)
   - [Query Embedding](#1-query-embedding)
   - [Retrieval Algorithm](#2-retrieval-algorithm)
   - [Context Assembly & LLM Generation](#3-context-assembly--llm-generation)
5. [Handling Large Books (1000+ pages)](#handling-large-books-1000-pages)
6. [Database Schema](#database-schema)
7. [Configuration Reference](#configuration-reference)
8. [API Endpoints](#api-endpoints)
9. [Setup Instructions](#setup-instructions)

---

## Overview

This RAG (Retrieval-Augmented Generation) pipeline allows users to **ask natural-language questions** about books in the library and receive **grounded, cited answers** drawn directly from book content.

**Tech stack:**

| Component         | Technology                                          |
| ----------------- | --------------------------------------------------- |
| PDF Text Extract  | PyPDF (`pypdf`)                                     |
| Chunking          | LangChain `RecursiveCharacterTextSplitter`          |
| Embeddings        | OpenAI `text-embedding-3-small` (1 536 dims)       |
| Vector Store      | Supabase PostgreSQL + pgvector (HNSW index)         |
| LLM Generation    | OpenRouter (e.g. `openai/gpt-4o-mini`)              |
| Orchestration     | LangChain + custom FastAPI services                 |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      INGESTION (write path)                  │
│                                                              │
│  Supabase Storage ──► PDF Loader ──► Chunker ──► Embedder   │
│       (bucket)        (PyPDF)     (Recursive)   (OpenAI)    │
│                                                     │        │
│                                                     ▼        │
│                                              Supabase DB     │
│                                             (pgvector)       │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       QUERY (read path)                      │
│                                                              │
│  User Question ──► Query Embedder ──► pgvector Search        │
│                      (OpenAI)         (cosine sim, HNSW)     │
│                                            │                 │
│                                            ▼                 │
│                                     Top-K Chunks             │
│                                            │                 │
│                                            ▼                 │
│                                     LLM (OpenRouter)         │
│                                     + System Prompt          │
│                                            │                 │
│                                            ▼                 │
│                                    Grounded Answer           │
│                                    + Source Citations         │
└──────────────────────────────────────────────────────────────┘
```

---

## Ingestion Pipeline

Triggered via `POST /rag/ingest` with a `book_id`. The pipeline is **idempotent** — re-calling for the same book is a no-op unless `force=true`.

### 1. PDF Loading

**Service:** `services/rag/pdf_loader.py` → `PDFLoaderService`

| Step | Detail |
|------|--------|
| **Download** | The existing `SupabaseStorageService.download()` fetches the raw PDF bytes from the Supabase Storage bucket. The book's `file_path` (stored in the `book` table at upload time) is used as the object key. |
| **Parse** | `pypdf.PdfReader` opens the byte stream in memory — no temporary files are written to disk. |
| **Extract** | Text is extracted **page by page** via `page.extract_text()`. Pages that yield no text (scanned images without OCR) are skipped. |
| **Output** | One LangChain `Document` per non-empty page, each carrying metadata: `book_id`, `book_title`, `page_number`, `total_pages`, `source`. |

**Why PyPDF?**
- Pure Python — no system dependencies (unlike `pdfminer`, `poppler`).
- Handles most well-formed PDFs reliably.
- Lightweight memory footprint because pages are processed sequentially.

---

### 2. Chunking Strategy

**Service:** `services/rag/chunking_service.py` → `ChunkingService`

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| `chunk_size` | **1 000 chars** | ~200–250 words. Large enough to preserve paragraph semantics; small enough that the embedding captures a focused topic. |
| `chunk_overlap` | **200 chars** | ~20 % overlap ensures sentences split at a boundary still appear in at least one chunk. |
| Separators | `\n\n`, `\n`, `. `, `, `, ` `, `""` | The **RecursiveCharacterTextSplitter** tries the largest separator first, only falling back to smaller ones when a chunk would still exceed `chunk_size`. This preserves natural paragraph/sentence boundaries wherever possible. |

**How it works for a 1 000-page book:**

Assume an average of 3 000 characters per page (typical for a paperback):
- 1 000 pages × 3 000 chars = **3 000 000 characters** of raw text.
- With `chunk_size=1000` and `overlap=200`: each effective step is 800 chars.
- Expected chunks ≈ 3 000 000 / 800 ≈ **3 750 chunks**.

Each chunk inherits the parent page's metadata and gains:
- `chunk_index` — global sequential index across the whole book.
- `chunk_size` — actual character count of that chunk.

---

### 3. Embedding Generation

**Service:** `services/rag/embedding_service.py` → `EmbeddingService`

| Setting | Value |
|---------|-------|
| Model | `text-embedding-3-small` (OpenAI) |
| Dimensions | 1 536 |
| API | `https://api.openai.com/v1` |

**Process:**

1. The `VectorStoreService.add_documents()` processes chunks in **batches of 100**.
2. For each batch, LangChain's `SupabaseVectorStore.add_documents()` calls `OpenAIEmbeddings.embed_documents()` which sends the texts to the OpenAI Embeddings API.
3. The API returns a 1 536-dimensional float vector for each text.
4. The vectors and document content are upserted into the `book_chunks` table.

**For a 1 000-page book (~3 750 chunks):**
- 38 API calls (100 chunks each) + 1 final batch of 50.
- Embedding throughput is bounded by the OpenAI rate limit (typically 3 000 RPM / 1 000 000 TPM on Tier 1).
- Total embedding time: **~30–90 seconds** depending on rate limits.

**Why `text-embedding-3-small`?**
- Best cost/performance ratio for retrieval tasks (OpenAI MTEB benchmark).
- 1 536 dimensions offer strong semantic fidelity without excessive storage.
- Native dimension reduction support if lower dims are needed later.

---

### 4. Vector Storage

**Service:** `services/rag/vector_store_service.py` → `VectorStoreService`

Vectors are stored in a **Supabase PostgreSQL** table using the **pgvector** extension.

**Table: `book_chunks`**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | `text` (UUID) | Primary key, generated client-side by LangChain |
| `content` | `text` | The raw chunk text |
| `metadata` | `jsonb` | `book_id`, `book_title`, `page_number`, `chunk_index`, etc. |
| `embedding` | `vector(1536)` | The dense embedding vector |

**Indexes:**
- **HNSW** on `embedding` with cosine distance (`vector_cosine_ops`).
  - `m=16` — number of bi-directional links per node.
  - `ef_construction=64` — size of the dynamic candidate list during index build.
  - HNSW provides high recall (~99 %) and doesn't require periodic rebuilds after inserts (unlike IVFFlat).
- **GIN** on `metadata` for fast JSONB containment queries (`@>` operator).

---

## Query Pipeline

Triggered via `POST /rag/query`.

### 1. Query Embedding

The user's question is embedded using the **same model** (`text-embedding-3-small`) and **same dimensions** (1 536) as the document chunks. This ensures the query vector lives in the same semantic space, making cosine similarity meaningful.

```
"What is the main theme of Chapter 5?"
        │
        ▼
  OpenAI Embeddings API
        │
        ▼
  [0.012, -0.034, 0.078, …]   (1 536 floats)
```

### 2. Retrieval Algorithm

**Algorithm:** Approximate Nearest Neighbour (ANN) search via **HNSW** index with **cosine distance**.

```sql
-- Executed by the match_book_chunks() RPC function:
SELECT id, content, metadata,
       1 - (embedding <=> query_embedding) AS similarity
FROM   book_chunks
WHERE  metadata @> filter          -- e.g. {"book_id": 42}
ORDER BY embedding <=> query_embedding
LIMIT  match_count;                -- default: 5
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `top_k` | 5 | Number of chunks returned |
| `similarity_threshold` | 0.3 | Minimum cosine similarity to keep a chunk |
| `filter` (optional) | `{}` | JSONB containment — restrict to a specific `book_id` |

**Distance metric: Cosine Distance (`<=>`)**

`cosine_similarity = 1 - cosine_distance`

Cosine similarity ranges from −1 to 1 (in practice 0 to 1 for normalised embeddings). A score of 1.0 means identical vectors.

**Why HNSW over IVFFlat?**
- HNSW provides consistently high recall (>99 %) without needing to tune the number of probe lists.
- Inserts don't require index rebuilds — critical for a library that continuously ingests new books.
- Query latency is sub-millisecond for datasets under 1 M vectors.

### 3. Context Assembly & LLM Generation

After retrieval, the top-k chunks (that pass the similarity threshold) are assembled into a **structured context block**:

```
[Book: Clean Code, Page: 42]
Functions should do one thing. They should do it well.
They should do it only.

---

[Book: Clean Code, Page: 43]
The first rule of functions is that they should be small.
The second rule is that they should be smaller than that.
```

This context is injected into a **system prompt** that instructs the LLM to:
1. Answer **only** from the provided context.
2. **Cite** book title and page numbers.
3. Acknowledge when the context is insufficient.

The system prompt + user question are sent to the **OpenRouter LLM** (default: `openai/gpt-4o-mini`) with `temperature=0.3` for factual precision.

**Response structure:**
```json
{
  "answer": "The main theme of Chapter 5 is...",
  "sources": [
    {
      "content": "Functions should do one thing...",
      "book_id": 1,
      "book_title": "Clean Code",
      "page_number": 42,
      "chunk_index": 187,
      "similarity": 0.89
    }
  ],
  "model": "openai/gpt-4o-mini",
  "provider": "openrouter"
}
```

---

## Handling Large Books (1000+ pages)

| Challenge | Solution |
|-----------|----------|
| **Memory** | PyPDF processes pages sequentially; only one page's text is in memory at a time during extraction. |
| **Embedding API limits** | Chunks are embedded in batches of 100. At ~250 tokens/chunk, each batch uses ~25 000 tokens — well within OpenAI's per-request limit. |
| **Supabase payload size** | The `SupabaseVectorStore` upserts in batches (controlled by its `chunk_size` parameter) to avoid exceeding PostgREST's default 8 MB payload limit. |
| **Ingestion tracking** | The `bookingestion` table tracks status (`pending → processing → completed/failed`), so clients can poll `GET /rag/ingest/{book_id}/status`. |
| **Idempotency** | Calling ingest twice is a no-op (returns the existing record). Use `force=true` to delete old chunks and re-ingest. |
| **Error resilience** | If ingestion fails mid-way, the status is set to `failed` with the error message stored. The user can retry with `force=true`. |

---

## Database Schema

Run `sql/rag_setup.sql` in the Supabase SQL Editor to create:

```
book_chunks                    bookingestion
┌──────────────────────┐      ┌──────────────────────────┐
│ id         text  PK  │      │ id            serial PK  │
│ content    text      │      │ book_id       int FK→book│
│ metadata   jsonb     │      │ status        varchar(20)│
│ embedding  vector    │      │ total_chunks  int        │
│            (1536)    │      │ total_pages   int        │
└──────────────────────┘      │ error_message text       │
                              │ created_at    timestamptz│
                              │ updated_at    timestamptz│
                              └──────────────────────────┘
```

---

## Configuration Reference

Add these to your `.env` file:

```env
# Embedding (required – OpenAI API key for embeddings)
EMBEDDING_API_KEY=sk-your-openai-key-here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_DIMENSIONS=1536

# Chunking
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200

# Retrieval
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.3

# Vector store table names
VECTOR_TABLE_NAME=book_chunks
VECTOR_QUERY_FUNCTION=match_book_chunks
```

> **Note:** `EMBEDDING_API_KEY` falls back to `LLM_API_KEY` if not set. However, OpenRouter does **not** provide an embeddings endpoint — you need a direct OpenAI key (or any OpenAI-compatible embedding provider) for this setting.

---

## API Endpoints

### `POST /rag/ingest`

Trigger ingestion for a book.

**Request:**
```json
{
  "book_id": 1,
  "force": false
}
```

**Response (202 Accepted):**
```json
{
  "book_id": 1,
  "status": "completed",
  "total_chunks": 3750,
  "total_pages": 987,
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:32:45Z"
}
```

### `GET /rag/ingest/{book_id}/status`

Poll ingestion progress.

### `POST /rag/query`

Ask a question.

**Request:**
```json
{
  "query": "What design principles does the author recommend for functions?",
  "book_id": 1,
  "top_k": 5,
  "similarity_threshold": 0.3
}
```

**Response:**
```json
{
  "answer": "The author recommends that functions should be small and do one thing well...",
  "sources": [
    {
      "content": "Functions should do one thing...",
      "book_id": 1,
      "book_title": "Clean Code",
      "page_number": 42,
      "chunk_index": 187,
      "similarity": 0.89
    }
  ],
  "model": "openai/gpt-4o-mini",
  "provider": "openrouter"
}
```

---

## Setup Instructions

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the SQL migration** in the Supabase SQL Editor:
   ```
   sql/rag_setup.sql
   ```

3. **Add environment variables** to `.env` (see Configuration Reference above). At minimum you need `EMBEDDING_API_KEY`.

4. **Start the server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Ingest a book:**
   ```bash
   curl -X POST http://localhost:8000/rag/ingest \
     -H "Content-Type: application/json" \
     -d '{"book_id": 1}'
   ```

6. **Query:**
   ```bash
   curl -X POST http://localhost:8000/rag/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the main idea of the book?", "book_id": 1}'
   ```
