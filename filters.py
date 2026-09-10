from aiogram.filters import Filter
from aiogram.types import Message
from config import ADMIN_ID


class IsAdmin(Filter):
    """Foydalanuvchi admin ekanligini tekshiruvchi aiogram 3 filtri."""

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        # ADMIN_ID 0 bo'lsa yoki mos kelmasa False
        return ADMIN_ID != 0 and message.from_user.id == ADMIN_ID
