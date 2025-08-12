"""
Artifacts management for the pipeline
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

def ensure_artifacts_dir(job_id: str) -> str:
    """Ensure artifacts directory exists and return path."""
    artifacts_dir = os.path.join("/data/artifacts", job_id)
    Path(artifacts_dir).mkdir(parents=True, exist_ok=True)
    return artifacts_dir

def log_step(job_id: str, message: str):
    """Log a step message to the pipeline log."""
    artifacts_dir = ensure_artifacts_dir(job_id)
    log_file = os.path.join(artifacts_dir, "_pipeline.log")
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    print(f"[{job_id}] {message}")

def write_json(job_id: str, filename: str, data: Dict[str, Any]):
    """Write JSON data to artifacts directory."""
    artifacts_dir = ensure_artifacts_dir(job_id)
    filepath = os.path.join(artifacts_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    log_step(job_id, f"Wrote {filename}")

def write_text(job_id: str, filename: str, content: str):
    """Write text content to artifacts directory."""
    artifacts_dir = ensure_artifacts_dir(job_id)
    filepath = os.path.join(artifacts_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    log_step(job_id, f"Wrote {filename}")

def write_srt(job_id: str, segments: List[Dict[str, Any]], filename: str = "transcript.srt"):
    """Write SRT subtitle file."""
    artifacts_dir = ensure_artifacts_dir(job_id)
    filepath = os.path.join(artifacts_dir, filename)
    
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment.get("text", "").strip()
        
        srt_content += f"{i}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    log_step(job_id, f"Wrote {filename}")

def write_vtt(job_id: str, segments: List[Dict[str, Any]], filename: str = "transcript.vtt"):
    """Write VTT subtitle file."""
    artifacts_dir = ensure_artifacts_dir(job_id)
    filepath = os.path.join(artifacts_dir, filename)
    
    vtt_content = "WEBVTT\n\n"
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"], vtt=True)
        end_time = format_timestamp(segment["end"], vtt=True)
        text = segment.get("text", "").strip()
        
        vtt_content += f"{start_time} --> {end_time}\n"
        vtt_content += f"{text}\n\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    
    log_step(job_id, f"Wrote {filename}")

def format_timestamp(seconds: float, vtt: bool = False) -> str:
    """Format seconds to SRT/VTT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    if vtt:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}" 