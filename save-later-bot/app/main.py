import asyncio
import logging

from app.bot.dispatcher import create_bot, create_dispatcher
from app.config import settings
from app.services.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Bot started, reminder poll every %ss", settings.reminder_poll_seconds)

    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
