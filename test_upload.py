#!/usr/bin/env python3
"""
Test script for uploading audio and testing transcript feature
"""

import requests
import os
import time

# API configuration
API_URL = "http://localhost:8000"
API_TOKEN = "changeme"  # Default token from docker-compose.yml
TEST_FILE = "test-files/multi-speaker-test.m4a"

def test_upload():
    """Test uploading a file and check transcript generation."""
    
    # Check if test file exists
    if not os.path.exists(TEST_FILE):
        print(f"Test file not found: {TEST_FILE}")
        return
    
    print(f"Testing upload with file: {TEST_FILE}")
    
    # Upload the file with authentication
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': ('multi-speaker-test.m4a', f, 'audio/m4a')}
        response = requests.post(f"{API_URL}/upload", files=files, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Upload successful: {result}")
        
        # Get the job ID
        job_id = result.get('job_id')
        if job_id:
            print(f"Job ID: {job_id}")
            
            # Wait a bit and check job status
            print("Waiting for job processing...")
            time.sleep(5)
            
            # Check job status
            job_response = requests.get(f"{API_URL}/jobs/{job_id}")
            if job_response.status_code == 200:
                job = job_response.json()
                print(f"Job status: {job.get('status')}")
                print(f"Job progress: {job.get('progress')}%")
                
                # If job is completed, check transcript
                if job.get('status') == 'SUCCEEDED':
                    print("Job completed! Checking transcript...")
                    
                    # Check if transcript exists
                    if job.get('transcript'):
                        transcript_id = job['transcript']['id']
                        transcript_response = requests.get(f"{API_URL}/transcripts/{transcript_id}")
                        if transcript_response.status_code == 200:
                            transcript = transcript_response.json()
                            print(f"Transcript found: {transcript.get('title', 'No title')}")
                            print(f"Segments: {len(transcript.get('segments', []))}")
                            print(f"Speakers: {len(transcript.get('speakers', []))}")
                        else:
                            print(f"Failed to get transcript: {transcript_response.status_code}")
                    else:
                        print("No transcript found in job")
                else:
                    print(f"Job not completed yet. Status: {job.get('status')}")
            else:
                print(f"Failed to get job: {job_response.status_code}")
        else:
            print("No job ID in response")
    else:
        print(f"Upload failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_upload() 