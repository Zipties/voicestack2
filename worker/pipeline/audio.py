"""
Audio processing utilities using ffmpeg
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional

def get_audio_info(file_path: str) -> Dict[str, Any]:
    """Get audio file information using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    
    info = json.loads(result.stdout)
    
    # Find audio stream
    audio_stream = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break
    
    if not audio_stream:
        raise RuntimeError("No audio stream found")
    
    return {
        "duration": float(info.get("format", {}).get("duration", 0)),
        "sample_rate": int(audio_stream.get("sample_rate", 0)),
        "channels": int(audio_stream.get("channels", 0)),
        "codec": audio_stream.get("codec_name", "unknown"),
        "bit_rate": int(audio_stream.get("bit_rate", 0))
    }

def normalize_audio(input_path: str, output_path: str) -> Dict[str, Any]:
    """Normalize audio to EBU R128 standards and convert to 16kHz mono WAV."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", "16000", "-ac", "1",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg normalization failed: {result.stderr}")
    
    # Get info about the normalized file
    info = get_audio_info(output_path)
    
    return info

def extract_audio_from_video(input_path: str, output_path: str) -> Dict[str, Any]:
    """Extract audio from video file and normalize."""
    return normalize_audio(input_path, output_path)

def create_opus_archive(input_path: str, job_id: str) -> str:
    """Create Opus archive of the original file."""
    archive_dir = "/data/archival"
    Path(archive_dir).mkdir(parents=True, exist_ok=True)
    
    archive_path = os.path.join(archive_dir, f"{job_id}.opus")
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:a", "libopus", "-b:a", "24k", "-vbr", "on",
        archive_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg opus archive failed: {result.stderr}")
    
    return archive_path

def process_audio_file(input_path: str, job_id: str) -> Dict[str, Any]:
    """Process audio file: normalize and create archive."""
    # Create normalized 16kHz mono WAV
    normalized_path = os.path.join("/data/artifacts", job_id, "raw_16k_mono.wav")
    Path(os.path.dirname(normalized_path)).mkdir(parents=True, exist_ok=True)
    
    # Check if input is video
    input_info = get_audio_info(input_path)
    is_video = input_info.get("codec") != "pcm_s16le"  # Simple heuristic
    
    if is_video:
        # Extract and normalize audio from video
        audio_info = extract_audio_from_video(input_path, normalized_path)
    else:
        # Normalize audio file
        audio_info = normalize_audio(input_path, normalized_path)
    
    # Create Opus archive
    archive_path = create_opus_archive(input_path, job_id)
    
    return {
        "normalized_path": normalized_path,
        "archive_path": archive_path,
        "duration": audio_info["duration"],
        "sample_rate": audio_info["sample_rate"],
        "channels": audio_info["channels"],
        "is_video": is_video
    } 