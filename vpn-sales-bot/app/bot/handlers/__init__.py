from aiogram import Router

from app.bot.handlers import admin, payments, plans, start, subscription, support


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(payments.router)
    router.include_router(plans.router)
    router.include_router(subscription.router)
    router.include_router(support.router)
    router.include_router(admin.router)
    return router
