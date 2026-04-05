import logging
 
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, Session, create_engine
 
from core.config import settings
 
logger = logging.getLogger(__name__)

if settings.DATABASE_URL == None : 
    raise ValueError("Database Connection String NOT FOUND")

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,           # Supabase manages pooling server-side
    connect_args={
        "options": "-c statement_timeout=30000",  # 30s query timeout
    },
)

def verify_connection() -> None:
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
 
def get_session():
    with Session(engine) as session:
        yield session