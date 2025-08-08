import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/voicestack")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Directories
    INPUTS_DIR: str = os.getenv("INPUTS_DIR", "/data/inputs")
    ARCHIVAL_DIR: str = os.getenv("ARCHIVAL_DIR", "/data/archival")
    ARTIFACTS_DIR: str = os.getenv("ARTIFACTS_DIR", "/data/artifacts")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "/data/models")
    
    # Security
    API_TOKEN: Optional[str] = os.getenv("API_TOKEN")
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    def __init__(self):
        # Ensure directories exist
        for dir_path in [self.INPUTS_DIR, self.ARCHIVAL_DIR, self.ARTIFACTS_DIR, self.MODELS_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create model subdirectories
        for model_dir in ["whisper", "pyannote", "speechbrain", "llm"]:
            Path(f"{self.MODELS_DIR}/{model_dir}").mkdir(parents=True, exist_ok=True)

settings = Settings() 