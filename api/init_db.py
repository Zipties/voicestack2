#!/usr/bin/env python3
"""
Database initialization script for VoiceStack2 Phase 1
"""

from db.base import Base
from db.session import engine
from db.init_pgvector import init_pgvector

# Import all models to ensure they are registered with SQLAlchemy
import models

def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")
    
    # Initialize pgvector extension
    try:
        init_pgvector()
        print("✓ pgvector extension initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize pgvector: {e}")

if __name__ == "__main__":
    init_database() 