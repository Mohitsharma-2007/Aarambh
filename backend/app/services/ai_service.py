"""AI Service for natural language queries and analysis - Multi-provider support"""
from typing import AsyncGenerator, Optional
import httpx
import json
from loguru import logger

from app.config import settings, LLMProvider


FREE_MODELS = {
    LLMProvider.OPENROUTER: [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "qwen/qwen3-coder:free",
        "google/gemma-3-27b-it:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "openrouter/auto",
    ],
    LLMProvider.GROQ: [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
    LLMProvider.GLM: [
        "glm-4-flash",
        "glm-4-air",
        "glm-4",
        "glm-4-plus",
        "glm-4-long",
        "glm-3-turbo",
    ],
    LLMProvider.GOOGLE_AI: [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
    ],
}

class AIService:
    """Service for AI-powered analysis and queries with multi-provider support"""

    # Provider API endpoints
    OPENROUTER_BASE = "https://openrouter.ai/api/v1"
    GROQ_BASE = "https://api.groq.com/openai/v1"
    GLM_BASE = "https://open.bigmodel.cn/api/paas/v4"
    GOOGLE_AI_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.provider = settings.default_llm_provider
        self.model = settings.default_llm_model

    async def query(
        self, 
        prompt: str, 
        context: dict | None = None, 
        model: str | None = None, 
        provider: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> str:
        """Query AI with specified provider and model"""
        provider = provider or self.provider
        model = model or self.model
        
        # Robustly determine provider string
        if hasattr(provider, 'value'):
            prov_str = str(provider.value)
        elif isinstance(provider, str):
            prov_str = provider.lower().strip()
        else:
            prov_str = str(provider).lower().strip()
        
        # Auto-detect OpenRouter for :free models
        if model and ":free" in model and prov_str != "openrouter":
            logger.info(f"Auto-switching provider to openrouter for free model: {model}")
            prov_str = "openrouter"

        logger.info(f"AI Query [Executing]: provider={prov_str}, model={model}")

        try:
            if prov_str == "openrouter":
                return await self._query_openrouter(prompt, context, model, max_tokens, temperature)
            elif prov_str == "groq":
                return await self._query_groq(prompt, context, model, max_tokens, temperature)
            elif prov_str == "glm":
                return await self._query_glm(prompt, context, model, max_tokens, temperature)
            elif prov_str == "google_ai":
                return await self._query_google_ai(prompt, context, model, max_tokens, temperature)
            elif prov_str == "anthropic":
                return await self._query_anthropic(prompt, context, model, max_tokens, temperature)
            else:
                logger.warning(f"Unknown provider '{prov_str}', falling back to mock")
                return self._mock_response(prompt)
        except Exception as e:
            logger.error(f"AI query error ({prov_str}): {e}")
            return f"Error processing query: {str(e)}"

    async def _query_openrouter(
        self, prompt: str, context: dict | None, model: str, max_tokens: int, temperature: float
    ) -> str:
        """Query via OpenRouter API"""
        if not settings.openrouter_api_key:
            return self._mock_response(prompt)

        messages = self._build_messages(prompt, context)
        
        response = await self.http_client.post(
            f"{self.OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": settings.frontend_url,
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _query_groq(self, prompt: str, context: dict | None, model: str, max_tokens: int, temperature: float) -> str:
        """Query via Groq API (fast inference)"""
        if not settings.groq_api_key:
            return self._mock_response(prompt)

        messages = self._build_messages(prompt, context)
        
        url = f"{self.GROQ_BASE}/chat/completions"
        logger.info(f"Groq Request: POST {url} [model={model}]")
        
        response = await self.http_client.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _query_glm(self, prompt: str, context: dict | None, model: str, max_tokens: int, temperature: float) -> str:
        """Query via GLM API"""
        if not settings.glm_api_key:
            return self._mock_response(prompt)

        messages = self._build_messages(prompt, context)
        
        response = await self.http_client.post(
            f"{self.GLM_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.glm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def _query_google_ai(self, prompt: str, context: dict | None, model: str, max_tokens: int, temperature: float) -> str:
        """Query via Google AI API"""
        if not settings.google_ai_api_key:
            return self._mock_response(prompt)

        messages = self._build_messages(prompt, context)
        
        response = await self.http_client.post(
            f"{self.GOOGLE_AI_BASE}/models/{model}:generateContent",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "contents": [{"parts": [{"text": messages[-1]["content"]}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _query_anthropic(self, prompt: str, context: dict | None, model: str, max_tokens: int, temperature: float) -> str:
        """Query via Anthropic API"""
        if not settings.anthropic_api_key:
            return self._mock_response(prompt)

        messages = self._build_messages(prompt, context)
        
        response = await self.http_client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
            },
        )
        
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    async def stream_query(
        self, 
        prompt: str, 
        context: dict | None = None, 
        model: str | None = None, 
        provider: str | None = None
    ) -> AsyncGenerator[str, None]:
        """Stream AI response"""
        provider = provider or self.provider
        model = model or self.model
        
        # Robustly determine provider string
        prov_str = str(provider.value) if hasattr(provider, 'value') else str(provider)
        prov_str = prov_str.lower().strip()
        
        if ":free" in model and prov_str != "openrouter":
            prov_str = "openrouter"

        try:
            if prov_str == "openrouter":
                async for chunk in self._stream_openrouter(prompt, context, model):
                    yield chunk
            elif prov_str == "groq":
                async for chunk in self._stream_groq(prompt, context, model):
                    yield chunk
            elif prov_str == "glm":
                async for chunk in self._stream_glm(prompt, context, model):
                    yield chunk
            elif prov_str == "google_ai":
                async for chunk in self._stream_google_ai(prompt, context, model):
                    yield chunk
            else:
                yield self._mock_response(prompt)
        except Exception as e:
            logger.error(f"AI stream error ({provider}): {e}")
            yield f"Error: {str(e)}"

    async def batch_query(
        self, 
        prompts: list[str], 
        model: Optional[str] = None,
        models: Optional[list[str]] = None, 
        provider: str | None = None
    ) -> list[dict]:
        """Run multiple queries in parallel using specified models"""
        import asyncio
        
        target_provider = provider or self.provider
        
        # Robustly determine provider string for lookup
        if hasattr(target_provider, 'value'):
            prov_str = str(target_provider.value).lower()
        else:
            prov_str = str(target_provider).lower()

        # Determine the list of models to use
        if model:
            target_models = [model] * len(prompts)
        elif models:
            target_models = models
        else:
            # Use top free models from the specific provider if available
            # We match the string key in FREE_MODELS (which are LLMProvider enums)
            lookup_key = prov_str
            for p_enum in LLMProvider:
                if p_enum.value.lower() == prov_str:
                    lookup_key = p_enum
                    break
            
            target_models = FREE_MODELS.get(lookup_key, [])[:len(prompts)]
            if not target_models:
                target_models = [model or self.model] * len(prompts)
            
        tasks = []
        for i, prompt in enumerate(prompts):
            m = target_models[i % len(target_models)]
            tasks.append(self.query(prompt, model=m, provider=target_provider))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            {"model": target_models[i % len(target_models)], "content": r if not isinstance(r, Exception) else f"Error: {str(r)}"}
            for i, r in enumerate(results)
        ]


    async def _stream_openrouter(
        self, prompt: str, context: dict | None, model: str
    ) -> AsyncGenerator[str, None]:
        """Stream from OpenRouter API"""
        messages = self._build_messages(prompt, context)

        async with self.http_client.stream(
            "POST",
            f"{self.OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.3,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        if content := data["choices"][0].get("delta", {}).get("content"):
                            yield content
                    except:
                        pass

    async def _stream_groq(
        self, prompt: str, context: dict | None, model: str
    ) -> AsyncGenerator[str, None]:
        """Stream from Groq API"""
        messages = self._build_messages(prompt, context)

        async with self.http_client.stream(
            "POST",
            f"{self.GROQ_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.3,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        if content := data["choices"][0].get("delta", {}).get("content"):
                            yield content
                    except:
                        pass

    async def _stream_glm(
        self, prompt: str, context: dict | None, model: str
    ) -> AsyncGenerator[str, None]:
        """Stream from GLM API"""
        messages = self._build_messages(prompt, context)

        async with self.http_client.stream(
            "POST",
            f"{self.GLM_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.glm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.3,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        data = json.loads(line[6:])
                        if content := data["choices"][0].get("delta", {}).get("content"):
                            yield content
                    except:
                        pass

    async def _stream_google_ai(
        self, prompt: str, context: dict | None, model: str
    ) -> AsyncGenerator[str, None]:
        """Stream from Google AI API"""
        messages = self._build_messages(prompt, context)

        async with self.http_client.stream(
            "POST",
            f"{self.GOOGLE_AI_BASE}/models/{model}:streamGenerateContent",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "contents": [{"parts": [{"text": messages[-1]["content"]}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2000,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "text" in data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0]:
                            yield data["candidates"][0]["content"]["parts"][0]["text"]
                    except:
                        pass

    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (-1 to 1)"""
        try:
            response = await self.query(
                f"Analyze sentiment of this text and return ONLY a number between -1 (very negative) and 1 (very positive):\n\n{text}",
                model="meta-llama/llama-3.2-3b-instruct:free",
            )
            return float(response.strip())
        except:
            return 0.0

    async def extract_entities(self, text: str) -> list[dict]:
        """Extract named entities from text"""
        try:
            response = await self.query(
                f"""Extract entities from this text as JSON array:
                [{{"name": "Entity Name", "type": "GPE|ORG|PERSON|EVENT", "relevance": 0-1}}]
                
                Text: {text}
                
                Return ONLY valid JSON.""",
                model="meta-llama/llama-3.2-3b-instruct:free",
            )
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return []

    def _build_messages(self, prompt: str, context: dict | None) -> list[dict]:
        """Build messages array for chat completion"""
        system_prompt = """You are an intelligence analyst assistant for AARAMBH, India's sovereign OSINT platform.
        Analyze queries in context of Indian national security, geopolitics, economics, and strategic interests.
        Provide concise, factual responses with entity mentions and sentiment indicators where relevant."""

        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({"role": "user", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": prompt})
        return messages

    def _mock_response(self, prompt: str) -> str:
        """Generate smart mock response based on prompt context for testing"""
        import re
        
        # If it asks for JSON
        if "JSON format" in prompt or "valid JSON" in prompt or "JSON array" in prompt:
            if "analyze_impact" in prompt or "impact_analysis" in prompt:
                return '''{
                    "impact_analysis": "Mock analysis: The event signifies a major shift in the specified domain with cascading effects on regional stability and economic indicators.",
                    "affected_sectors": [{"sector": "Technology", "impact": "Supply chain disruption", "severity": "high"}],
                    "affected_entities": [{"name": "Mock Entity", "impact": "Regulatory scrutiny"}],
                    "geopolitical_implications": "Increased regional tensions and realignment of strategic partnerships.",
                    "economic_implications": "Market volatility and potential shifts in foreign direct investment.",
                    "recommendations": ["Monitor key indicators", "Diversify supply chains"],
                    "risk_level": "medium"
                }'''
            if "entities" in prompt.lower():
                return '[{"name": "India", "type": "GPE", "relevance": 0.9}, {"name": "USA", "type": "GPE", "relevance": 0.8}]'
                
            return '{"status": "mock", "message": "Configure API keys for real JSON generation"}'
            
        # For analysis prompts (like Deep Research)
        if "Raw Search Results" in prompt:
            # Extract content from search results
            match = re.search(r'Raw Search Results:(.*)', prompt, re.DOTALL)
            if match:
                res = match.group(1)[:500]
                return f"**Mock Summarized Data:**\nBased on search results, the key findings are:\n{res}...\n\n(Configure API keys for full AI analysis)"

        return f"Mock response. Please configure API keys (OpenRouter/Groq/Google) for production use.\n\nContext received: {prompt[:100]}..."


# Singleton instance
ai_service = AIService()
