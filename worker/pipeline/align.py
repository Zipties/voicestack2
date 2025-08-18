"""
Word-level alignment using WhisperX without ctranslate2
"""

import os
import json
from typing import Dict, Any, List
import whisperx

def align_with_whisperx(audio_path: str, asr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform word-level alignment using WhisperX.
    Uses the alignment model without ctranslate2.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load audio
    audio = whisperx.load_audio(audio_path)
    
    # Load alignment model
    model_a, metadata = whisperx.load_align_model(
        language_code=asr_result.get("language", "en"),
        device=device
    )
    
    # Prepare segments for alignment
    segments = asr_result["segments"]
    
    # Perform alignment
    result = whisperx.align(
        segments,
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False
    )
    
    # Extract aligned words
    aligned_words = []
    for segment in result["segments"]:
        if "words" in segment:
            for word in segment["words"]:
                aligned_words.append({
                    "word": word["word"],
                    "start": word["start"],
                    "end": word["end"],
                    "segment_id": segment.get("id", 0)
                })
    
    return {
        "aligned_words": aligned_words,
        "segments": result["segments"]
    }

# Import torch for device detection
import torch
