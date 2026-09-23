import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from handlers import main_router

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def handle_ping(request: web.Request) -> web.Response:
    """Keep-alive tekshiruvi uchun GET / so'roviga javob qaytarish."""
    return web.Response(text="Bot is running!", status=200)


async def start_keep_alive_server() -> web.AppRunner:
    """Render spin-down bo'lib qolmasligi uchun asinxron veb-server ishga tushirish."""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    port_str = os.getenv("PORT", "8080").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 8080

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info(f"Keep-alive veb-serveri http://0.0.0.0:{port} manzilida ishga tushirildi.")
    return runner


async def set_bot_commands(bot: Bot) -> None:
    """Telegram bot buyruqlar menyusini sozlash."""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish va asosiy menyu"),
        BotCommand(command="help", description="Javob yuborish tartibi haqida ma'lumot"),
        BotCommand(command="list", description="Barcha testlar ro'yxati (Admin)"),
        BotCommand(command="results", description="Test natijalari reytingi (Admin)"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())



async def main() -> None:
    """Asosiy ishga tushirish funksiyasi."""
    logger.info("Bot ishga tushirilmoqda...")

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "XATOLIK: BOT_TOKEN ko'rsatilmagan! Iltimos, .env fayliga Telegram bot tokenini kiriting."
        )
        return

    # Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("Ma'lumotlar bazasi tekshirilmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(main_router)

    # Buyruqlar menyusi
    try:
        await set_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Buyruqlar menyusini o'rnatishda ogohlantirish: {e}")

    logger.info(f"Bot muvaffaqiyatli ishga tushdi! Admin ID: {ADMIN_ID}")

    # Render spin-down bo'lib qolmasligi uchun fon veb-serverini ishga tushirish
    web_runner = await start_keep_alive_server()

    # Eskirgan xabarlarni o'tkazib yuborish va pollingni boshlash
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        try:
            await web_runner.cleanup()
        except Exception as e:
            logger.warning(f"Veb-serverni to'xtatishda ogohlantirish: {e}")
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")
