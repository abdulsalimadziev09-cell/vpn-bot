import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


class TranscriptionService:
    def __init__(self) -> None:
        self._api_key = settings.whisper_api_key
        self._base_url = settings.whisper_base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    async def transcribe_file(self, file_path: Path) -> str:
        if not self.enabled:
            raise TranscriptionError("Whisper API key not configured")

        url = f"{self._base_url}/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            with file_path.open("rb") as audio_file:
                response = await client.post(
                    url,
                    headers=headers,
                    data={"model": "whisper-1", "language": "ru"},
                    files={"file": (file_path.name, audio_file, "audio/ogg")},
                )

        if response.status_code != 200:
            logger.error("Whisper API error: %s %s", response.status_code, response.text)
            raise TranscriptionError(f"Whisper API returned {response.status_code}")

        data = response.json()
        text = data.get("text", "").strip()
        if not text:
            raise TranscriptionError("Empty transcription result")
        return text
