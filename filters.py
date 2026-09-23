import logging
from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from config import ADMIN_ID, CHANNEL_ID

logger = logging.getLogger(__name__)


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Foydalanuvchi kanalga a'zo ekanligini get_chat_member orqali tekshirish.
    Agar CHANNEL_ID sozlanmagan bo'lsa, True qaytaradi.
    """
    if not CHANNEL_ID:
        return True

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in (
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ):
            return True
        if member.status == ChatMemberStatus.RESTRICTED:
            return getattr(member, "is_member", True)
        return False
    except Exception as e:
        logger.error(
            f"Kanal a'zoligini tekshirishda xatolik (chat_id={CHANNEL_ID}, user_id={user_id}): {e}"
        )
        return False


class IsAdmin(Filter):
    """Foydalanuvchi admin ekanligini tekshiruvchi aiogram 3 filtri."""

    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        # ADMIN_ID 0 bo'lsa yoki mos kelmasa False
        return ADMIN_ID != 0 and message.from_user.id == ADMIN_ID


class IsSubscribed(Filter):
    """Foydalanuvchi kanalga a'zo ekanligini tekshiruvchi aiogram 3 filtri."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if not message.from_user:
            return False
        if ADMIN_ID != 0 and message.from_user.id == ADMIN_ID:
            return True
        return await is_subscribed(bot, message.from_user.id)

