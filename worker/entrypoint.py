#!/usr/bin/env python3
"""
RQ Worker entrypoint for VoiceStack2
"""

import os
import signal
import sys
from rq import Worker, Queue, Connection
from redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def signal_handler(signum, frame):
    """Handle graceful shutdown."""
    print("Received shutdown signal, stopping worker...")
    sys.exit(0)

def main():
    """Start the RQ worker."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get Redis connection
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queue = Queue("voicestack2", connection=redis_conn)
    
    print(f"Starting RQ worker on queue: voicestack2")
    print(f"Redis URL: {redis_url}")
    
    # Start worker
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()

if __name__ == "__main__":
    main() 