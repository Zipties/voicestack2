"""
ASR using original OpenAI whisper package (no HuggingFace dependency)
"""

import os
import tempfile
import subprocess
import json
from typing import Dict, Any, List

def transcribe_audio(audio_path: str, model_name: str = "base", compute_type: str = "float32") -> Dict[str, Any]:
    """Transcribe audio using original OpenAI whisper command line tool."""
    
    print(f"Using OpenAI whisper CLI for: {audio_path}")
    
    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Build whisper command
            cmd = [
                "whisper", 
                audio_path,
                "--model", model_name,
                "--output_format", "json",
                "--output_dir", temp_dir,
                "--verbose", "False"
            ]
            
            print(f"Running whisper command: {' '.join(cmd)}")
            
            # Run whisper
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                print(f"Whisper command failed: {result.stderr}")
                raise RuntimeError(f"Whisper failed: {result.stderr}")
            
            # Find the JSON output file - whisper uses the input filename as base
            audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
            json_file = os.path.join(temp_dir, f"{audio_basename}.json")
            
            if not os.path.exists(json_file):
                # List all files in temp_dir for debugging
                files = os.listdir(temp_dir)
                print(f"Files in temp_dir: {files}")
                raise RuntimeError(f"Expected output file not found: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                whisper_result = json.load(f)
            
            # Convert to our expected format
            segments = []
            for segment in whisper_result.get('segments', []):
                segments.append({
                    "start": float(segment.get('start', 0)),
                    "end": float(segment.get('end', 0)),
                    "text": segment.get('text', '').strip(),
                    "words": []  # Original whisper doesn't provide word-level by default
                })
            
            full_text = whisper_result.get('text', '').strip()
            
            print(f"OpenAI Whisper transcription completed: {len(full_text)} characters, {len(segments)} segments")
            
            return {
                "segments": segments,
                "language": whisper_result.get('language', 'en'),
                "language_probability": 1.0,
                "full_text": full_text
            }
            
    except subprocess.TimeoutExpired:
        print("Whisper command timed out")
        raise RuntimeError("Whisper transcription timed out")
    except Exception as e:
        print(f"OpenAI Whisper transcription failed: {e}")
        raise RuntimeError(f"OpenAI Whisper failed: {e}")