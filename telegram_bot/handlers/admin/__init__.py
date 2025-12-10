from aiogram import Router

from .block_user import router as block_router
from .register_user import router as register_router

admin_router = Router()
admin_router.include_router(register_router)
admin_router.include_router(block_router)

__all__ = ["admin_router"]
