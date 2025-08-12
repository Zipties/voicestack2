"""
Database utilities for the worker
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API source directory from environment variable
api_dir = os.getenv("API_SRC_DIR", "/app/api")
print(f"API_SRC_DIR: {api_dir}")

# Add the API directory to Python path FIRST
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)
    print(f"Added {api_dir} to Python path")

# Also add the parent directory to find models
parent_dir = os.path.dirname(api_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to Python path")

# Add current directory to path
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Added {current_dir} to Python path")

print(f"Final Python path: {sys.path[:5]}...")

# Create engine and session
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://voice:voice@db:5432/voice")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import models after setting up the engine and path
try:
    print(f"Attempting to import models from {api_dir}")
    
    # First, let's check what's available
    print(f"API directory exists: {os.path.exists(api_dir)}")
    if os.path.exists(api_dir):
        print(f"API directory contents: {os.listdir(api_dir)}")
        models_dir = os.path.join(api_dir, "models")
        if os.path.exists(models_dir):
            print(f"Models directory contents: {os.listdir(models_dir)}")
    
    # Try to import the base first
    try:
        from api.db.base import Base
        print("✓ Imported Base from api.db.base")
    except ImportError as e:
        print(f"Failed to import Base: {e}")
        # Create a fallback Base
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
        print("✓ Created fallback Base")
    
    # Try importing models with proper error handling
    Job = Asset = Transcript = Segment = Speaker = Embedding = Tag = Setting = None
    
    try:
        # Import Job model - handle relative import issue
        try:
            from api.models.job import Job
            print("✓ Imported Job model from api.models.job")
        except ImportError as e:
            print(f"Failed to import Job model: {e}")
            # Try to fix the relative import by temporarily modifying sys.path
            original_path = sys.path.copy()
            try:
                # Add the models directory to path and try direct import
                models_path = os.path.join(api_dir, "models")
                if models_path not in sys.path:
                    sys.path.insert(0, models_path)
                
                # Also add the db directory to path
                db_path = os.path.join(api_dir, "db")
                if db_path not in sys.path:
                    sys.path.insert(0, db_path)
                
                # Also add the schemas directory to path
                schemas_path = os.path.join(api_dir, "schemas")
                if schemas_path not in sys.path:
                    sys.path.insert(0, schemas_path)
                
                # Now try importing
                from job import Job
                print("✓ Imported Job model using direct import")
            except ImportError as e2:
                print(f"Direct import also failed: {e2}")
                # Create a minimal Job class as final fallback
                try:
                    from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
                    from sqlalchemy.dialects.postgresql import UUID
                    import uuid
                    
                    class Job(Base):
                        __tablename__ = "jobs"
                        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
                        status = Column(String, nullable=False, default="QUEUED")
                        progress = Column(Integer, nullable=False, default=0)
                        params = Column(JSON, nullable=False, default=dict)
                        email_to = Column(String, nullable=True)
                        log_path = Column(String, nullable=True)
                        created_at = Column(DateTime(timezone=True))
                        updated_at = Column(DateTime(timezone=True))
                    print("✓ Created fallback Job model")
                except Exception as e3:
                    print(f"Failed to create fallback Job model: {e3}")
            finally:
                # Restore original path
                sys.path = original_path
    except Exception as e:
        print(f"Unexpected error importing Job model: {e}")
    
    # Try importing other models with the same approach
    try:
        from api.models.asset import Asset
        print("✓ Imported Asset model")
    except ImportError as e:
        print(f"Failed to import Asset model: {e}")
        Asset = None
    
    try:
        from api.models.transcript import Transcript
        print("✓ Imported Transcript model")
    except ImportError as e:
        print(f"Failed to import Transcript model: {e}")
        Transcript = None
    
    try:
        from api.models.segment import Segment
        print("✓ Imported Segment model")
    except ImportError as e:
        print(f"Failed to import Segment model: {e}")
        Segment = None
    
    try:
        from api.models.speaker import Speaker
        print("✓ Imported Speaker model")
    except ImportError as e:
        print(f"Failed to import Speaker model: {e}")
        Speaker = None
    
    try:
        from api.models.embedding import Embedding
        print("✓ Imported Embedding model")
    except ImportError as e:
        print(f"Failed to import Embedding model: {e}")
        Embedding = None
    
    try:
        from api.models.tag import Tag
        print("✓ Imported Tag model")
    except ImportError as e:
        print(f"Failed to import Tag model: {e}")
        Tag = None
    
    try:
        from api.models.setting import Setting
        print("✓ Imported Setting model")
    except ImportError as e:
        print(f"Failed to import Setting model: {e}")
        Setting = None
    
    print("Model import process completed")
    
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    print(f"Python path: {sys.path[:3]}...")
    print(f"API directory: {api_dir}")
    print(f"API directory exists: {os.path.exists(api_dir)}")
    if os.path.exists(api_dir):
        print(f"API directory contents: {os.listdir(api_dir)}")
        models_dir = os.path.join(api_dir, "models")
        if os.path.exists(models_dir):
            print(f"Models directory contents: {os.listdir(models_dir)}")
    
    # Create dummy classes for testing
    Job = Asset = Transcript = Segment = Speaker = Embedding = Tag = Setting = None 