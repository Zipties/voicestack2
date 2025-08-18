"""
ASR using faster-whisper with transformers fallback
"""

import os
import json
from typing import Dict, Any, List
from pipeline.artifacts import log_step, write_json

# Try faster-whisper first, fall back to transformers
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
    print("✓ faster-whisper available")
except ImportError as e:
    print(f"faster-whisper not available: {e}")
    print("Using transformers fallback")
    FASTER_WHISPER_AVAILABLE = False
    from pipeline.asr_transformers import transcribe_audio_transformers, transcribe_with_simple_chunking

def load_whisper_model(model_name: str = "base", compute_type: str = "float16"):
    """Load faster-whisper model."""
    # Map model names to proper HuggingFace model IDs that work with faster-whisper
    # faster-whisper works with the original Whisper models, not the OpenAI ones
    model_mapping = {
        "tiny": "Systran/faster-whisper-tiny",
        "base": "Systran/faster-whisper-base", 
        "small": "Systran/faster-whisper-small",
        "medium": "Systran/faster-whisper-medium",
        "large": "Systran/faster-whisper-large",
        "large-v2": "Systran/faster-whisper-large-v2"
    }
    
    # Get the proper model ID, fallback to base if not found
    hf_model_id = model_mapping.get(model_name, "Systran/faster-whisper-base")
    
    print(f"Loading Whisper model: {model_name} -> {hf_model_id}")
    
    # Use CPU by default, GPU if available
    device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
    try:
        model = WhisperModel(
            hf_model_id,
            device=device,
            compute_type=compute_type
        )
        print(f"✓ Successfully loaded Whisper model: {hf_model_id}")
        return model
    except Exception as e:
        print(f"Failed to load model {hf_model_id}: {e}")
        print("Falling back to base model...")
        
        # Fallback to base model
        try:
            model = WhisperModel(
                "Systran/faster-whisper-base",
                device=device,
                compute_type=compute_type
            )
            print("✓ Successfully loaded fallback Whisper base model")
            return model
        except Exception as e2:
            print(f"Failed to load fallback model: {e2}")
            raise RuntimeError(f"Could not load any Whisper model: {e2}")

def transcribe_audio(audio_path: str, model_name: str = "base", compute_type: str = "float16") -> Dict[str, Any]:
    """Transcribe audio using faster-whisper or transformers fallback."""
    
    if not FASTER_WHISPER_AVAILABLE:
        print("Using transformers fallback for ASR")
        return transcribe_audio_transformers(audio_path, model_name)
    
    try:
        model = load_whisper_model(model_name, compute_type)
        
        # Transcribe with word-level timestamps
        # Don't specify language initially - let the model auto-detect
        segments, info = model.transcribe(
            audio_path,
            word_timestamps=True
        )
        
        # Convert to list and format
        segments_list = []
        for segment in segments:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": []
            }
            
            # Add word-level timestamps
            if segment.words:
                for word in segment.words:
                    segment_dict["words"].append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    })
            
            segments_list.append(segment_dict)
        
        return {
            "segments": segments_list,
            "language": info.language if hasattr(info, 'language') else "en",
            "language_probability": info.language_probability if hasattr(info, 'language_probability') else 1.0
        }
        
    except Exception as e:
        print(f"faster-whisper failed: {e}")
        print("Falling back to transformers ASR")
        return transcribe_audio_transformers(audio_path, model_name)

def transcribe_with_chunking(audio_path: str, model_name: str = "base", compute_type: str = "float16", chunk_duration: int = 30) -> Dict[str, Any]:
    """Transcribe long audio files by chunking."""
    import librosa
    
    # Get audio duration
    duration = librosa.get_duration(path=audio_path)
    
    if duration <= chunk_duration * 2:
        # Short file, transcribe directly
        return transcribe_audio(audio_path, model_name, compute_type)
    
    if not FASTER_WHISPER_AVAILABLE:
        print("Using transformers chunking fallback")
        return transcribe_with_simple_chunking(audio_path, model_name, chunk_duration)
    
    try:
        # Long file, use chunking
        model = load_whisper_model(model_name, compute_type)
        
        # Load audio
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Calculate chunks
        chunk_samples = chunk_duration * sr
        overlap_samples = int(5 * sr)  # 5 second overlap
        
        segments_list = []
        current_time = 0
        
        for i in range(0, len(audio), chunk_samples - overlap_samples):
            chunk_start = i
            chunk_end = min(i + chunk_samples, len(audio))
            
            # Extract chunk
            chunk = audio[chunk_start:chunk_end]
            
            # Save temporary chunk file
            temp_chunk_path = f"/tmp/chunk_{i}.wav"
            librosa.output.write_wav(temp_chunk_path, chunk, sr)
            
            try:
                # Transcribe chunk
                chunk_segments, info = model.transcribe(
                    temp_chunk_path,
                    word_timestamps=True
                )
                
                # Adjust timestamps and add to results
                for segment in chunk_segments:
                segment_dict = {
                    "start": segment.start + current_time,
                    "end": segment.end + current_time,
                    "text": segment.text.strip(),
                    "words": []
                }
                
                # Adjust word timestamps
                if segment.words:
                    for word in segment.words:
                        segment_dict["words"].append({
                            "word": word.word,
                            "start": word.start + current_time,
                            "end": word.end + current_time,
                            "probability": word.probability
                        })
                
                segments_list.append(segment_dict)
            
            current_time += chunk_duration - (overlap_samples / sr)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_chunk_path):
                os.remove(temp_chunk_path)
    
        return {
            "segments": segments_list,
            "language": "en",  # Default for chunked processing
            "language_probability": 1.0
        }
        
    except Exception as e:
        print(f"faster-whisper chunking failed: {e}")
        print("Falling back to transformers chunking")
        return transcribe_with_simple_chunking(audio_path, model_name, chunk_duration) 