#!/usr/bin/env python3
"""
RQ Worker for VoiceStack2
"""

import os
import sys
from rq import Worker, Queue
from redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path so we can import pipeline modules
sys.path.insert(0, os.path.dirname(__file__))

# Add the api directory to Python path for models
api_dir = os.getenv("API_SRC_DIR", "/app/api")
if api_dir not in sys.path:
    sys.path.append(api_dir)

def test_job(job_id: str, input_path: str, params: dict):
    """Simple test function for RQ."""
    print(f"Test job {job_id} with input {input_path} and params {params}")
    return f"Job {job_id} completed successfully"

def main():
    """Start the RQ worker."""
    # Get Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queue = Queue("voicestack2", connection=redis_conn)
    
    print(f"Starting RQ worker on queue: voicestack2")
    print(f"Redis URL: {redis_url}")
    print(f"Python path: {sys.path[:5]}...")
    
    # Test database imports first
    print("\n=== Testing Database Imports ===")
    try:
        import db
        print("✓ Successfully imported db module")
        print(f"db.get_db function exists: {hasattr(db, 'get_db')}")
        
        # Test if models are available
        if hasattr(db, 'Job') and db.Job is not None:
            print("✓ Job model is available")
        else:
            print("⚠ Job model is not available")
            
        if hasattr(db, 'Asset') and db.Asset is not None:
            print("✓ Asset model is available")
        else:
            print("⚠ Asset model is not available")
            
    except ImportError as e:
        print(f"✗ Failed to import db module: {e}")
        print("This will cause database update failures")
    
    # Pre-import the simple_pipeline module to ensure it's available
    print("\n=== Testing Pipeline Imports ===")
    try:
        import simple_pipeline
        print(f"✓ Successfully imported simple_pipeline module")
        print(f"simple_pipeline.run_job_sync function exists: {hasattr(simple_pipeline, 'run_job_sync')}")
    except ImportError as e:
        print(f"✗ Failed to import simple_pipeline: {e}")
        print(f"Python path: {sys.path}")
        return
    
    print("\n=== Starting Worker ===")
    # Start worker
    worker = Worker([queue], connection=redis_conn)
    worker.work()

if __name__ == "__main__":
    main()
