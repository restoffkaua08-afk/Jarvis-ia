import os
import httpx
import json
from typing import AsyncIterator, Optional
from .base import VoiceProvider

class ElevenLabsProvider(VoiceProvider):
    def __init__(self, api_key: Optional[str] = None, voice_id: str = "pNInz6obS6S9T0PAtRsh"):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY must be provided or set as environment variable")
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"

    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base_url}/text-to-speech/{self.voice_id}/stream", headers=headers, json=payload) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
