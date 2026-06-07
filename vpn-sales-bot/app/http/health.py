from pathlib import Path

from aiohttp import web

LAVA_VERIFY_PATH = "/lava-verify_751e93edad61d6f3.html"
LAVA_VERIFY_FILENAME = "lava-verify_751e93edad61d6f3.html"


def _lava_verify_content() -> str:
    candidates = [
        Path(__file__).resolve().parent.parent.parent / LAVA_VERIFY_FILENAME,
        Path("/app") / LAVA_VERIFY_FILENAME,
    ]
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    return "lava-verify"


async def health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


async def lava_verify(_: web.Request) -> web.Response:
    return web.Response(text=_lava_verify_content(), content_type="text/html")


def create_http_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get(LAVA_VERIFY_PATH, lava_verify)
    return app
