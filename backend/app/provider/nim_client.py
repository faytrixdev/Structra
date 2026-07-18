import asyncio
import json
import logging
import re
import time
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)


class NIMClientError(Exception):
    pass


class _RateLimiter:
    """Minimal token-bucket-ish limiter: ensures at least `min_interval_s`
    seconds elapse between consecutive requests."""

    def __init__(self, min_interval_s: float):
        self._min_interval = max(min_interval_s, 0.0)
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


class NIMClient:
    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.model = settings.nvidia_model
        self.base_url = settings.nvidia_base_url
        # Convert pacing (ms) to minimum interval (seconds). The NIM free tier
        # tolerates roughly 1 request every ~6-7 seconds, but we use the
        # configured pacing as a floor (default 1500ms → 1.5s).
        pacing_s = getattr(settings, "pipeline_request_pacing_ms", 1500) / 1000.0
        self._limiter = _RateLimiter(pacing_s)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=30.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def aclose(self) -> None:
        client = self._client
        self._client = None
        if client is not None and not client.is_closed:
            await client.aclose()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        await self._limiter.acquire()
        client = self._get_client()
        response = await client.post(self.base_url, headers=headers, json=payload)

        # 429 / 5xx → raise so tenacity can retry with backoff
        if response.status_code == 429 or response.status_code >= 500:
            response.raise_for_status()

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def chat_completion_json(
        self, system_prompt: str, user_prompt: str, **kwargs
    ) -> dict:
        content = await self.chat_completion(system_prompt, user_prompt, **kwargs)
        parsed = self._parse_json_object(content)
        if isinstance(parsed, dict):
            return parsed
        return {}

    @staticmethod
    def _parse_json_object(content: str):
        text = (content or "").strip()
        if not text:
            return text
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        # Strip markdown code fences
        fence_match = re.search(
            r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.DOTALL
        )
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass
        # Find first balanced JSON object
        brace_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        return text


nim_client = NIMClient()
