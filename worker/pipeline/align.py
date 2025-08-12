"""
Word-level alignment using WhisperX
"""

import os
import json
from typing import Dict, Any, List
import whisperx
from pipeline.artifacts import log_step, write_json

def align_transcript(audio_path: str, segments: List[Dict[str, Any]], language: str = "en") -> Dict[str, Any]:
    """Align transcript to audio using WhisperX."""
    # Load the audio
    audio = whisperx.load_audio(audio_path)
    
    # Load the model - use float32 for CPU compatibility
    model = whisperx.load_model("base", device="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu", compute_type="float32")
    
    # Get device for alignment
    device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # Align the transcript - using the correct parameter order for WhisperX
    try:
        result = whisperx.align(
            segments,
            model,
            audio,
            language,
            device=device,
            return_char_alignments=False
        )
    except Exception as e:
        print(f"WhisperX alignment failed: {e}")
        print(f"Parameters: segments={len(segments)}, model={type(model)}, audio={type(audio)}, language={language}, device={device}")
        # Return empty result on failure
        return {
            "aligned_words": [],
            "segments": segments
        }
    
    # Extract word-level alignments
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

def align_with_whisperx(audio_path: str, asr_result: Dict[str, Any]) -> Dict[str, Any]:
    """Align ASR result using WhisperX."""
    # Convert our format to WhisperX format
    segments = []
    for i, segment in enumerate(asr_result["segments"]):
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"]
        })
    
    # Perform alignment
    alignment_result = align_transcript(
        audio_path,
        segments,
        asr_result.get("language", "en")
    )
    
    return alignment_result 