"""
Base LLM client protocol
"""

from typing import Protocol, List, Dict, Any

class LLMClient(Protocol):
    """Protocol for LLM clients."""
    
    async def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: float
    ) -> str:
        """Send chat completion request and return assistant message content."""
        ... 