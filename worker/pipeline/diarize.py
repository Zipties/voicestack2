"""
Speaker diarization using pyannote.audio
"""

import os
import json
from typing import Dict, Any, List, Optional
from pyannote.audio import Pipeline
from pipeline.artifacts import log_step, write_json

def load_diarization_pipeline(hf_token: str) -> Pipeline:
    """Load pyannote.audio diarization pipeline."""
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=hf_token
    )
    
    return pipeline

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