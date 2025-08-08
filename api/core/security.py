from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .config import settings

security = HTTPBearer(auto_error=False)

def require_bearer(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Validate bearer token and return the token if valid."""
    if not settings.API_TOKEN:
        # If no API token is configured, allow all requests
        return "no_token_configured"
    
    if not credentials or credentials.credentials != settings.API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing bearer token"
        )
    
    return credentials.credentials 