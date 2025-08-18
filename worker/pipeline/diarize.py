"""
Speaker diarization using pyannote.audio with local model caching
"""

import os
import json
from typing import Dict, Any, List, Optional
from pyannote.audio import Pipeline
from pipeline.artifacts import log_step, write_json

# Global pipeline cache to avoid reloading
_pipeline_cache = None

def load_diarization_pipeline(hf_token: str) -> Pipeline:
    """Load pyannote.audio diarization pipeline with caching."""
    global _pipeline_cache
    
    # Return cached pipeline if available
    if _pipeline_cache is not None:
        print("✓ Using cached diarization pipeline")
        return _pipeline_cache
    
    print(f"Loading diarization pipeline with HF token: {hf_token[:10]}...")
    
    # Set cache directory for models to persist between container restarts
    cache_dir = "/app/model_cache"
    os.makedirs(cache_dir, exist_ok=True)
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    
    try:
        # Try to load from cache first (offline mode)
        try:
            print("Attempting to load pipeline from local cache...")
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization@2.1",
                cache_dir=cache_dir,
                local_files_only=True
            )
            print("✓ Loaded diarization pipeline from local cache")
            _pipeline_cache = pipeline
            return pipeline
        except Exception as cache_error:
            print(f"Cache load failed: {cache_error}")
            print("Downloading pipeline with HF token...")
        
        # Download with token if cache fails
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization@2.1",
            use_auth_token=hf_token,
            cache_dir=cache_dir
        )
        
        if pipeline is None:
            raise RuntimeError(
                "Pipeline.from_pretrained returned None. This usually means:\n"
                "1. You need to accept user conditions at: https://huggingface.co/pyannote/speaker-diarization\n"
                "2. You need to accept user conditions at: https://huggingface.co/pyannote/segmentation\n"
                "3. Your HF token may be invalid or lack the required permissions\n"
                "4. The model may not be accessible from your current location"
            )
        
        print("✓ Diarization pipeline downloaded and cached successfully")
        _pipeline_cache = pipeline
        return pipeline
    
    except Exception as e:
        error_msg = str(e).lower()
        if "401" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg:
            raise RuntimeError(
                f"Authentication failed when loading diarization pipeline.\n"
                f"Please ensure:\n"
                f"1. You have accepted user conditions at: https://huggingface.co/pyannote/speaker-diarization\n"
                f"2. You have accepted user conditions at: https://huggingface.co/pyannote/segmentation\n"
                f"3. Your HF token is valid and has the required permissions\n"
                f"Original error: {e}"
            ) from e
        else:
            print(f"Failed to load diarization pipeline: {e}")
            raise RuntimeError(f"Could not load diarization pipeline: {e}") from e

def diarize_audio(audio_path: str, hf_token: str) -> Dict[str, Any]:
    """Perform speaker diarization on audio."""
    pipeline = load_diarization_pipeline(hf_token)
    
    # Run diarization
    diarization = pipeline(audio_path)
    
    # Extract speaker turns
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })
    
    return {
        "turns": turns,
        "speakers": list(set(turn["speaker"] for turn in turns))
    }

def map_words_to_speakers(aligned_words: List[Dict[str, Any]], diarization_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Map aligned words to speakers based on diarization turns."""
    turns = diarization_result["turns"]
    
    # Create a mapping of time ranges to speakers
    speaker_map = {}
    for turn in turns:
        for time in range(int(turn["start"] * 100), int(turn["end"] * 100)):
            speaker_map[time / 100] = turn["speaker"]
    
    # Map each word to a speaker
    for word in aligned_words:
        word_start = word["start"]
        word_end = word["end"]
        
        # Find the speaker for the middle of the word
        word_middle = (word_start + word_end) / 2
        
        # Find overlapping turn
        speaker = "Unknown"
        for turn in turns:
            if turn["start"] <= word_middle <= turn["end"]:
                speaker = turn["speaker"]
                break
        
        word["speaker"] = speaker
    
    return aligned_words

def assign_speakers_to_segments(segments: List[Dict[str, Any]], word_speakers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign speakers to segments based on majority vote of words."""
    # Group words by segment
    segment_words = {}
    for word in word_speakers:
        segment_id = word.get("segment_id", 0)
        if segment_id not in segment_words:
            segment_words[segment_id] = []
        segment_words[segment_id].append(word)
    
    # Assign speaker to each segment by majority vote
    for i, segment in enumerate(segments):
        if i in segment_words:
            words = segment_words[i]
            speaker_counts = {}
            
            for word in words:
                speaker = word.get("speaker", "Unknown")
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            # Find most common speaker
            if speaker_counts:
                segment["speaker"] = max(speaker_counts, key=speaker_counts.get)
            else:
                segment["speaker"] = "Unknown"
        else:
            segment["speaker"] = "Unknown"
    
    return segments 