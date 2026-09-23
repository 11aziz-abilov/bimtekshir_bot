import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SCHEDULE_FILE = Path(__file__).resolve().parent / "schedule.json"

CLASSES: List[str] = [
    "5-A", "5-B", "6-A", "6-B",
    "7-A", "7-T", "8-A", "8-T",
    "9-A", "9-B", "9-T", "10-A",
    "10-T", "11-A", "11-T"
]

DAYS: List[str] = [
    "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"
]


def load_schedule_data() -> Dict[str, Dict[str, List[str]]]:
    """schedule.json faylidan dars jadvalini o'qish."""
    if not SCHEDULE_FILE.exists():
        logger.warning(f"Dars jadvali fayli topilmadi: {SCHEDULE_FILE}")
        return {}
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Dars jadvalini o'qishda xatolik: {e}")
        return {}


def get_schedule(class_name: str, day_name: str) -> Optional[List[str]]:
    """Berilgan sinf va kun uchun darslar ro'yxatini qaytarish."""
    data = load_schedule_data()
    class_data = data.get(class_name)
    if not class_data:
        return None
    return class_data.get(day_name)
