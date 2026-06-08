from aiogram import Router

from app.bot.handlers import (
    daily_review,
    folders,
    inbox,
    list_items,
    payments,
    pro,
    reminders,
    save,
    search,
    start,
    tags,
)


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(payments.router)
    router.include_router(pro.router)
    router.include_router(inbox.router)
    router.include_router(daily_review.router)
    router.include_router(folders.router)
    router.include_router(search.router)
    router.include_router(list_items.router)
    router.include_router(tags.router)
    router.include_router(reminders.router)
    router.include_router(save.router)
    return router
