"""
OpenAI client implementation
"""

import asyncio
import httpx
from typing import List, Dict, Any
from .base import LLMClient

class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        """Send chat completion request to OpenAI."""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        # Retry logic
        for attempt in range(3):
            try:
                response = await self.client.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 500, 502, 503, 504] and attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 