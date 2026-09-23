import os
from pathlib import Path
from dotenv import load_dotenv

from typing import Union, Optional

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

try:
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0").strip())
except ValueError:
    ADMIN_ID = 0

DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "tests.db")))

# Majburiy kanal a'zoligi sozlamalari
CHANNEL_ID_RAW: str = os.getenv("CHANNEL_ID", "").strip()
CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "").strip()
CHANNEL_URL: str = os.getenv("CHANNEL_URL", "").strip()

# get_chat_member uchun CHANNEL_ID ni aniqlash (int yoki str)
CHANNEL_ID: Optional[Union[int, str]] = None
if CHANNEL_ID_RAW:
    try:
        CHANNEL_ID = int(CHANNEL_ID_RAW)
    except ValueError:
        CHANNEL_ID = CHANNEL_ID_RAW
elif CHANNEL_USERNAME:
    if CHANNEL_USERNAME.startswith(("http://", "https://")):
        slug = CHANNEL_USERNAME.rstrip("/").split("/")[-1]
        CHANNEL_ID = f"@{slug}"
    else:
        CHANNEL_ID = CHANNEL_USERNAME if CHANNEL_USERNAME.startswith("@") else f"@{CHANNEL_USERNAME}"


def get_channel_url() -> str:
    """Foydalanuvchiga kanalga a'zo bo'lish havolasini qaytarish."""
    if CHANNEL_URL:
        return CHANNEL_URL
    if CHANNEL_USERNAME:
        if CHANNEL_USERNAME.startswith(("http://", "https://")):
            return CHANNEL_USERNAME
        return f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    if CHANNEL_ID_RAW:
        if CHANNEL_ID_RAW.startswith(("http://", "https://")):
            return CHANNEL_ID_RAW
        if CHANNEL_ID_RAW.startswith("@"):
            return f"https://t.me/{CHANNEL_ID_RAW.lstrip('@')}"
    return "https://t.me"


if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    # Ogohlantirish: token to'liq sozlanmagan bo'lishi mumkin
    pass

