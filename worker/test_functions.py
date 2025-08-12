#!/usr/bin/env python3
"""
Test functions for RQ worker
"""

def test_job(job_id: str, input_path: str, params: dict):
    """Simple test function for RQ."""
    print(f"Test job {job_id} with input {input_path} and params {params}")
    return f"Job {job_id} completed successfully"

def run_job(job_id: str, input_path: str, params: dict):
    """Main job function for RQ."""
    print(f"Running job {job_id} with input {input_path} and params {params}")
    
    # For now, just return success
    # TODO: Implement full pipeline
    return f"Job {job_id} completed successfully" 