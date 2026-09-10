from aiogram import Router
from .admin import admin_router
from .user import user_router

# Asosiy router
main_router = Router()
main_router.include_router(admin_router)
main_router.include_router(user_router)

__all__ = ["main_router", "admin_router", "user_router"]
