"""
LLM Client Wrapper
Unified OpenAI-format calling with multi-provider + multi-model automatic fallback
"""

import json
import re
import traceback
from typing import Optional, Dict, Any, List, Tuple
from openai import OpenAI, APIError, APITimeoutError

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('aarambh.llm')

# Prioritized OpenRouter models (Liquid Thinking first as it succeeded in logs)
OPENROUTER_FREE_MODELS = [
    "liquid/lfm-2.5-1.2b-thinking:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-3-4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen3-4b:free",
    "google/gemini-2.0-flash-001",  # Demoted due to 402 errors
    "google/gemini-2.0-flash-lite-001",
    "google/gemini-2.5-flash-lite",
    "google/gemini-2.5-flash-lite-preview-09-2025",
]


class LLMProvider:
    """LLM Provider Configuration"""
    
    def __init__(self, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = None
        
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def is_available(self) -> bool:
        return self.client is not None and self.api_key is not None


class LLMClient:
    """LLM Client with multi-provider + multi-model automatic fallback"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        # Initialize all available providers
        self.providers: List[LLMProvider] = []
        
        # --- OpenRouter providers (primary + free model fallbacks) ---
        or_api_key = api_key or Config.LLM_API_KEY
        or_base_url = base_url or Config.LLM_BASE_URL
        primary_model = model or Config.LLM_MODEL_NAME
        
        if or_api_key:
            # 1. Primary configured model
            primary = LLMProvider(
                name=f"OpenRouter ({primary_model})",
                api_key=or_api_key,
                base_url=or_base_url,
                model=primary_model
            )
            if primary.is_available():
                self.providers.append(primary)
                logger.info(f"Primary provider configured: {primary_model}")
            
            # 2. Add all free OpenRouter model fallbacks
            for free_model in OPENROUTER_FREE_MODELS:
                if free_model == primary_model:
                    continue  # Skip if already primary
                fallback = LLMProvider(
                    name=f"OpenRouter ({free_model})",
                    api_key=or_api_key,
                    base_url=or_base_url,
                    model=free_model
                )
                if fallback.is_available():
                    self.providers.append(fallback)
        
        # 3. Groq (backup provider 1)
        groq = LLMProvider(
            name="Groq",
            api_key=Config.GROQ_API_KEY,
            base_url=Config.GROQ_BASE_URL,
            model=Config.GROQ_MODEL_NAME
        )
        if groq.is_available():
            self.providers.append(groq)
            logger.info(f"Backup provider configured: Groq - {groq.model}")
        
        # 4. GLM (backup provider 2)
        glm = LLMProvider(
            name="GLM",
            api_key=Config.GLM_API_KEY,
            base_url=Config.GLM_BASE_URL,
            model=Config.GLM_MODEL_NAME
        )
        if glm.is_available():
            self.providers.append(glm)
            logger.info(f"Backup provider configured: GLM - {glm.model}")
        
        if not self.providers:
            raise ValueError("No available LLM providers. Configure at least LLM_API_KEY or GROQ_API_KEY or GLM_API_KEY")
        
        logger.info(f"Total {len(self.providers)} LLM providers configured (including free model fallbacks)")
    
    def _try_provider(
        self,
        provider: LLMProvider,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict]
    ) -> Tuple[bool, str]:
        """
        Try calling a single provider
        
        Returns:
            (success, content_or_error)
        """
        kwargs = {
            "model": provider.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        try:
            logger.info(f"[{provider.name}] Calling LLM API: model={provider.model}")
            response = provider.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            # Handle None content
            if content is None:
                logger.warning(f"[{provider.name}] Empty content returned")
                return False, "Empty content returned"
            
            # Remove thinking tags
            content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
            content = re.sub(r'\[think\].*?\[/think\]', '', content, flags=re.DOTALL).strip()
            
            logger.info(f"[{provider.name}] Success, length={len(content)}")
            return True, content
            
        except APITimeoutError as e:
            logger.warning(f"[{provider.name}] Timeout: {e}")
            return False, f"Timeout: {e}"
        except APIError as e:
            logger.warning(f"[{provider.name}] API Error: {e}")
            return False, f"API Error: {e}"
        except Exception as e:
            error_detail = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_detail += f" - Response: {e.response.text}"
            logger.error(f"[{provider.name}] Call failed: {error_detail}")
            return False, f"Call failed: {error_detail}"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send chat request, automatically tries multiple providers and models
        
        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum token count
            response_format: Response format (e.g. JSON mode)
            
        Returns:
            Model response text
        """
        last_error = None
        
        for provider in self.providers:
            success, result = self._try_provider(
                provider, messages, temperature, max_tokens, response_format
            )
            
            if success:
                return result
            else:
                last_error = result
                logger.info(f"[{provider.name}] Failed, switching to next provider...")
                continue
        
        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send chat request and return JSON
        
        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum token count
            
        Returns:
            Parsed JSON object
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # Clean markdown code block markers
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format from LLM: {cleaned_response}")
