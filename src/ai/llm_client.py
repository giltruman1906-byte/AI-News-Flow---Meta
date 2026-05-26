"""LLM client abstraction. Higgsfield (OpenAI-compatible) primary, Anthropic fallback.

Both clients normalize to `complete_json(prompt) -> dict`. A StubClient is used
when no keys are configured (smoke-test mode) so the rest of the pipeline can
run end-to-end without network or credentials.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Protocol

import httpx

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete_json(self, prompt: str) -> dict: ...


def _extract_json(text: str) -> dict:
    text = text.strip()
    # strip ```json fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise
        return json.loads(m.group(0))


class HiggsfieldClient:
    """OpenAI-compatible chat completions. Verify endpoint shape against Higgsfield docs."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete_json(self, prompt: str) -> dict:
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.4,
            },
            timeout=60,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return _extract_json(content)


class AnthropicClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete_json(self, prompt: str) -> dict:
        msg = self._get().messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt + "\n\nRespond with JSON only."}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return _extract_json(text)


class StubClient:
    """Deterministic responses for smoke tests. No network."""

    def complete_json(self, prompt: str) -> dict:
        if "Score each item" in prompt or "scoring AI news" in prompt.lower():
            score = 9 if "anthropic" in prompt.lower() or "openai" in prompt.lower() else 7
            return {
                "score": score,
                "reason": "Stub LLM: deterministic high score for vendor items.",
                "category": "model",
            }
        return {
            "slide_1_hook": "AI just shipped something real.",
            "slide_2_what": "A major lab released a new capability today. It's available now in their API.",
            "slide_3_why": "SMBs gain a concrete new building block. Faster automation, lower cost.",
            "slide_4_take": "The bar moved — again. Move with it or get out-shipped.",
            "fb_caption": "A major lab released a new capability today. SMBs gain a concrete new building block — faster automation, lower cost.\n\nThe bar moved again. Move with it or get out-shipped.",
            "hashtags": ["#AI", "#SMB", "#Automation", "#LLM", "#Shipping"],
        }


def build_client(provider: str, settings) -> LLMClient:
    if provider == "stub":
        return StubClient()
    if provider == "higgsfield":
        if not settings.higgsfield_api_key or not settings.higgsfield_base_url:
            log.warning("higgsfield creds missing — falling back to anthropic")
            provider = "anthropic"
        else:
            return HiggsfieldClient(
                settings.higgsfield_api_key,
                settings.higgsfield_base_url,
                settings.higgsfield_model,
            )
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            log.warning("anthropic creds missing — using stub client")
            return StubClient()
        return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
    raise ValueError(f"unknown LLM provider: {provider}")
