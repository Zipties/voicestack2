"""
Simple ASR using transformers only (replaces faster-whisper)
"""

import os
import json
import torch
import torchaudio
from typing import Dict, Any, List
from transformers import pipeline, AutoModelForSpeechSeq2Seq, AutoProcessor

def load_whisper_pipeline(model_name: str = "base"):
    """Load whisper model using transformers pipeline."""
    # Try direct OpenAI Whisper models first, then fallback to alternatives
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
    
    # Check if HF_TOKEN is set
    hf_token = os.getenv("HF_TOKEN")
    print(f"HF_TOKEN found: {'Yes' if hf_token and hf_token != 'your_hf_token_here' else 'No'}")
    
    try:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        print(f"Using device: {device}, dtype: {torch_dtype}")
        
        # Try loading without authentication first (public models)
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
            batch_size=8,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        
        print(f"✓ Successfully loaded Whisper pipeline: {model_id}")
        return pipe
        
    except Exception as e:
        print(f"Failed to load model {model_id}: {e}")
        raise RuntimeError(f"Could not load Whisper model: {e}")

def transcribe_audio(audio_path: str, model_name: str = "base", compute_type: str = "float16") -> Dict[str, Any]:
    """Transcribe audio using transformers pipeline."""
    
    pipe = load_whisper_pipeline(model_name)
    
    print(f"Transcribing audio file: {audio_path}")
    
    try:
        # Load audio using torchaudio
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
        
        print(f"Transcription completed. Text: {result['text'][:100]}...")
        
        # Convert to our expected format
        segments_list = []
        
        if 'chunks' in result and result['chunks']:
            for i, chunk in enumerate(result['chunks']):
                segment_dict = {
                    "start": chunk['timestamp'][0] if chunk['timestamp'][0] is not None else 0.0,
                    "end": chunk['timestamp'][1] if chunk['timestamp'][1] is not None else len(audio) / sr,
                    "text": chunk['text'].strip(),
                    "words": []  # Transformers doesn't provide word-level by default
                }
                if segment_dict["text"]:  # Only add non-empty segments
                    segments_list.append(segment_dict)
        else:
            # Fallback: create single segment
            if result['text'].strip():
                segments_list.append({
                    "start": 0.0,
                    "end": len(audio) / sr,
                    "text": result['text'].strip(),
                    "words": []
                })
        
        return {
            "segments": segments_list,
            "language": "en",
            "language_probability": 1.0,
            "full_text": result['text']
        }
        
    except Exception as e:
        print(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}")