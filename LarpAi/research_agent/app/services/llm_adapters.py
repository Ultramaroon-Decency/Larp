import os
import json
import base64
import logging
import httpx
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel
from research_agent.app.services.llm_base import BaseLLMProvider, MockLLMProvider
from research_agent.app.config.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API adapter implementing BaseLLMProvider via httpx async HTTP.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY in environment.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }

        import asyncio
        max_retries = 3
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.endpoint, headers=headers, json=payload)
                if resp.status_code == 429 and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"OpenAI rate limited (429). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = f"{prompt}\n\nRespond ONLY with a valid JSON object matching this schema:\n{schema_json}"
        text_out = await self.generate_text(augmented_prompt, system_prompt=system_prompt)
        clean_json = text_out.strip("`").replace("json\n", "", 1).strip()
        return schema.model_validate_json(clean_json)

    async def generate_vision_text(self, image_bytes: bytes, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY in environment.")

        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": 1024
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API adapter implementing BaseLLMProvider via httpx async HTTP.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        self.model = model

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY in environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instructions: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {"contents": contents}
        headers = {"Content-Type": "application/json"}

        import asyncio
        max_retries = 3
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 429 and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"Gemini rate limited (429). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return ""

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = f"{prompt}\n\nRespond ONLY with a valid JSON object matching this schema:\n{schema_json}"
        text_out = await self.generate_text(augmented_prompt, system_prompt=system_prompt)
        clean_json = text_out.strip("`").replace("json\n", "", 1).strip()
        return schema.model_validate_json(clean_json)

    async def generate_vision_text(self, image_bytes: bytes, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY in environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return ""


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API adapter implementing BaseLLMProvider via httpx async HTTP.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set ANTHROPIC_API_KEY in environment.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()

    async def generate_structured(self, prompt: str, schema: Type[T], system_prompt: Optional[str] = None) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        augmented_prompt = f"{prompt}\n\nRespond ONLY with a valid JSON object matching this schema:\n{schema_json}"
        text_out = await self.generate_text(augmented_prompt, system_prompt=system_prompt)
        clean_json = text_out.strip("`").replace("json\n", "", 1).strip()
        return schema.model_validate_json(clean_json)

    async def generate_vision_text(self, image_bytes: bytes, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set ANTHROPIC_API_KEY in environment.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"].strip()


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function to instantiate the configured LLM provider adapter.
    Falls back gracefully to MockLLMProvider if no valid API key is present.
    When no provider_name is specified, auto-detects any available API key.
    """
    target = provider_name.lower() if provider_name else "auto"

    if target == "openai":
        _check = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if _check:
            return OpenAIProvider()
    elif target == "gemini":
        _check = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if _check:
            return GeminiProvider()
    elif target == "anthropic":
        _check = settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
        if _check:
            return AnthropicProvider()

    # Auto-detect: probe all providers in priority order
    if settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", ""):
        return OpenAIProvider()
    if settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", ""):
        return GeminiProvider()
    if settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", ""):
        return AnthropicProvider()

    logger.info("No active API keys found. Falling back to MockLLMProvider.")
    return MockLLMProvider()
