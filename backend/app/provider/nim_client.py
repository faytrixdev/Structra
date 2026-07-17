from typing import Optional
import httpx
from app.config import settings


class NIMClient:
    def __init__(self):
        self.api_key = settings.nvidia_api_key
        self.model = settings.nvidia_model
        self.base_url = settings.nvidia_base_url

    async def chat_completion(self, system_prompt: str, user_prompt: str, response_format: Optional[dict] = None, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": temperature, "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


nim_client = NIMClient()
