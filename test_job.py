#!/usr/bin/env python3
"""
Test script to create a job and test the worker
"""

import requests
import json

# Test the health endpoint
print("Testing health endpoint...")
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

# Create a test job
print("\nCreating test job...")
job_data = {
    "email_to": "test@example.com",
    "params": {}
}

try:
    response = requests.post(
        "http://localhost:8000/jobs/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(job_data)
    )
    print(f"Job creation: {response.status_code}")
    if response.status_code == 200:
        job = response.json()
        print(f"Job created: {job}")
        
        # Check job status
        job_id = job.get("id")
        if job_id:
            print(f"\nChecking job status for {job_id}...")
            status_response = requests.get(f"http://localhost:8000/jobs/{job_id}")
            print(f"Status check: {status_response.status_code}")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"Job status: {status}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Job creation failed: {e}")

print("\nTest completed!") 