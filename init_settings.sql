INSERT INTO settings (id, smtp_config, model_config, presets, secrets_config, api_token, hf_token) 
VALUES (
    1, 
    '{}', 
    '{"llm_provider": "openai_compat", "llm_model": "deepseek-r1-distill-qwen-7b", "llm_base_url": "http://host.docker.internal:1234/v1", "llm_temperature": 0.2, "llm_top_p": 1.0, "llm_max_output_tokens": 512, "whisper_model": "base"}', 
    '[]', 
    '{"openai_compat_api_key": "not-needed"}', 
    'changeme', 
    ''
) ON CONFLICT (id) DO UPDATE SET 
    model_config = EXCLUDED.model_config,
    secrets_config = EXCLUDED.secrets_config; 