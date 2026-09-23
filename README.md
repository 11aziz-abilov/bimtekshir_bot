# 🤖 Telegram Test Tekshiruvchi Bot

Ushbu loyiha **Python**, **aiogram 3.x** va asinxron **SQLite** (`aiosqlite`) yordamida yaratilgan to'liq funksional Telegram botidir. O'quvchilar test javoblarini yuborib bir zumda natijalarini (to'g'ri/xato savollar tahlili, foiz) bilib olishlari, o'qituvchi/adminlar esa yangi testlar kiritib, natijalar reytingini ko'rishlari mumkin.

---

## 🌟 Asosiy imkoniyatlar

### 👤 Foydalanuvchilar (O'quvchilar) uchun:
- **`/start` va `/help`**: Botdan foydalanish bo'yicha to'liq o'zbekcha yo'riqnoma va asosiy menyu:
  - 📝 **Test tekshirish**: test javoblarini tezkor topshirish;
  - 📅 **Dars jadvali**: 5-11-sinflar kesimida kunlar bo'yicha haftalik darslar jadvalini ko'rish.
- **Javoblarni tezkor tekshirish**: `test_kodi*javoblar` formatida yuboriladi (masalan: `101*abcdabcd...`).
- **Dars jadvali moduli**: `schedule.json` faylidan barcha 15 ta sinf (5-A dan 11-T gacha) darslarini interaktiv tugmalar orqali qulay ko'rsatish.
- **Xatoliklarga chidamli**: Katta-kichik harflar (A/a) e'tiborga olinmaydi, keraksiz probellar tozalanadi.
- **Savollar sonini nazorat qilish**: Javoblar soni testdagi savollar soniga teng bo'lmasa, aniq farq (kam yoki ortiqcha ekanligi) ko'rsatiladi.
- **Batafsil natijalar va tahlil**:
  - To'g'ri javoblar soni va umumiy savollar nisbati;
  - Foiz ko'rsatkichi (`%`);
  - Har bir xato qilingan savol bo'yicha aniq ma'lumot: `❌ 4-savol: Sizning javobingiz (A) ➔ To'g'ri (B)`.
- Natijalar avtomatik tarzda `submissions` jadvaliga yozib boriladi.

### 👑 Admin (O'qituvchi) uchun:
- **`/new <test_id> <keys>`**: Yangi test qo'shish yoki mavjud test kalitlarini yangilash.
  - *Misol:* `/new 101 abcdabcdabcd`
- **`/list`**: Bazadagi barcha faol testlar, ulardagi savollar soni va yaratilgan vaqtini ko'rish.
- **`/results <test_id>`**: Test bo'yicha o'quvchilar reytingi (eng yuqori ball va topshirgan vaqti bo'yicha saralangan, 🥇 🥈 🥉 sovrindorlar ajratilgan).
  - *Misol:* `/results 101`

---

## 🗄 Ma'lumotlar bazasi tuzilishi (`tests.db`)

Bot SQLite ma'lumotlar bazasidan foydalanadi va birinchi ishga tushganda jadvallarni avtomatik yaratadi:

1. **`tests`** jadvali:
   - `test_id` (TEXT PRIMARY KEY) — Test kodi;
   - `keys` (TEXT) — To'g'ri javoblar ketma-ketligi (kichik harflarda);
   - `created_at` (TIMESTAMP) — Yaratilgan / yangilangan vaqti.

2. **`submissions`** jadvali:
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT) — Yozuv identifikatori;
   - `test_id` (TEXT) — Test kodi;
   - `user_id` (INTEGER) — Foydalanuvchining Telegram ID si;
   - `full_name` (TEXT) — O'quvchining ismi va familiyasi;
   - `username` (TEXT) — Telegram username (@...);
   - `score` (INTEGER) — To'g'ri javoblar soni;
   - `total` (INTEGER) — Testdagi jami savollar soni;
   - `submitted_at` (TIMESTAMP) — Topshirilgan vaqti.

---

## 🚀 O'rnatish va Ishga tushirish

### 1. Talablar:
- Python 3.10 yoki undan yuqori talab qilinadi.

### 2. Kutubxonalarni o'rnatish:
Terminalda loyiha papkasiga kiring va quyidagi buyruqni bajaring:
```bash
pip install -r requirements.txt
```

### 3. Sozlamalarni kiritish (`.env`):
Loyiha papkasidagi `.env` faylini oching va qiymatlarni kiriting:
```env
# @BotFather orqali olingan token
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# O'zingizning Telegram user ID raqamingiz (@userinfobot orqali bilish mumkin)
ADMIN_ID=123456789
```

### 4. Botni ishga tushirish:
```bash
python main.py
```

---

## 🧪 Avtomatlashtirilgan testlarni tekshirish:
Loyihaning barcha funksiyalarini (baza, test tekshirish va dars jadvali) tekshirish uchun:
```bash
python test_system.py
```

