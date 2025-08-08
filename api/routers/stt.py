from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from core.security import require_bearer

router = APIRouter()

@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    _: str = Depends(require_bearer)
):
    """Accept audio and immediately return 202 with enqueued job (stub)."""
    # This is a stub endpoint for Phase 1
    # In Phase 2, this will accept audio and enqueue a job for immediate processing
    
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    # For now, return 501 Not Implemented
    # In Phase 2, this will save the audio and enqueue a job
    raise HTTPException(
        status_code=501, 
        detail="STT endpoint not implemented in Phase 1"
    ) 