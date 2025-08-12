"""
LLM utilities for metadata generation
"""

import json
import os
import re
import tiktoken
from typing import Dict, Any, List, Optional, Tuple
from providers.openai_client import OpenAIClient
from providers.openrouter_client import OpenRouterClient
from providers.openai_compat_client import OpenAICompatClient
from providers.base import LLMClient

def make_client(settings_row: Dict[str, Any]) -> Optional[LLMClient]:
    """Create LLM client based on environment variables."""
    provider = os.getenv("LLM_PROVIDER")
    print(f"DEBUG: LLM_PROVIDER = {provider}")
    
    if not provider:
        print("DEBUG: No LLM_PROVIDER set")
        return None
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("DEBUG: No OPENAI_API_KEY set")
            return None
        print("DEBUG: Creating OpenAI client")
        return OpenAIClient(api_key)
    
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("DEBUG: No OPENROUTER_API_KEY set")
            return None
        print("DEBUG: Creating OpenRouter client")
        return OpenRouterClient(api_key)
    
    elif provider == "openai_compat":
        api_key = os.getenv("OPENAI_COMPAT_API_KEY", "")  # Make API key optional for LM Studio
        base_url = os.getenv("LLM_BASE_URL")
        print(f"DEBUG: LLM_COMPAT_API_KEY = {'SET' if api_key else 'NOT SET'}")
        print(f"DEBUG: LLM_BASE_URL = {base_url}")
        if not base_url:
            print("DEBUG: Missing LLM_BASE_URL for openai_compat")
            return None
        print("DEBUG: Creating OpenAI Compat client")
        return OpenAICompatClient(api_key, base_url)
    
    print(f"DEBUG: Unknown provider: {provider}")
    return None

def count_tokens_approx(text: str, model_hint: str) -> int:
    """Count tokens approximately."""
    try:
        # Try to use tiktoken for OpenAI models
        if "gpt" in model_hint.lower():
            encoding = tiktoken.encoding_for_model(model_hint)
            return len(encoding.encode(text))
        else:
            # Fallback: rough estimate
            return len(text) // 4
    except:
        # Fallback: rough estimate
        return len(text) // 4

def truncate_for_budget(text: str, max_input_tokens: int, max_output_tokens: int, model_hint: str) -> str:
    """Truncate text to fit within token budget."""
    # Reserve tokens for system prompt, safety margin, and output
    system_tokens = 200  # Approximate system prompt tokens
    safety_margin = 200
    available_tokens = max_input_tokens - system_tokens - safety_margin - max_output_tokens
    
    if available_tokens <= 0:
        return ""
    
    # Count tokens in current text
    current_tokens = count_tokens_approx(text, model_hint)
    
    if current_tokens <= available_tokens:
        return text
    
    # Truncate text
    # Start with a rough estimate
    target_chars = int(available_tokens * 3.5)  # Rough chars per token
    truncated = text[:target_chars]
    
    # Refine by counting actual tokens
    while count_tokens_approx(truncated, model_hint) > available_tokens:
        # Cut at word boundary
        truncated = truncated.rsplit(' ', 1)[0]
        if not truncated:
            break
    
    return truncated

def parse_metadata_response(response: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    """Parse LLM response for metadata."""
    print(f"DEBUG: parse_metadata_response called with: {repr(response)}")
    response = response.strip()
    
    # Try to parse as JSON first
    try:
        data = json.loads(response)
        title = data.get("title")
        summary = data.get("summary")
        tags = data.get("tags", [])
        
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",")]
        
        print(f"DEBUG: JSON parsing successful - title: {title}, summary: {summary}, tags: {tags}")
        return title, summary, tags
    except json.JSONDecodeError:
        print(f"DEBUG: JSON parsing failed, trying plaintext parsing")
        pass
    
    # Try to parse as plaintext
    title = None
    summary = None
    tags = []
    
    lines = response.split('\n')
    current_section = None
    
    print(f"DEBUG: Plaintext parsing - lines: {lines}")
    
    # Handle the format: title on first line, summary on second line, tags on third line
    if len(lines) >= 3:
        # First non-empty line is title
        for line in lines:
            if line.strip():
                title = line.strip()
                print(f"DEBUG: Found title: {title}")
                break
        
        # Second non-empty line is summary
        found_title = False
        for line in lines:
            if line.strip() and not found_title:
                found_title = True
                continue
            if line.strip() and found_title:
                summary = line.strip()
                print(f"DEBUG: Found summary: {summary}")
                break
        
        # Third non-empty line is tags
        found_summary = False
        for line in lines:
            if line.strip() and not found_title:
                found_title = True
                continue
            if line.strip() and found_title and not found_summary:
                found_summary = True
                continue
            if line.strip() and found_title and found_summary:
                tags_text = line.strip()
                tags = [tag.strip() for tag in tags_text.split(",")]
                print(f"DEBUG: Found tags: {tags}")
                break
    
    print(f"DEBUG: Plaintext parsing result - title: {title}, summary: {summary}, tags: {tags}")
    return title, summary, tags

async def generate_metadata(transcript_text: str, settings_row: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], List[str]]:
    """Generate metadata using LLM."""
    print("DEBUG: generate_metadata called")
    print(f"DEBUG: transcript_text length: {len(transcript_text)}")
    print(f"DEBUG: settings_row: {settings_row}")
    
    client = make_client(settings_row)
    print(f"DEBUG: client created: {client is not None}")
    if not client:
        print("DEBUG: No client created, returning None")
        return None, None, []
    
    try:
        models_config = settings_row.get("model_config", {})
        
        # System prompt
        system_prompt = """You are a helpful assistant that writes metadata for speech transcripts.
Return:
1) a short, punchy Title (<= 12 words),
2) a concise Summary (1–3 sentences),
3) 5–12 topical Tags (single words or short phrases).
No markdown, no quotes."""

        # Truncate transcript to fit budget
        max_input = int(os.getenv("LLM_MAX_INPUT_TOKENS", "4000"))
        max_output = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512"))
        model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        
        truncated_text = truncate_for_budget(transcript_text, max_input, max_output, model)
        
        # User prompt
        user_prompt = f"TRANSCRIPT (truncated to fit):\n{truncated_text}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call LLM
        print(f"DEBUG: Calling LLM with model: {model}")
        print(f"DEBUG: Messages: {messages}")
        print(f"DEBUG: Max tokens: {max_output}")
        print(f"DEBUG: Temperature: {float(os.getenv('LLM_TEMPERATURE', '0.2'))}")
        print(f"DEBUG: Top P: {float(os.getenv('LLM_TOP_P', '1.0'))}")
        
        try:
            response = await client.chat(
                model=model,
                messages=messages,
                max_tokens=max_output,
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
                top_p=float(os.getenv("LLM_TOP_P", "1.0"))
            )
            print(f"DEBUG: LLM response received: {response[:100]}...")
        except Exception as e:
            print(f"DEBUG: LLM call failed: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return None, None, []
        
        # Parse response
        title, summary, tags = parse_metadata_response(response)
        
        # Normalize tags
        if tags:
            # Clean and deduplicate tags
            cleaned_tags = []
            for tag in tags:
                tag = tag.strip()
                if tag and tag not in cleaned_tags:
                    cleaned_tags.append(tag)
            
            # Limit to 12 tags
            tags = cleaned_tags[:12]
        
        return title, summary, tags
        
    except Exception as e:
        print(f"LLM metadata generation failed: {e}")
        return None, None, []
    
    finally:
        if client:
            await client.close() 