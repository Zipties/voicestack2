from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.session import get_db
from models.setting import Setting
from core.security import require_bearer

router = APIRouter()

class EmailTranscriptRequest(BaseModel):
    transcript_id: str
    to_email: str
    subject: str = "Transcript from VoiceStack"
    message: str = "Please find the attached transcript."

@router.post("/email/transcript")
def email_transcript(
    request: EmailTranscriptRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_bearer)
):
    """Send transcript via email (stub implementation)."""
    # Validate SMTP settings exist
    settings = db.query(Setting).filter(Setting.id == 1).first()
    if not settings or not settings.smtp_config:
        raise HTTPException(
            status_code=400, 
            detail="SMTP settings not configured"
        )
    
    # Validate transcript exists
    # In Phase 2, we'll add the actual transcript lookup and email sending
    
    # This is a stub - in Phase 2 we'll implement the actual email sending
    return {"message": "Email sent successfully (stub implementation)"} 