from aiogram import Router
from .handlers import common


def setup_routers() -> Router:
    router = Router()
    router.include_router(common.router)

    return router