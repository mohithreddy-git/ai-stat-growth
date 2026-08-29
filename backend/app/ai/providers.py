from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    name: str

    async def generate_text(self, prompt: str, *, system: str = "") -> str:
        ...

    async def generate_structured(self, prompt: str, response_model: type[T], *, system: str = "") -> T:
        ...


class ProviderError(RuntimeError):
    pass


async def _validated_structured(provider: LLMProvider, prompt: str, response_model: type[T], system: str) -> T:
    """Parse provider output strictly and give a model one corrective retry."""
    last_error = "unknown validation error"
    for attempt in range(2):
        retry_prompt = prompt if attempt == 0 else (
            f"{prompt}\n\nYour previous response was invalid. Return only one valid JSON object "
            f"matching this schema: {response_model.model_json_schema()}"
        )
        raw = await provider.generate_text(retry_prompt, system=system)
        candidates = [raw]
        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.S)
        if fenced:
            candidates.insert(0, fenced.group(1))
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                return response_model.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError, TypeError) as exc:
                last_error = str(exc)
    raise ProviderError(f"LLM output failed structured validation after retry: {last_error}")


@dataclass
class MockProvider:
    name: str = "mock"

    async def generate_text(self, prompt: str, *, system: str = "") -> str:
        return "Mock provider: deterministic fallback is active."

    async def generate_structured(self, prompt: str, response_model: type[T], *, system: str = "") -> T:
        raise ProviderError("Mock provider intentionally delegates structured generation to deterministic services")


@dataclass
class OllamaProvider:
    base_url: str
    model: str
    name: str = "ollama"

    async def generate_text(self, prompt: str, *, system: str = "") -> str:
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(f"{self.base_url.rstrip('/')}/api/generate", json={"model": self.model, "prompt": prompt, "system": system, "stream": False, "format": "json"})
                response.raise_for_status()
                return response.json().get("response", "")
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

    async def generate_structured(self, prompt: str, response_model: type[T], *, system: str = "") -> T:
        return await _validated_structured(self, prompt, response_model, system)


@dataclass
class OpenAICompatibleProvider:
    base_url: str
    api_key: str
    model: str = "gpt-4o-mini"
    name: str = "openai_compatible"

    async def generate_text(self, prompt: str, *, system: str = "") -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json={"model": self.model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0.1, "response_format": {"type": "json_object"}})
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise ProviderError(f"OpenAI-compatible request failed: {exc}") from exc

    async def generate_structured(self, prompt: str, response_model: type[T], *, system: str = "") -> T:
        return await _validated_structured(self, prompt, response_model, system)


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    settings = get_settings()
    name = (provider_name or settings.llm_provider).lower()
    if name == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    if name in {"openai", "openai_compatible"} and settings.openai_api_key:
        return OpenAICompatibleProvider(settings.openai_base_url, settings.openai_api_key, settings.openai_model)
    return MockProvider()
