import aiosqlite
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, AsyncGenerator
from pathlib import Path
from config import DB_PATH


@asynccontextmanager
async def get_db(db_path: Path = DB_PATH) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Ma'lumotlar bazasiga xavfsiz ulanish konteksti menejeri."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db(db_path: Path = DB_PATH) -> None:
    """Jadvallarni yaratish va bazani ishga tushirish."""
    async with get_db(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                test_id TEXT PRIMARY KEY,
                keys TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                full_name TEXT,
                username TEXT,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Tezkor qidiruv uchun indekslar
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_test_id 
            ON submissions(test_id);
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_user_id 
            ON submissions(user_id);
        """)

        await db.commit()


async def add_or_update_test(test_id: str, keys: str, db_path: Path = DB_PATH) -> bool:
    """Yangi test qo'shish yoki mavjud test kalitlarini yangilash."""
    clean_test_id = test_id.strip()
    clean_keys = keys.strip().lower()

    async with get_db(db_path) as db:
        await db.execute("""
            INSERT INTO tests (test_id, keys, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(test_id) DO UPDATE SET
                keys = excluded.keys,
                created_at = CURRENT_TIMESTAMP;
        """, (clean_test_id, clean_keys))
        await db.commit()
        return True


async def get_test(test_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Test ma'lumotlarini test_id bo'yicha olish."""
    clean_test_id = test_id.strip()
    async with get_db(db_path) as db:
        async with db.execute(
            "SELECT test_id, keys, created_at FROM tests WHERE test_id = ?",
            (clean_test_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def get_all_tests(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Barcha faol testlarni olish (yangi kiritilganlari oldinda)."""
    async with get_db(db_path) as db:
        async with db.execute(
            "SELECT test_id, keys, created_at FROM tests ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def save_submission(
    test_id: str,
    user_id: int,
    full_name: str,
    username: Optional[str],
    score: int,
    total: int,
    db_path: Path = DB_PATH
) -> int:
    """O'quvchi javob natijasini saqlash."""
    async with get_db(db_path) as db:
        cursor = await db.execute("""
            INSERT INTO submissions (test_id, user_id, full_name, username, score, total, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (test_id.strip(), user_id, full_name, username, score, total))
        await db.commit()
        return cursor.lastrowid or 0


async def get_test_submissions(
    test_id: str,
    unique_user: bool = True,
    db_path: Path = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Test bo'yicha o'quvchilar natijalarini olish.
    Eng yuqori ball va topshirilgan vaqti bo'yicha saralanadi.
    unique_user=True bo'lsa har bir o'quvchining eng yaxshi natijasi olinadi.
    """
    clean_test_id = test_id.strip()
    async with get_db(db_path) as db:
        if unique_user:
            query = """
                WITH RankedSubmissions AS (
                    SELECT id, test_id, user_id, full_name, username, score, total, submitted_at,
                           ROW_NUMBER() OVER (
                               PARTITION BY user_id 
                               ORDER BY score DESC, submitted_at ASC
                           ) as rank_num
                    FROM submissions
                    WHERE test_id = ?
                )
                SELECT id, test_id, user_id, full_name, username, score, total, submitted_at
                FROM RankedSubmissions
                WHERE rank_num = 1
                ORDER BY score DESC, submitted_at ASC;
            """
        else:
            query = """
                SELECT id, test_id, user_id, full_name, username, score, total, submitted_at
                FROM submissions
                WHERE test_id = ?
                ORDER BY score DESC, submitted_at ASC;
            """

        async with db.execute(query, (clean_test_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
