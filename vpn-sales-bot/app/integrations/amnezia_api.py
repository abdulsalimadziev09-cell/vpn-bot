from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class AmneziaClientInfo:
    external_id: str
    config_text: str


class AmneziaApiClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.amnezia_api_url).rstrip("/")
        self.api_key = api_key or settings.amnezia_api_key

    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key}

    async def create_user(self, client_name: str) -> AmneziaClientInfo:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/users",
                headers=self._headers(),
                json={"name": client_name},
            )
            response.raise_for_status()
            payload = response.json()

        return AmneziaClientInfo(
            external_id=str(payload.get("id") or payload.get("name") or client_name),
            config_text=str(payload.get("config") or payload.get("configText") or ""),
        )

    async def delete_user(self, external_id: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/users/{external_id}",
                headers=self._headers(),
            )
            if response.status_code not in (200, 204, 404):
                response.raise_for_status()
