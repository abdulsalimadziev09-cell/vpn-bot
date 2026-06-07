from aiogram import Router

from app.bot.handlers import about, admin, download, payments, plans, referral, start, subscription, support, trial


def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(payments.router)
    router.include_router(plans.router)
    router.include_router(trial.router)
    router.include_router(subscription.router)
    router.include_router(download.router)
    router.include_router(about.router)
    router.include_router(referral.router)
    router.include_router(support.router)
    router.include_router(admin.router)
    return router
