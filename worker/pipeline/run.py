"""
Main pipeline runner for VoiceStack2
"""

import asyncio
import os
import json
import logging
import traceback
import uuid
from typing import Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session

# Import worker-specific modules using absolute paths
from pipeline.artifacts import log_step, write_json, write_text, write_srt, write_vtt
from pipeline.audio import process_audio_file

# Try to use OpenAI Whisper (no ctranslate2), fall back to other options
try:
    from pipeline.asr_whisper import transcribe_audio
    print("✓ Using OpenAI Whisper ASR (ctranslate2 bypassed)")
except ImportError as e:
    print(f"OpenAI Whisper import failed: {e}")
    try:
        from pipeline.asr import transcribe_audio
        print("✓ Using faster-whisper ASR")
    except (ImportError, SyntaxError) as e2:
        print(f"faster-whisper ASR failed: {e2}")
        print("Using simple transformers ASR fallback")
        from pipeline.asr_simple import transcribe_audio
from pipeline.align import align_with_whisperx
from pipeline.diarize import diarize_audio, map_words_to_speakers, assign_speakers_to_segments
from pipeline.speakers import process_speaker_embeddings
from pipeline.gpu_mutex import get_gpu_mutex

# Import database and models with fallback handling
try:
    from db import get_db, Job, Asset, Transcript, Segment, Tag
    print("✓ Imported models from db module")
except ImportError:
    print("Warning: Could not import from db module, trying direct imports...")
    try:
        # Try importing models directly
        from api.models.job import Job
        from api.models.asset import Asset
        from api.models.transcript import Transcript
        from api.models.segment import Segment
        from api.models.tag import Tag
        print("✓ Imported models directly from api.models")
    except ImportError as e:
        print(f"Failed to import models: {e}")
        # Create dummy classes for testing
        Job = Asset = Transcript = Segment = Tag = None

try:
    from llm import generate_metadata
    print("✓ Imported llm module")
except ImportError:
    print("Warning: Could not import llm module")
    generate_metadata = None

try:
    from api.schemas.common import JobStatus
    print("✓ Imported JobStatus from api.schemas.common")
except ImportError:
    print("Warning: Could not import JobStatus, using string values")
    class JobStatus:
        RUNNING = "RUNNING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

async def run_job(job_id: str, input_path: str, params: Dict[str, Any]) -> None:
    """Run the complete pipeline for a job."""
    # Convert job_id string to UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise RuntimeError(f"Invalid job ID format: {job_id}")
    
    # Get database session with error handling
    try:
        db = next(get_db())
        if db is None:
            raise RuntimeError("Failed to get database session")
        print(f"✓ Got database session: {db}")
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise RuntimeError(f"Database connection failed: {e}")
    
    job = None  # Declare job variable outside try block
    
    try:
        # Step 0: Setup
        log_step(job_id, "Starting pipeline")
        
        # Update job status - with better error handling
        if Job is not None:
            try:
                job = db.query(Job).filter(Job.id == job_uuid).first()
                if not job:
                    print(f"Warning: Job {job_id} not found in database, continuing without DB updates")
                else:
                    job.status = JobStatus.RUNNING.value
                    job.progress = 0
                    db.commit()
                    print(f"✓ Updated job status to RUNNING")
            except Exception as e:
                print(f"Warning: Failed to update job status: {e}")
                job = None
        else:
            print("Warning: Job model not available, skipping database updates")
        
        # Get settings with fallback
        settings_dict = {}
        try:
            if 'Setting' in globals() and Setting is not None:
                settings = db.query(Setting).filter(Setting.id == 1).first()
                if settings:
                    settings_dict = {
                        "model_config": settings.model_config or {},
                        "secrets_config": settings.secrets_config or {},
                        "hf_token": settings.hf_token
                    }
                    print("✓ Loaded settings from database")
                else:
                    print("Warning: No settings found in database, using defaults")
            else:
                print("Warning: Setting model not available, using defaults")
        except Exception as e:
            print(f"Warning: Failed to load settings: {e}")
        
        # Set default settings if none loaded
        if not settings_dict:
            settings_dict = {
                "model_config": {
                    "whisper_model": os.getenv("WHISPER_MODEL", "base"),
                    "whisper_compute_type": "float32"  # CPU compatible
                },
                "secrets_config": {},
                "hf_token": os.getenv("HF_TOKEN")
            }
            print("✓ Using environment variable settings")
        
        # Step 1: Audio processing
        log_step(job_id, "Processing audio file")
        audio_result = process_audio_file(input_path, job_id)
        
        # Update asset with metadata
        asset = None  # Initialize asset variable
        print(f"DEBUG: Asset model status: {Asset}, Job model status: {job}")
        if Asset is not None and job is not None:
            try:
                asset = db.query(Asset).filter(Asset.job_id == job_uuid).first()
                if asset:
                    asset.duration = audio_result["duration"]
                    asset.samplerate = audio_result["sample_rate"]
                    asset.channels = audio_result["channels"]
                    asset.archival_path = audio_result["archive_path"]
                    db.commit()
                    print("✓ Updated asset metadata")
                else:
                    print("Warning: Asset not found for job")
            except Exception as e:
                print(f"Warning: Failed to update asset: {e}")
                asset = None
        else:
            print("Warning: Asset model or job not available, skipping asset updates")
        
        if job:
            try:
                job.progress = 10
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 2: ASR
        log_step(job_id, "Running ASR")
        
        with get_gpu_mutex():
            whisper_model = settings_dict["model_config"].get("whisper_model", "base")
            # Use float32 for CPU compatibility, float16 only for GPU
            compute_type = "float32"  # Changed from float16 to float32 for CPU compatibility
            
            asr_result = transcribe_audio(
                audio_result["normalized_path"],
                whisper_model,
                compute_type
            )
        
        write_json(job_id, "asr_segments.json", asr_result)
        
        if job:
            try:
                job.progress = 40
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 3: Alignment
        log_step(job_id, "Running word-level alignment")
        
        with get_gpu_mutex():
            alignment_result = align_with_whisperx(
                audio_result["normalized_path"],
                asr_result
            )
        
        write_json(job_id, "aligned_words.json", alignment_result)
        
        if job:
            try:
                job.progress = 55
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 4: Diarization
        log_step(job_id, "Running speaker diarization")
        
        hf_token = settings_dict.get("hf_token")
        if not hf_token or hf_token == "your_hf_token_here":
            log_step(job_id, "Skipping diarization (no valid HF token)")
            diarization_result = {"turns": [], "speakers": []}
        else:
            try:
                with get_gpu_mutex():
                    diarization_result = diarize_audio(
                        audio_result["normalized_path"],
                        hf_token
                    )
                log_step(job_id, f"Diarization completed: {len(diarization_result.get('turns', []))} speaker turns")
            except Exception as diarization_error:
                log_step(job_id, f"Diarization failed (skipping): {diarization_error}")
                print(f"Warning: Diarization failed but continuing pipeline: {diarization_error}")
                diarization_result = {"turns": [], "speakers": []}
        
        write_json(job_id, "diarization.json", diarization_result)
        
        # Map words to speakers
        if diarization_result["turns"]:
            aligned_words = alignment_result["aligned_words"]
            word_speakers = map_words_to_speakers(aligned_words, diarization_result)
            write_json(job_id, "word_speakers.json", word_speakers)
            
            # Assign speakers to segments
            segments_with_speakers = assign_speakers_to_segments(
                asr_result["segments"],
                word_speakers
            )
        else:
            segments_with_speakers = asr_result["segments"]
            for segment in segments_with_speakers:
                segment["speaker"] = "Unknown"
        
        if job:
            try:
                job.progress = 70
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 5: Speaker embeddings
        log_step(job_id, "Processing speaker embeddings")
        
        if diarization_result["turns"]:
            try:
                with get_gpu_mutex():
                    speaker_result = process_speaker_embeddings(
                        audio_result["normalized_path"],
                        diarization_result,
                        db
                    )
            except Exception as e:
                log_step(job_id, f"Speaker embeddings failed (skipping): {e}")
                speaker_result = {"speaker_mapping": {}, "embeddings_count": 0}
        else:
            speaker_result = {"speaker_mapping": {}, "embeddings_count": 0}
        
        if job:
            try:
                job.progress = 80
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 6: Persist transcript and segments
        log_step(job_id, "Persisting transcript and segments")
        
        # Create transcript
        transcript_text = " ".join([seg["text"] for seg in segments_with_speakers])
        
        # Handle case where Asset model is not available
        if asset is None:
            print("Warning: Asset not available, skipping transcript persistence to database")
            # Still generate output files
            write_text(job_id, "transcript.txt", transcript_text)
            write_srt(job_id, segments_with_speakers)
            write_vtt(job_id, segments_with_speakers)
            
            # Save compact JSON without database IDs
            transcript_json = {
                "transcript": {
                    "text": transcript_text
                },
                "segments": segments_with_speakers,
                "speakers": list(speaker_result["speaker_mapping"].keys())
            }
            write_json(job_id, "transcript.json", transcript_json)
            
            log_step(job_id, "Generated output files (database persistence skipped)")
        else:
            # Asset is available, proceed with database persistence
            transcript = db.query(Transcript).filter(Transcript.asset_id == asset.id).first()
            if not transcript:
                transcript = Transcript(
                    asset_id=asset.id,
                    raw_text=transcript_text
                )
                db.add(transcript)
                db.flush()
            
            # Create segments
            for segment_data in segments_with_speakers:
                # Find speaker ID
                speaker_id = None
                if segment_data.get("speaker") != "Unknown":
                    speaker_label = segment_data["speaker"]
                    if speaker_label in speaker_result["speaker_mapping"]:
                        speaker_id = speaker_result["speaker_mapping"][speaker_label]
                
                segment = Segment(
                    transcript_id=transcript.id,
                    start=segment_data["start"],
                    end=segment_data["end"],
                    text=segment_data["text"],
                    word_timings=segment_data.get("words", []),
                    speaker_id=speaker_id,
                    original_speaker_label=segment_data.get("speaker")
                )
                db.add(segment)
            
            # Generate output files
            write_text(job_id, "transcript.txt", transcript_text)
            write_srt(job_id, segments_with_speakers)
            write_vtt(job_id, segments_with_speakers)
            
            # Save compact JSON
            transcript_json = {
                "transcript": {
                    "id": str(transcript.id),
                    "text": transcript_text
                },
                "segments": segments_with_speakers,
                "speakers": list(speaker_result["speaker_mapping"].keys())
            }
            write_json(job_id, "transcript.json", transcript_json)
            
            log_step(job_id, "Generated output files and persisted to database")
        
        if job:
            try:
                job.progress = 90
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 7: LLM metadata
        log_step(job_id, "Generating metadata with LLM")
        
        title, summary, tags = await generate_metadata(transcript_text, {})
        
        if title or summary or tags:
            # Update transcript if available
            if asset is not None and transcript is not None:
                if title:
                    transcript.title = title
                if summary:
                    transcript.summary = summary
                
                # Add tags
                for tag_text in tags:
                    tag = Tag(
                        transcript_id=transcript.id,
                        tag=tag_text,
                        source="LLM"
                    )
                    db.add(tag)
                
                db.commit()
                log_step(job_id, f"Generated metadata: title='{title}', summary='{summary}', tags={tags}")
            else:
                log_step(job_id, f"Generated metadata but skipped database update (asset/transcript not available): title='{title}', summary='{summary}', tags={tags}")
        else:
            log_step(job_id, "LLM metadata generation skipped (not configured or failed)")
        
        if job:
            try:
                job.progress = 95
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job progress: {e}")
        
        # Step 8: Finalize
        log_step(job_id, "Pipeline completed successfully")
        
        # Always try to update job status, even if job object wasn't found earlier
        final_job_updated = False
        if job:
            try:
                job.status = JobStatus.SUCCEEDED.value
                job.progress = 100
                db.commit()
                final_job_updated = True
                print(f"✓ Updated job {job_id} to SUCCEEDED with 100% progress")
            except Exception as e:
                print(f"Warning: Failed to update job status via job object: {e}")
        
        # Fallback: try direct database update if we have Job model but no job object
        if not final_job_updated and Job is not None:
            try:
                result = db.query(Job).filter(Job.id == job_uuid).update({
                    'status': JobStatus.SUCCEEDED.value,
                    'progress': 100
                })
                db.commit()
                if result > 0:
                    print(f"✓ Updated job {job_id} via direct query to SUCCEEDED with 100% progress")
                else:
                    print(f"Warning: Job {job_id} not found in database for direct update")
            except Exception as e:
                print(f"Warning: Failed to update job status via direct query: {e}")
        
        if not final_job_updated and Job is None:
            print(f"Warning: Cannot update job status - Job model not available")
        
    except Exception as e:
        # Handle errors
        error_msg = f"Pipeline failed: {str(e)}"
        log_step(job_id, error_msg)
        log_step(job_id, f"Traceback: {traceback.format_exc()}")
        
        if job:
            try:
                job.status = JobStatus.FAILED.value
                job.log_path = error_msg
                db.commit()
            except Exception as e:
                print(f"Warning: Failed to update job status: {e}")
        
        raise 