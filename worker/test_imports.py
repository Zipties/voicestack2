#!/usr/bin/env python3
"""
Test script to verify imports are working correctly
"""

import os
import sys

print("=== Testing Import Resolution ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Add the API directory to Python path
api_dir = os.getenv("API_SRC_DIR", "/app/api")
print(f"API_SRC_DIR: {api_dir}")
print(f"API directory exists: {os.path.exists(api_dir)}")

if os.path.exists(api_dir):
    print(f"API directory contents: {os.listdir(api_dir)}")
    
    models_dir = os.path.join(api_dir, "models")
    if os.path.exists(models_dir):
        print(f"Models directory contents: {os.listdir(models_dir)}")
    else:
        print("Models directory not found!")

# Add paths
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)
    print(f"Added {api_dir} to Python path")

parent_dir = os.path.dirname(api_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to Python path")

print(f"Python path: {sys.path[:5]}...")

# Test imports
print("\n=== Testing Model Imports ===")

try:
    from api.models.job import Job
    print("✓ Imported Job model")
except ImportError as e:
    print(f"✗ Failed to import Job model: {e}")

try:
    from api.models.asset import Asset
    print("✓ Imported Asset model")
except ImportError as e:
    print(f"✗ Failed to import Asset model: {e}")

try:
    from api.models.transcript import Transcript
    print("✓ Imported Transcript model")
except ImportError as e:
    print(f"✗ Failed to import Transcript model: {e}")

try:
    from api.models.segment import Segment
    print("✓ Imported Segment model")
except ImportError as e:
    print(f"✗ Failed to import Segment model: {e}")

try:
    from api.models.speaker import Speaker
    print("✓ Imported Speaker model")
except ImportError as e:
    print(f"✗ Failed to import Speaker model: {e}")

try:
    from api.models.embedding import Embedding
    print("✓ Imported Embedding model")
except ImportError as e:
    print(f"✗ Failed to import Embedding model: {e}")

try:
    from api.models.tag import Tag
    print("✓ Imported Tag model")
except ImportError as e:
    print(f"✗ Failed to import Tag model: {e}")

try:
    from api.models.setting import Setting
    print("✓ Imported Setting model")
except ImportError as e:
    print(f"✗ Failed to import Setting model: {e}")

print("\n=== Testing Database Connection ===")

try:
    from db import get_db
    print("✓ Imported get_db function")
    
    # Test database connection
    db_gen = get_db()
    db = next(db_gen)
    print(f"✓ Got database session: {db}")
    
    # Test a simple query
    try:
        result = db.execute("SELECT 1 as test").fetchone()
        print(f"✓ Database query successful: {result}")
    except Exception as e:
        print(f"✗ Database query failed: {e}")
    
except ImportError as e:
    print(f"✗ Failed to import get_db: {e}")

print("\n=== Testing Pipeline Imports ===")

try:
    from pipeline.run import run_job
    print("✓ Imported run_job function")
except ImportError as e:
    print(f"✗ Failed to import run_job: {e}")

try:
    from pipeline.artifacts import log_step
    print("✓ Imported log_step function")
except ImportError as e:
    print(f"✗ Failed to import log_step: {e}")

print("\n=== Import Test Complete ===") 