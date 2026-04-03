from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from database.db import get_session
from models.models import Book
from schemas.schemas import BookCreate, BookResponse, BookUpdate

router = APIRouter(prefix="/books")


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Book).where(Book.isbn == book.isbn)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{book.isbn}' already exists",
        )
    db_book = Book(
        **book.model_dump(),
        available_copies=book.total_copies,
    )
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@router.get("/", response_model=list[BookResponse])
def list_books(
    search: Optional[str] = Query(None, description="Search by title or author"),
    genre: Optional[str] = Query(None),
    available_only: bool = Query(False, description="Show only books with available copies"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    query = select(Book)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            func.lower(Book.title).like(term) | func.lower(Book.author).like(term)
        )
    if genre:
        query = query.where(func.lower(Book.genre).like(f"%{genre.lower()}%"))
    if available_only:
        query = query.where(Book.available_copies > 0)
    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int, updates: BookUpdate, session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    data = updates.model_dump(exclude_unset=True)

    if "total_copies" in data:
        delta = data["total_copies"] - book.total_copies
        new_available = book.available_copies + delta
        if new_available < 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot reduce total_copies below the number currently on loan",
            )
        book.available_copies = new_available

    for key, value in data.items():
        setattr(book, key, value)

    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_copies < book.total_copies:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete book while copies are on loan",
        )
    session.delete(book)
    session.commit()
