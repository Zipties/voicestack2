from sqlalchemy import text
from .session import engine

def init_pgvector():
    """Initialize pgvector extension in the database."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit() 