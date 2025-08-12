"""
GPU mutex for coordinating GPU operations
"""

import os
import time
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

class GPUMutex:
    """Simple mutex for GPU operations using Redis."""
    
    def __init__(self, lock_name="gpu_lock", timeout=300):
        self.lock_name = lock_name
        self.timeout = timeout
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = Redis.from_url(self.redis_url)
    
    def __enter__(self):
        """Acquire the lock."""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.redis.set(self.lock_name, "locked", ex=300, nx=True):
                return self
            time.sleep(1)
        raise TimeoutError(f"Could not acquire GPU lock after {self.timeout} seconds")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        self.redis.delete(self.lock_name)

def get_gpu_mutex():
    """Get a GPU mutex instance."""
    return GPUMutex() 