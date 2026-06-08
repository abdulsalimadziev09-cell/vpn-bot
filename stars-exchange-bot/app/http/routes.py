import logging

from aiohttp import web
from aiogram import Bot

from app.db.session import async_session_factory
from app.integrations.robokassa_client import verify_result_notification
from app.services.fulfillment import fulfill_order
from app.services.payment import mark_paid_from_robokassa, notify_payment_received

logger = logging.getLogger(__name__)


async def health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


async def robokassa_result(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    params = dict(request.query)
    if request.method == "POST":
        try:
            data = await request.post()
            params.update({k: str(v) for k, v in data.items()})
        except Exception:
            logger.exception("Failed to parse Robokassa POST body")

    try:
        _, inv_id_str = verify_result_notification(params)
        inv_id = int(inv_id_str)
    except Exception:
        logger.exception("Robokassa signature verification failed")
        return web.Response(text="bad sign", status=400)

    async with async_session_factory() as session:
        order = await mark_paid_from_robokassa(session, inv_id=inv_id, out_sum=params.get("OutSum", ""))
        if not order:
            return web.Response(text="order not found", status=404)

        await notify_payment_received(bot, order)
        await fulfill_order(session, bot, order)

    return web.Response(text=f"OK{inv_id}")


async def robokassa_success(request: web.Request) -> web.Response:
    inv_id = request.query.get("InvId", "")
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Оплата принята</title></head><body>"
        "<h1>Оплата принята</h1>"
        f"<p>Заказ #{inv_id}. Stars будут отправлены в Telegram в ближайшие минуты.</p>"
        "<p>Можно закрыть эту страницу и вернуться в бот.</p>"
        "</body></html>"
    )
    return web.Response(text=html, content_type="text/html")


async def robokassa_fail(_: web.Request) -> web.Response:
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Оплата не прошла</title></head><body>"
        "<h1>Оплата не прошла</h1>"
        "<p>Попробуйте снова в Telegram-боте.</p>"
        "</body></html>"
    )
    return web.Response(text=html, content_type="text/html")


def create_http_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/health", health)
    app.router.add_get("/payments/robokassa/result", robokassa_result)
    app.router.add_post("/payments/robokassa/result", robokassa_result)
    app.router.add_get("/payments/robokassa/success", robokassa_success)
    app.router.add_get("/payments/robokassa/fail", robokassa_fail)
    return app
