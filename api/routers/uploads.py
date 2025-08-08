import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from rq import Queue
from redis import Redis
from db.session import get_db
from models.job import Job
from models.asset import Asset
from core.config import settings
from core.security import require_bearer

router = APIRouter()

# Initialize Redis and RQ
redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue(connection=redis_conn)

def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return Path(filename).suffix.lower()

def guess_media_type(extension: str) -> str:
    """Guess media type from file extension."""
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
    
    if extension in audio_extensions:
        return 'audio'
    elif extension in video_extensions:
        return 'video'
    else:
        return 'unknown'

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    email_to: Optional[str] = Form(None),
    preset_id: Optional[str] = Form(None),
    params: Optional[str] = Form("{}"),
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Upload a media file and enqueue a processing job."""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_id = str(uuid.uuid4())
    extension = get_file_extension(file.filename)
    unique_filename = f"{timestamp}_{file_id}{extension}"
    
    # Save file to inputs directory
    input_path = os.path.join(settings.INPUTS_DIR, unique_filename)
    
    try:
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Parse params JSON
    try:
        job_params = json.loads(params) if params else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in params")
    
    # Create job record
    job = Job(
        status="QUEUED",
        progress=0,
        params=job_params,
        email_to=email_to
    )
    db.add(job)
    db.flush()  # Get the job ID
    
    # Create asset record
    asset = Asset(
        job_id=job.id,
        input_path=input_path,
        media_type=guess_media_type(extension)
    )
    db.add(asset)
    db.commit()
    
    # Enqueue RQ job (stub for now)
    try:
        queue.enqueue(
            "worker.pipeline.run_job",
            str(job.id),
            input_path,
            params,
            job_timeout=3600  # 1 hour timeout
        )
    except Exception as e:
        # If enqueue fails, mark job as failed
        job.status = "FAILED"
        job.log_path = f"Enqueue failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {str(e)}")
    
    return {"job_id": str(job.id)} 