from typing import Optional, Dict, Any, Literal
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
    llm_provider: Optional[Literal["openai", "openrouter", "openai_compat"]] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None  # for openai_compat (LM Studio/Open WebUI/vLLM)
    llm_temperature: float = 0.2
    llm_top_p: float = 1.0
    llm_max_input_tokens: int = 4000
    llm_max_output_tokens: int = 512

class PresetConfig(BaseModel):
    name: str
    description: Optional[str] = None
    params: Dict[str, Any] = {}

class SecretsConfig(BaseModel):
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openai_compat_api_key: Optional[str] = None

class SettingsRequest(BaseModel):
    smtp: Optional[SMTPConfig] = None
    models: Optional[ModelConfig] = None
    presets: Optional[list[PresetConfig]] = None
    secrets: Optional[SecretsConfig] = None
    api_token: Optional[str] = None
    hf_token: Optional[str] = None

class SettingsResponse(BaseModel):
    smtp: Optional[SMTPConfig] = None
    models: ModelConfig
    presets: list[PresetConfig] = []
    secrets: Optional[SecretsConfig] = None
    api_token: Optional[str] = None
    hf_token: Optional[str] = None

    def mask_secrets(self) -> "SettingsResponse":
        """Return a copy with sensitive data masked for GET requests."""
        masked = self.model_copy()
        if masked.smtp:
            masked.smtp.password = "***"
        if masked.secrets:
            masked.secrets.openai_api_key = "***"
            masked.secrets.openrouter_api_key = "***"
            masked.secrets.openai_compat_api_key = "***"
        if masked.api_token:
            masked.api_token = "***"
        if masked.hf_token:
            masked.hf_token = "***"
        return masked 