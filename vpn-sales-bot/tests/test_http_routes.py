from aiohttp.test_utils import TestClient, TestServer

from app.http.health import LAVA_VERIFY_PATH, create_http_app


async def test_lava_verify_route_returns_token() -> None:
    app = create_http_app()
    async with TestClient(TestServer(app)) as client:
        response = await client.get(LAVA_VERIFY_PATH)
        body = await response.text()

    assert response.status == 200
    assert body == "lava-verify"
    assert response.content_type.startswith("text/html")
