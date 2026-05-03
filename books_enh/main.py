from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import time
import logging

from database.db import verify_connection
from routers import books, member, loan, chat, conversation, rag

from core.utils import char_streamer
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache import FastAPICache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    FastAPICache.init(InMemoryBackend())
    try:
        verify_connection()
        logger.info("Supabase connection OK.")
    except Exception as e:
        logger.error("Could not connect to Supabase: %s", e)
        raise
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Library Management System",
    description=(
        "A REST API for managing a library"
        "Built with FastAPI + Supabase"
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(books.router)
app.include_router(member.router)
app.include_router(loan.router)
app.include_router(chat.router)
app.include_router(conversation.router)
app.include_router(rag.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Library Management API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/stream")
def stream_file():
    file_path = "sample.txt"
    return StreamingResponse(char_streamer(file_path), media_type="text/event-stream")

