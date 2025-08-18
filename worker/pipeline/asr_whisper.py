"""
ASR using OpenAI Whisper (no ctranslate2 dependency)
"""

import os
import json
import whisper
from typing import Dict, Any, List
from pathlib import Path

def transcribe_audio(audio_path: str, model_name: str = "base", compute_type: str = "float32") -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper.
    
    Args:
        audio_path: Path to the audio file
        model_name: Whisper model name (tiny, base, small, medium, large)
        compute_type: Ignored (kept for compatibility)
    
    Returns:
        Dictionary with segments containing text and timestamps
    """
    print(f"Loading Whisper model: {model_name}")
    
    # Load model with CPU or GPU based on availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)
    
    print(f"Transcribing audio file: {audio_path}")
    
    # Transcribe with word timestamps
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        verbose=True,
        language=None,  # Auto-detect language
        task="transcribe"
    )
    
    # Format segments for compatibility with the rest of the pipeline
    segments = []
    for segment in result["segments"]:
        segment_data = {
            "id": segment["id"],
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
            "words": []
        }
        
        # Add word-level timestamps if available
        if "words" in segment:
            for word in segment["words"]:
                segment_data["words"].append({
                    "word": word["word"],
                    "start": word["start"],
                    "end": word["end"],
                    "probability": word.get("probability", 1.0)
                })
        
        segments.append(segment_data)
    
    return {
        "segments": segments,
        "language": result.get("language", "unknown"),
        "text": result.get("text", "")
    }

# Import torch for device detection
import torch
