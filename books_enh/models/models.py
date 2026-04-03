from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    isbn: str = Field(unique=True, index=True)
    genre: Optional[str] = None
    published_year: Optional[int] = None
    total_copies: int = Field(default=1)
    available_copies: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))