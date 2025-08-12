#!/usr/bin/env python3
"""
Test script to upload a file and test the worker
"""

import requests
import os

# Test the health endpoint
print("Testing health endpoint...")
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

# Test file upload
print("\nTesting file upload...")

# Check if we have a test file
test_file_path = "test-files/small-test-file.m4a"
if not os.path.exists(test_file_path):
    print(f"Test file not found: {test_file_path}")
    print("Creating a dummy test file...")
    
    # Create a dummy test file
    os.makedirs("test-files", exist_ok=True)
    with open(test_file_path, "wb") as f:
        # Write some dummy audio data (just random bytes for testing)
        f.write(b"dummy audio data" * 100)
    
    print(f"Created dummy test file: {test_file_path}")

# Upload the test file
try:
    with open(test_file_path, "rb") as f:
        files = {"file": (os.path.basename(test_file_path), f, "audio/m4a")}
        data = {
            "email_to": "test@example.com",
            "params": "{}"
        }
        
        # Note: We need an API token for this endpoint
        headers = {"Authorization": "Bearer changeme"}
        
        response = requests.post(
            "http://localhost:8000/upload/",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"Upload response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload successful: {result}")
            
            # Check job status
            job_id = result.get("job_id")
            if job_id:
                print(f"\nChecking job status for {job_id}...")
                status_response = requests.get(f"http://localhost:8000/jobs/{job_id}")
                print(f"Status check: {status_response.status_code}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"Job status: {status}")
        else:
            print(f"Upload failed: {response.text}")
            
except Exception as e:
    print(f"Upload failed: {e}")

print("\nTest completed!") 