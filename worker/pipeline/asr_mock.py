"""
Mock ASR implementation that creates realistic transcription output
This is used when real ASR models are not available
"""

import os
import json
import torchaudio
from typing import Dict, Any, List

def transcribe_audio(audio_path: str, model_name: str = "base", compute_type: str = "float32") -> Dict[str, Any]:
    """Mock transcribe audio function that creates realistic output."""
    
    print(f"Mock transcribing audio file: {audio_path}")
    
    try:
        # Get audio duration for realistic segment timing
        info = torchaudio.info(audio_path)
        duration = info.num_frames / info.sample_rate
        
        print(f"Audio duration: {duration:.2f} seconds")
        
        # Create realistic mock segments based on duration
        segments = []
        current_time = 0.0
        segment_duration = min(5.0, duration / 3)  # 3-5 second segments
        
        # Generate more realistic sample texts based on duration and common speech patterns
        sample_texts = [
            "Hello, this is a test recording for the voice transcription system.",
            "The audio quality seems to be working well today.",
            "I'm testing the new transcription features and functionality.",
            "This is an example of continuous speech that we might encounter.",
            "The system should be able to handle different types of audio content.",
            "Thank you for trying out the VoiceStack transcription service.",
            "We hope this demonstration shows the capabilities of our platform.",
            "Please let us know if you have any questions or feedback.",
            "The mock transcription is working as expected.",
            "This concludes our test of the audio processing pipeline."
        ]
        
        text_index = 0
        while current_time < duration and text_index < len(sample_texts):
            end_time = min(current_time + segment_duration, duration)
            
            segment = {
                "start": round(current_time, 2),
                "end": round(end_time, 2),
                "text": sample_texts[text_index],
                "words": []  # Mock doesn't provide word-level timing
            }
            segments.append(segment)
            
            current_time = end_time
            text_index += 1
            
            if text_index >= len(sample_texts):
                text_index = 0  # Loop back if we need more segments
        
        # If audio is very short, create at least one segment
        if not segments:
            segments.append({
                "start": 0.0,
                "end": duration,
                "text": "This is a test audio transcription.",
                "words": []
            })
        
        full_text = " ".join([seg["text"] for seg in segments])
        
        print(f"Mock transcription completed: {len(full_text)} characters, {len(segments)} segments")
        
        return {
            "segments": segments,
            "language": "en",
            "language_probability": 1.0,
            "full_text": full_text
        }
        
    except Exception as e:
        print(f"Mock transcription failed: {e}")
        # Even if we can't read the audio file, return something
        return {
            "segments": [{
                "start": 0.0,
                "end": 10.0,
                "text": "Hello, this is a demonstration transcription. The audio file has been processed successfully using our mock transcription system.",
                "words": []
            }],
            "language": "en", 
            "language_probability": 1.0,
            "full_text": "Hello, this is a demonstration transcription. The audio file has been processed successfully using our mock transcription system."
        }