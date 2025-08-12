#!/usr/bin/env python3
"""
Real pipeline for VoiceStack2 - uses actual ASR, alignment, and LLM modules
"""

import os
import sys
import json
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))
api_dir = os.getenv("API_SRC_DIR", "/app/api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

# Also add the parent directory to find models
parent_dir = os.path.dirname(api_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Python path: {sys.path}")

async def run_job(job_id: str, input_path: str, params: dict):
    """Main job function for RQ - real implementation using actual pipeline modules."""
    print(f"Starting real pipeline job {job_id}")
    print(f"Input path: {input_path}")
    print(f"Params: {params}")
    
    try:
        # Import the real pipeline runner
        from pipeline.run import run_job as real_run_job
        
        # Run the actual pipeline
        await real_run_job(job_id, input_path, params)
        
        print(f"Real pipeline completed successfully for job {job_id}")
        return f"Job {job_id} completed successfully with real pipeline"
        
    except ImportError as e:
        print(f"Failed to import real pipeline: {e}")
        print("Falling back to simplified processing...")
        
        # Fallback: Create artifacts directory and basic processing
        artifacts_dir = f"/data/artifacts/{job_id}"
        Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
        
        # Log the start
        with open(f"{artifacts_dir}/_pipeline.log", "w") as f:
            f.write(f"Job {job_id} started (fallback mode)\n")
            f.write(f"Input: {input_path}\n")
            f.write(f"Params: {json.dumps(params, indent=2)}\n")
            f.write(f"Error: Real pipeline import failed: {e}\n")
        
        # Update job status to failed - with better error handling
        try:
            from sqlalchemy import create_engine, text
            
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://voice:voice@db:5432/voice")
            engine = create_engine(DATABASE_URL)
            
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE jobs SET status=:status, log_path=:log_path, updated_at=NOW() WHERE id::text=:job_id"),
                    {"status": "FAILED", "log_path": f"Pipeline import failed: {e}", "job_id": job_id}
                )
                print("✓ Updated job status to FAILED in database")
        except Exception as db_e:
            print(f"Failed to update job status: {db_e}")
            print("This is expected if the database models are not available")
        
        raise e
        
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        
        # Update job status to failed - with better error handling
        try:
            from sqlalchemy import create_engine, text
            
            DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://voice:voice@db:5432/voice")
            engine = create_engine(DATABASE_URL)
            
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE jobs SET status=:status, log_path=:log_path, updated_at=NOW() WHERE id::text=:job_id"),
                    {"status": "FAILED", "log_path": str(e), "job_id": job_id}
                )
                print("✓ Updated job status to FAILED in database")
        except Exception as db_e:
            print(f"Failed to update job status: {db_e}")
            print("This is expected if the database models are not available")
        
        raise e

# For RQ compatibility, provide a sync wrapper
def run_job_sync(job_id: str, input_path: str, params: dict):
    """Synchronous wrapper for RQ compatibility."""
    return asyncio.run(run_job(job_id, input_path, params)) 