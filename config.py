import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

try:
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0").strip())
except ValueError:
    ADMIN_ID = 0

DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "tests.db")))

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    # Ogohlantirish: token to'liq sozlanmagan bo'lishi mumkin
    pass
