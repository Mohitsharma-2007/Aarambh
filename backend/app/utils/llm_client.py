"""
LLM Client wrapper
Unified OpenAI-format calls with multi-provider automatic fallback
"""

import json
import re
import traceback
from typing import Optional, Dict, Any, List, Tuple
from openai import OpenAI, APIError, APITimeoutError

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('aarambh.llm')


class LLMProvider:
    """LLM provider configuration"""

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
    """LLM client with multi-provider automatic fallback"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        # Initialize all available providers
        self.providers: List[LLMProvider] = []

        # 1. Primary provider (OpenRouter)
        primary = LLMProvider(
            name="Primary (OpenRouter)",
            api_key=api_key or Config.LLM_API_KEY,
            base_url=base_url or Config.LLM_BASE_URL,
            model=model or Config.LLM_MODEL_NAME
        )
        if primary.is_available():
            self.providers.append(primary)
            logger.info(f"Primary provider configured: {primary.model}")

        # 2. Groq (backup 1)
        groq = LLMProvider(
            name="Groq",
            api_key=Config.GROQ_API_KEY,
            base_url=Config.GROQ_BASE_URL,
            model=Config.GROQ_MODEL_NAME
        )
        if groq.is_available():
            self.providers.append(groq)
            logger.info(f"Backup provider configured: Groq - {groq.model}")

        # 3. GLM (backup 2)
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
            raise ValueError("No available LLM providers. Please configure at least LLM_API_KEY, GROQ_API_KEY, or GLM_API_KEY")

        logger.info(f"Total {len(self.providers)} LLM providers configured")

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
                logger.warning(f"[{provider.name}] Returned empty content")
                return False, "Returned empty content"

            # Remove thinking tags (Chinese and English variants)
            content = re.sub(r'<\u601d\u8003>[\s\S]*?</\u601d\u8003>', '', content).strip()
            content = re.sub(r'\[\u601d\u8003\].*?\[/\u601d\u8003\]', '', content, flags=re.DOTALL).strip()
            content = re.sub(r'<thinking>[\s\S]*?</thinking>', '', content).strip()

            logger.info(f"[{provider.name}] Success, length={len(content)}")
            return True, content

        except APITimeoutError as e:
            logger.warning(f"[{provider.name}] Timeout: {e}")
            return False, f"Timeout: {e}"
        except APIError as e:
            logger.warning(f"[{provider.name}] API error: {e}")
            return False, f"API error: {e}"
        except Exception as e:
            logger.warning(f"[{provider.name}] Call failed: {e}")
            return False, f"Call failed: {e}"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request, automatically trying multiple providers

        Args:
            messages: Message list
            temperature: Temperature parameter
            max_tokens: Maximum token count
            response_format: Response format (e.g., JSON mode)

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
        Send a chat request and return JSON

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
            raise ValueError(f"LLM returned invalid JSON format: {cleaned_response}")
