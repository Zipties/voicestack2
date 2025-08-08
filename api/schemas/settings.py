from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

class SMTPConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    from_email: str
    default_to: Optional[str] = None
    use_tls: bool = True

class ModelConfig(BaseModel):
    whisper_model: str = "base"
    whisper_compute_type: str = "float16"
    llm_provider: str = "openai"  # openai, openrouter, local
    llm_model: str = "gpt-3.5-turbo"
    llm_max_input_tokens: int = 4000
    llm_max_output_tokens: int = 1000

class PresetConfig(BaseModel):
    name: str
    description: Optional[str] = None
    params: Dict[str, Any] = {}

class SettingsRequest(BaseModel):
    smtp: Optional[SMTPConfig] = None
    models: Optional[ModelConfig] = None
    presets: Optional[list[PresetConfig]] = None
    api_token: Optional[str] = None
    hf_token: Optional[str] = None

class SettingsResponse(BaseModel):
    smtp: Optional[SMTPConfig] = None
    models: ModelConfig
    presets: list[PresetConfig] = []
    api_token: Optional[str] = None
    hf_token: Optional[str] = None

    def mask_secrets(self) -> "SettingsResponse":
        """Return a copy with sensitive data masked for GET requests."""
        masked = self.model_copy()
        if masked.smtp:
            masked.smtp.password = "***"
        if masked.api_token:
            masked.api_token = "***"
        if masked.hf_token:
            masked.hf_token = "***"
        return masked 