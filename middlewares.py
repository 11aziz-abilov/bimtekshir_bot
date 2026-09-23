import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message
from config import ADMIN_ID, CHANNEL_ID
from filters import is_subscribed
from handlers.user import send_subscription_prompt

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Foydalanuvchilarning Telegram kanalga obuna bo'lganligini
    tekshiruvchi aiogram 3 middleware'i.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Faqat xabarlar (Message) uchun tekshiramiz
        if not isinstance(event, Message):
            return await handler(event, data)

        # Agar CHANNEL_ID belgilanmagan bo'lsa, tekshiruvsiz o'tkazamiz
        if not CHANNEL_ID:
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        # Bot admini tekshiruvdan ozod
        if ADMIN_ID != 0 and user.id == ADMIN_ID:
            return await handler(event, data)

        bot: Bot = data.get("bot") or event.bot
        if not bot:
            return await handler(event, data)

        # Obunani tekshirish
        subscribed = await is_subscribed(bot, user.id)
        if not subscribed:
            await send_subscription_prompt(event)
            return  # Keyingi handlerlar chaqirilmaydi

        return await handler(event, data)
