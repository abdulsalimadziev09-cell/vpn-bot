from aiohttp import web


def create_http_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", lambda _: web.Response(text="ok"))
    return app
