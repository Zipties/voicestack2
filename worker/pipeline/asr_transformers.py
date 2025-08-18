"""
ASR using transformers pipeline (alternative to faster-whisper)
This version avoids ctranslate2 dependency issues
"""

import os
import json
import torch
import torchaudio
import soundfile as sf
from typing import Dict, Any, List
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor
from pipeline.artifacts import log_step, write_json

def load_whisper_pipeline(model_name: str = "base"):
    """Load whisper model using transformers pipeline."""
    # Map model names to HuggingFace model IDs
    model_mapping = {
        "tiny": "openai/whisper-tiny",
        "base": "openai/whisper-base", 
        "small": "openai/whisper-small",
        "medium": "openai/whisper-medium",
        "large": "openai/whisper-large",
        "large-v2": "openai/whisper-large-v2",
        "large-v3": "openai/whisper-large-v3"
    }
    
    model_id = model_mapping.get(model_name, "openai/whisper-base")
    
    print(f"Loading Whisper model via transformers: {model_name} -> {model_id}")
    
    try:
        # Check if GPU is available
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        print(f"Using device: {device}, dtype: {torch_dtype}")
        
        # Load model and processor
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, 
            torch_dtype=torch_dtype, 
            low_cpu_mem_usage=True, 
            use_safetensors=True
        )
        model.to(device)
        
        processor = AutoProcessor.from_pretrained(model_id)
        
        # Create pipeline
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        
        print(f"✓ Successfully loaded Whisper pipeline: {model_id}")
        return pipe
        
    except Exception as e:
        print(f"Failed to load model {model_id}: {e}")
        print("Falling back to base model...")
        
        # Fallback to base model
        try:
            model_id = "openai/whisper-base"
            device = "cpu"  # Use CPU for fallback
            torch_dtype = torch.float32
            
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, 
                torch_dtype=torch_dtype, 
                low_cpu_mem_usage=True, 
                use_safetensors=True
            )
            model.to(device)
            
            processor = AutoProcessor.from_pretrained(model_id)
            
            pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=8,  # Smaller batch for CPU
                return_timestamps=True,
                torch_dtype=torch_dtype,
                device=device,
            )
            
            print("✓ Successfully loaded fallback Whisper base model")
            return pipe
            
        except Exception as e2:
            print(f"Failed to load fallback model: {e2}")
            raise RuntimeError(f"Could not load any Whisper model: {e2}")

def transcribe_audio_transformers(audio_path: str, model_name: str = "base") -> Dict[str, Any]:
    """Transcribe audio using transformers pipeline."""
    pipe = load_whisper_pipeline(model_name)
    
    print(f"Transcribing audio file: {audio_path}")
    
    try:
        # Load audio using torchaudio (transformers expects 16kHz)
        audio, sr = torchaudio.load(audio_path)
        
        # Resample to 16kHz if needed
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            audio = resampler(audio)
            sr = 16000
        
        # Convert to numpy array for transformers
        audio = audio.squeeze().numpy()
        
        # Transcribe with timestamps
        result = pipe(audio, return_timestamps=True, generate_kwargs={"language": "english"})
        
        print(f"Transcription completed. Text length: {len(result['text'])}")
        
        # Convert to our expected format
        segments_list = []
        
        if 'chunks' in result:
            # Process chunks (word-level or sentence-level timestamps)
            for i, chunk in enumerate(result['chunks']):
                segment_dict = {
                    "start": chunk['timestamp'][0] if chunk['timestamp'][0] is not None else 0.0,
                    "end": chunk['timestamp'][1] if chunk['timestamp'][1] is not None else len(audio) / sr,
                    "text": chunk['text'].strip(),
                    "words": []  # Transformers doesn't provide word-level by default
                }
                segments_list.append(segment_dict)
        else:
            # Fallback: create single segment
            segments_list.append({
                "start": 0.0,
                "end": len(audio) / sr,
                "text": result['text'].strip(),
                "words": []
            })
        
        return {
            "segments": segments_list,
            "language": "en",  # Default to English
            "language_probability": 1.0,
            "full_text": result['text']
        }
        
    except Exception as e:
        print(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}")

def transcribe_with_simple_chunking(audio_path: str, model_name: str = "base", chunk_duration: int = 30) -> Dict[str, Any]:
    """Transcribe long audio files by simple chunking."""
    
    # Get audio duration using torchaudio
    info = torchaudio.info(audio_path)
    duration = info.num_frames / info.sample_rate
    
    if duration <= chunk_duration * 2:
        # Short file, transcribe directly
        return transcribe_audio_transformers(audio_path, model_name)
    
    print(f"Audio duration: {duration:.2f}s, using chunking with {chunk_duration}s chunks")
    
    # Long file, use chunking
    pipe = load_whisper_pipeline(model_name)
    
    # Load audio using torchaudio
    audio, sr = torchaudio.load(audio_path)
    
    # Resample to 16kHz if needed
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        audio = resampler(audio)
        sr = 16000
    
    # Convert to numpy for processing
    audio = audio.squeeze().numpy()
    
    # Calculate chunks
    chunk_samples = chunk_duration * sr
    
    segments_list = []
    current_time = 0
    
    for i in range(0, len(audio), chunk_samples):
        chunk_start = i
        chunk_end = min(i + chunk_samples, len(audio))
        
        # Extract chunk
        chunk = audio[chunk_start:chunk_end]
        chunk_duration_actual = len(chunk) / sr
        
        print(f"Processing chunk {i//chunk_samples + 1}: {current_time:.1f}s - {current_time + chunk_duration_actual:.1f}s")
        
        try:
            # Transcribe chunk
            result = pipe(chunk, return_timestamps=True, generate_kwargs={"language": "english"})
            
            # Add to results with adjusted timestamps
            if 'chunks' in result and result['chunks']:
                for chunk_data in result['chunks']:
                    segment_dict = {
                        "start": (chunk_data['timestamp'][0] or 0.0) + current_time,
                        "end": (chunk_data['timestamp'][1] or chunk_duration_actual) + current_time,
                        "text": chunk_data['text'].strip(),
                        "words": []
                    }
                    if segment_dict["text"]:  # Only add non-empty segments
                        segments_list.append(segment_dict)
            else:
                # Fallback: single segment for chunk
                if result['text'].strip():
                    segments_list.append({
                        "start": current_time,
                        "end": current_time + chunk_duration_actual,
                        "text": result['text'].strip(),
                        "words": []
                    })
            
            current_time += chunk_duration_actual
            
        except Exception as e:
            print(f"Failed to process chunk {i//chunk_samples + 1}: {e}")
            # Continue with next chunk
            current_time += chunk_duration_actual
            continue
    
    # Combine all text
    full_text = " ".join([seg["text"] for seg in segments_list])
    
    return {
        "segments": segments_list,
        "language": "en",
        "language_probability": 1.0,
        "full_text": full_text
    }