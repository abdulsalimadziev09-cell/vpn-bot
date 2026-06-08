from aiohttp.test_utils import TestClient, TestServer

from app.http.routes import create_http_app


async def test_health_endpoint():
    app = create_http_app(bot=None)
    async with TestClient(TestServer(app)) as client:
        response = await client.get("/health")
        assert response.status == 200
        assert await response.text() == "ok"
