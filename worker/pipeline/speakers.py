"""
Speaker embeddings and identification using SpeechBrain ECAPA
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from speechbrain.pretrained import EncoderClassifier
from pipeline.artifacts import log_step, write_json
from db import get_db, Speaker, Embedding
from sqlalchemy.orm import Session

def load_ecapa_model():
    """Load SpeechBrain ECAPA model."""
    model = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="/data/models/speechbrain/spkrec-ecapa-voxceleb"
    )
    return model

def extract_speaker_embeddings(audio_path: str, speaker_turns: List[Dict[str, Any]], model) -> List[Dict[str, Any]]:
    """Extract embeddings for each speaker turn."""
    embeddings = []
    
    for turn in speaker_turns:
        start_time = turn["start"]
        end_time = turn["end"]
        speaker_label = turn["speaker"]
        
        # Extract audio segment
        import librosa
        audio, sr = librosa.load(audio_path, sr=16000)
        
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        
        segment_audio = audio[start_sample:end_sample]
        
        # Skip very short segments
        if len(segment_audio) < sr * 0.5:  # Less than 0.5 seconds
            continue
        
        # Save temporary segment using soundfile instead of deprecated librosa.output
        import soundfile as sf
        temp_path = f"/tmp/speaker_{speaker_label}_{start_time}.wav"
        sf.write(temp_path, segment_audio, sr)
        
        try:
            # Extract embedding
            embedding = model.encode_batch([temp_path])
            embedding_vector = embedding.squeeze().cpu().numpy()
            
            embeddings.append({
                "speaker_label": speaker_label,
                "start": start_time,
                "end": end_time,
                "embedding": embedding_vector.tolist()
            })
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return embeddings

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def find_similar_speaker(embedding: List[float], db: Session, threshold: float = 0.3) -> Optional[Speaker]:
    """Find similar speaker in database using cosine similarity."""
    # Get all existing embeddings
    existing_embeddings = db.query(Embedding).all()
    
    best_similarity = 0.0
    best_speaker = None
    
    for emb in existing_embeddings:
        similarity = cosine_similarity(embedding, emb.vector)
        if similarity > best_similarity:
            best_similarity = similarity
            best_speaker = emb.speaker
    
    if best_similarity >= threshold:
        return best_speaker
    
    return None

def create_or_assign_speaker(speaker_label: str, embedding: List[float], db: Session, threshold: float = 0.3) -> Speaker:
    """Create new speaker or assign to existing one."""
    # Try to find similar speaker
    existing_speaker = find_similar_speaker(embedding, db, threshold)
    
    if existing_speaker:
        # Add embedding to existing speaker
        new_embedding = Embedding(
            speaker_id=existing_speaker.id,
            vector=embedding
        )
        db.add(new_embedding)
        return existing_speaker
    else:
        # Create new speaker
        # Convert speaker label to readable name
        if speaker_label.startswith("SPEAKER_"):
            # Generate a readable name
            speaker_num = speaker_label.split("_")[1]
            speaker_name = f"Speaker {chr(65 + int(speaker_num))}"  # A, B, C, etc.
        else:
            speaker_name = speaker_label
        
        new_speaker = Speaker(name=speaker_name, is_trusted=False)
        db.add(new_speaker)
        db.flush()  # Get the ID
        
        # Add embedding
        new_embedding = Embedding(
            speaker_id=new_speaker.id,
            vector=embedding
        )
        db.add(new_embedding)
        
        return new_speaker

def process_speaker_embeddings(audio_path: str, diarization_result: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Process speaker embeddings and create/assign speakers."""
    model = load_ecapa_model()
    
    # Extract embeddings for each speaker turn
    embeddings = extract_speaker_embeddings(audio_path, diarization_result["turns"], model)
    
    # Process each speaker
    speaker_mapping = {}
    
    for emb_data in embeddings:
        speaker_label = emb_data["speaker_label"]
        embedding = emb_data["embedding"]
        
        # Create or assign speaker
        speaker = create_or_assign_speaker(speaker_label, embedding, db)
        speaker_mapping[speaker_label] = speaker
    
    db.commit()
    
    return {
        "speaker_mapping": {label: speaker.id for label, speaker in speaker_mapping.items()},
        "embeddings_count": len(embeddings)
    } 