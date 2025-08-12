#!/usr/bin/env python3
"""
Test script to manually enqueue a job and test the worker
"""

import os
import sys
from rq import Queue
from redis import Redis

def test_worker():
    """Test the worker by enqueueing a job."""
    # Connect to Redis
    redis_url = "redis://localhost:6379/0"
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queue = Queue("voicestack2", connection=redis_conn)
    
    print(f"Connected to Redis at {redis_url}")
    print(f"Queue: {queue.name}")
    
    # Enqueue a test job
    job = queue.enqueue(
        "simple_pipeline.run_job",
        "test-manual-job",
        "/test/path",
        {},
        job_timeout=3600
    )
    
    print(f"Job enqueued: {job.id}")
    print(f"Job status: {job.get_status()}")
    
    return job.id

if __name__ == "__main__":
    try:
        job_id = test_worker()
        print(f"Successfully enqueued job: {job_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 