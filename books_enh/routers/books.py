from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from database.db import get_session
from models.models import Book
from schemas.schemas import BookCreate, BookResponse, BookUpdate
from services.book_service import BookService
from core.exceptions import BookNotFoundException

router = APIRouter(prefix="/books")


def get_book_service(session: Session = Depends(get_session)) -> BookService:
    return BookService(session)

def _get_book(book_id: int, service: BookService) -> Book:
    book = service.get_by_id(book_id)
    if not book:
        raise BookNotFoundException()
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    data: BookCreate,
    service: BookService = Depends(get_book_service),
):
    return service.create(data)

@router.get("/", response_model=list[BookResponse])
def list_books(
    search: Optional[str] = Query(None, description="Search by title or author"),
    genre: Optional[str] = Query(None),
    available_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: BookService = Depends(get_book_service),
):
    return service.list(
        search=search,
        genre=genre,
        available_only=available_only,
        offset=offset,
        limit=limit,
    )


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    return _get_book(book_id, service)


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    data: BookUpdate,
    service: BookService = Depends(get_book_service),
):
    book = _get_book(book_id, service)
    return service.update(book, data)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    book = _get_book(book_id, service)
    service.delete(book)