import asyncio
import logging

from aiohttp import web
from aiogram import Bot

from app.bot.dispatcher import create_bot, create_dispatcher
from app.config import settings
from app.http.health import create_http_app
from app.services.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def run_http_server() -> web.AppRunner:
    app = create_http_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.http_host, settings.http_port)
    await site.start()
    logger.info("HTTP server listening on %s:%s", settings.http_host, settings.http_port)
    return runner


async def main() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    scheduler = setup_scheduler(bot)
    scheduler.start()

    http_runner = await run_http_server()
    logger.info("VPN sales bot started")

    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await http_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
