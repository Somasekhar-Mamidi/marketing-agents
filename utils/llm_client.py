"""LLM Client for OpenAI API integration with retry and error handling."""

import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from config.loader import get_env_var
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None


class LLMClient:
    """OpenAI LLM client with retry logic and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (loads from env if not provided)
            model: Model to use for completions
        """
        self.api_key = api_key or get_env_var("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. LLM features will be disabled.")
    
    @property
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return self.api_key is not None and self.api_key != "your_openai_api_key_here"
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                raise
        return self._client
    
    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(Exception,)
    )
    def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None
    ) -> LLMResponse:
        """Get completion from LLM.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            LLMResponse with content and metadata
        """
        if not self.is_configured:
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error="LLM not configured - no API key"
            )
        
        try:
            client = self._get_client()
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = client.chat.completions.create(**kwargs)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                success=True
            )
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=str(e)
            )
    
    def parse_json_response(self, response: LLMResponse) -> Dict[str, Any]:
        """Parse JSON from LLM response.
        
        Args:
            response: LLMResponse object
            
        Returns:
            Parsed JSON dictionary
        """
        if not response.success:
            return {"error": response.error}
        
        try:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Invalid JSON", "raw_content": response.content}


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
