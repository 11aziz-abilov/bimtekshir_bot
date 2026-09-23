import html
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    User
)
from database import get_test, save_submission
from config import get_channel_url, CHANNEL_USERNAME
from filters import is_subscribed
from schedule_service import CLASSES, DAYS, get_schedule

user_router = Router()

TEST_INSTRUCTION_TEXT = (
    "📝 <b>TEST TEKSHIRISH TARTIBI:</b>\n\n"
    "Javoblarni quyidagi formatda yuboring:\n"
    "<code>&lt;test_kodi&gt;*&lt;javoblar&gt;</code>\n\n"
    "📌 <b>Masalan:</b>\n"
    "<code>101*abcdabcdabcdabcdabcd</code>\n\n"
    "🔹 <i>Harflar katta yoki kichik bo'lishining farqi yo'q (masalan: <b>A</b> yoki <b>a</b>).</i>\n"
    "🔹 <i>Javoblar orasidagi bo'shliqlar (probellar) avtomatik tozalanadi.</i>\n\n"
    "Boshlash uchun test kodi va javoblaringizni yuboring! 🎯"
)

SCHEDULE_PROMPT_TEXT = (
    "📅 <b>DARS JADVALI</b>\n\n"
    "Dars jadvalini ko'rish uchun sinfni tanlang:"
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy pastki menyu tugmalari."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Test tekshirish"),
                KeyboardButton(text="📅 Dars jadvali")
            ]
        ],
        resize_keyboard=True
    )


def get_main_menu_inline() -> InlineKeyboardMarkup:
    """Asosiy inline menyu tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Test tekshirish", callback_data="menu_test"),
                InlineKeyboardButton(text="📅 Dars jadvali", callback_data="menu_schedule")
            ]
        ]
    )


def get_classes_keyboard() -> InlineKeyboardMarkup:
    """Sinflar ro'yxatini chiqaruvchi inline klaviatura (3 tadan qatorda)."""
    rows = []
    for i in range(0, len(CLASSES), 3):
        chunk = CLASSES[i:i + 3]
        rows.append([InlineKeyboardButton(text=c, callback_data=f"class:{c}") for c in chunk])
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_days_keyboard(class_name: str) -> InlineKeyboardMarkup:
    """Tanlangan sinf uchun hafta kunlari klaviaturasi (2 tadan qatorda)."""
    rows = []
    for i in range(0, len(DAYS), 2):
        chunk = DAYS[i:i + 2]
        rows.append([InlineKeyboardButton(text=d, callback_data=f"day:{class_name}:{d}") for d in chunk])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="menu_schedule")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_schedule_view_keyboard(class_name: str) -> InlineKeyboardMarkup:
    """Dars jadvali ko'rilayotganda navigatsiya tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Boshqa kun", callback_data=f"class:{class_name}"),
                InlineKeyboardButton(text="🏫 Barcha sinflar", callback_data="menu_schedule")
            ]
        ]
    )


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Majburiy kanal a'zoligi uchun inline tugmalar."""
    channel_url = get_channel_url()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=channel_url)
            ],
            [
                InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")
            ]
        ]
    )
    return keyboard


async def send_subscription_prompt(message: Message) -> None:
    """Foydalanuvchiga kanalga a'zo bo'lish talabini yuborish."""
    channel_url = get_channel_url()
    channel_display = CHANNEL_USERNAME or "Rasmiy kanalimiz"
    if channel_display.startswith(("http://", "https://")):
        slug = channel_display.rstrip("/").split("/")[-1]
        if slug and not slug.startswith("+"):
            channel_display = f"@{slug}"

    text = (
        "⚠️ <b>Botdan foydalanish uchun kanalimizga a'zo bo'ling!</b>\n\n"
        "Bot imkoniyatlaridan to'liq foydalanish va test natijalarini bilish uchun "
        "quyidagi rasmiy kanalimizga obuna bo'lishingiz lozim:\n\n"
        f"👉 <b>Kanal:</b> <a href=\"{channel_url}\">{html.escape(channel_display)}</a>\n\n"
        "<i>Kanalga a'zo bo'lgach, pastdagi <b>«✅ Obunani tekshirish»</b> tugmasini bosing.</i>"
    )
    await message.answer(
        text,
        reply_markup=get_subscription_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def send_welcome_message(message: Message, user: Optional[User] = None) -> None:
    """Foydalanuvchiga botdan foydalanish yo'riqnomasini ko'rsatish."""
    target_user = user or message.from_user
    name = html.escape(target_user.full_name if target_user else "Foydalanuvchi")

    text = (
        f"Assalomu alaykum, <b>{name}</b>!\n\n"
        f"🤖 <b>Test Tekshiruvchi va Dars Jadvali Botiga xush kelibsiz!</b>\n\n"
        f"Quyidagi bo'limlardan birini tanlang:\n"
        f"• <b>📝 Test tekshirish</b> — test javoblarini tekshirish va reyting\n"
        f"• <b>📅 Dars jadvali</b> — sinflar bo'yicha dars jadvalini ko'rish"
    )
    await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await message.answer(
        "👇 <i>Kerakli bo'limni tanlang:</i>",
        reply_markup=get_main_menu_inline(),
        parse_mode="HTML"
    )


@user_router.callback_query(F.data == "check_sub")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    """Foydalanuvchi 'Obunani tekshirish' tugmasini bosganda a'zolikni qayta tekshirish."""
    user = callback.from_user
    if not user:
        await callback.answer("Foydalanuvchi aniqlanmadi.", show_alert=True)
        return

    subscribed = await is_subscribed(bot, user.id)
    if subscribed:
        await callback.answer("✅ Rahmat! Obunangiz tasdiqlandi.", show_alert=False)
        try:
            if callback.message:
                await callback.message.delete()
        except Exception:
            pass

        if callback.message:
            await send_welcome_message(callback.message, user=user)
    else:
        await callback.answer(
            "❌ Siz hali kanalga a'zo bo'lmadingiz!\n\n"
            "Iltimos, avval kanalga obuna bo'ling va so'ng qayta tekshiring.",
            show_alert=True
        )


@user_router.message(CommandStart())
@user_router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    """Foydalanuvchiga botdan foydalanish yo'riqnomasini ko'rsatish."""
    await send_welcome_message(message, user=message.from_user)


@user_router.message(F.text == "📝 Test tekshirish")
async def msg_test_instructions(message: Message) -> None:
    """'Test tekshirish' tugmasi bosilganda yo'riqnoma ko'rsatish."""
    await message.answer(TEST_INSTRUCTION_TEXT, parse_mode="HTML")


@user_router.callback_query(F.data == "menu_test")
async def cb_test_instructions(callback: CallbackQuery) -> None:
    """Inline 'Test tekshirish' tugmasi bosilganda yo'riqnoma ko'rsatish."""
    await callback.answer()
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="back_to_main")]]
    )
    try:
        await callback.message.edit_text(TEST_INSTRUCTION_TEXT, reply_markup=back_kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(TEST_INSTRUCTION_TEXT, reply_markup=back_kb, parse_mode="HTML")


@user_router.message(F.text == "📅 Dars jadvali")
async def msg_schedule_menu(message: Message) -> None:
    """'Dars jadvali' tugmasi bosilganda sinflar ro'yxatini chiqarish."""
    await message.answer(
        SCHEDULE_PROMPT_TEXT,
        reply_markup=get_classes_keyboard(),
        parse_mode="HTML"
    )


@user_router.callback_query(F.data == "menu_schedule")
async def cb_schedule_menu(callback: CallbackQuery) -> None:
    """Inline 'Dars jadvali' bosilganda sinflar ro'yxatini chiqarish."""
    await callback.answer()
    try:
        await callback.message.edit_text(
            SCHEDULE_PROMPT_TEXT,
            reply_markup=get_classes_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            SCHEDULE_PROMPT_TEXT,
            reply_markup=get_classes_keyboard(),
            parse_mode="HTML"
        )


@user_router.callback_query(F.data == "back_to_main")
async def cb_back_to_main(callback: CallbackQuery) -> None:
    """Bosh menyuga qaytish."""
    await callback.answer()
    text = (
        "🤖 <b>Asosiy menyu</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu_inline(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=get_main_menu_inline(),
            parse_mode="HTML"
        )


@user_router.callback_query(F.data.startswith("class:"))
async def cb_select_class(callback: CallbackQuery) -> None:
    """Sinf tanlanganda hafta kunlarini chiqarish."""
    await callback.answer()
    class_name = callback.data.split("class:")[1].strip()
    text = (
        f"🏫 <b>{html.escape(class_name)} sinfi</b>\n\n"
        "Dars jadvalini ko'rish uchun hafta kunini tanlang:"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_days_keyboard(class_name),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=get_days_keyboard(class_name),
            parse_mode="HTML"
        )


@user_router.callback_query(F.data.startswith("day:"))
async def cb_select_day(callback: CallbackQuery) -> None:
    """Kun tanlanganda darslar ro'yxatini chiqarish."""
    await callback.answer()
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        return
    class_name = parts[1].strip()
    day_name = parts[2].strip()

    lessons = get_schedule(class_name, day_name)
    if lessons:
        lessons_list = "\n".join(f"  {html.escape(lesson)}" for lesson in lessons)
        text = (
            f"📅 <b>{html.escape(class_name)} sinfi — {html.escape(day_name)}</b>\n\n"
            f"📚 <b>Darslar ro'yxati:</b>\n"
            f"{lessons_list}"
        )
    else:
        text = (
            f"📅 <b>{html.escape(class_name)} sinfi — {html.escape(day_name)}</b>\n\n"
            f"🏖 <i>Ushbu kunda darslar mavjud emas (Dam olish kuni).</i>"
        )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_schedule_view_keyboard(class_name),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=get_schedule_view_keyboard(class_name),
            parse_mode="HTML"
        )




@user_router.message(F.text)
async def handle_test_submission(message: Message) -> None:
    """Foydalanuvchi yuborgan test javoblarini qabul qilish va tekshirish."""
    text = (message.text or "").strip()

    # Agar buyruq bo'lsa va yuqoridagi handlerlarga tushmagan bo'lsa
    if text.startswith("/"):
        await message.answer(
            "⚠️ Noma'lum buyruq! Botdan foydalanish bo'yicha yo'riqnoma: /start",
            parse_mode="HTML"
        )
        return

    # test_kodi*javoblar formatini tekshiramiz
    if "*" not in text:
        await message.answer(
            "⚠️ <b>Javob formati noto'g'ri!</b>\n\n"
            "Javoblarni quyidagi ko'rinishda yuboring:\n"
            "<code>&lt;test_kodi&gt;*&lt;javoblar&gt;</code>\n\n"
            "📌 <b>Masalan:</b> <code>101*abcdabcdabcd</code>\n"
            "Qo'shimcha ma'lumot uchun: /start",
            parse_mode="HTML"
        )
        return

    parts = text.split("*", 1)
    test_id = parts[0].strip()
    # Javoblardagi barcha bo'shliqlarni olib tashlaymiz va kichik harflarga o'tkazamiz
    user_answers = "".join(parts[1].split()).lower()

    if not test_id:
        await message.answer(
            "⚠️ <b>Test kodi kiritilmadi!</b>\n\n"
            "Misol: <code>101*abcd...</code>",
            parse_mode="HTML"
        )
        return

    if not user_answers:
        await message.answer(
            "⚠️ <b>Javoblar ketma-ketligi kiritilmadi!</b>\n\n"
            "Misol: <code>101*abcd...</code>",
            parse_mode="HTML"
        )
        return

    # Bazadan testni qidiramiz
    test = await get_test(test_id)
    if not test:
        await message.answer(
            f"❌ <b>Xatolik:</b> <code>{html.escape(test_id)}</code> kodli test bazada topilmadi!\n\n"
            f"Iltimos, test kodini to'g'ri kiritganingizni qayta tekshiring.",
            parse_mode="HTML"
        )
        return

    correct_keys = test["keys"]
    total_questions = len(correct_keys)
    user_len = len(user_answers)

    # Savollar sonini tekshirish
    if user_len != total_questions:
        if user_len < total_questions:
            diff = total_questions - user_len
            diff_msg = f"❗️ Siz <b>{diff}</b> ta kam javob yubordingiz."
        else:
            diff = user_len - total_questions
            diff_msg = f"❗️ Siz <b>{diff}</b> ta ortiqcha javob yubordingiz."

        await message.answer(
            f"⚠️ <b>Savollar soni mos kelmadi!</b>\n\n"
            f"🆔 <b>Test kodi:</b> <code>{html.escape(test_id)}</code>\n"
            f"📋 <b>Testdagi savollar soni:</b> <code>{total_questions}</code> ta\n"
            f"📥 <b>Siz yuborgan javoblar:</b> <code>{user_len}</code> ta\n\n"
            f"{diff_msg}\n\n"
            f"<i>Iltimos, barcha savollarga to'liq javob yozib qayta yuboring.</i>",
            parse_mode="HTML"
        )
        return

    # Javoblarni birma-bir tekshirish
    correct_count = 0
    wrong_answers = []

    for i in range(total_questions):
        user_ch = user_answers[i]
        correct_ch = correct_keys[i]

        if user_ch == correct_ch:
            correct_count += 1
        else:
            wrong_answers.append({
                "num": i + 1,
                "user": user_ch.upper(),
                "correct": correct_ch.upper()
            })

    # Foizni hisoblash
    percentage = round((correct_count / total_questions) * 100, 1)

    # Natijani bazaga saqlash
    from_user = message.from_user
    user_id = from_user.id if from_user else 0
    full_name = from_user.full_name if from_user else "Noma'lum"
    username = from_user.username if from_user else None

    await save_submission(
        test_id=test_id,
        user_id=user_id,
        full_name=full_name,
        username=username,
        score=correct_count,
        total=total_questions
    )

    # Baholash xabari
    if percentage >= 90:
        grade_badge = "🌟 A'lo natija!"
    elif percentage >= 70:
        grade_badge = "👍 Yaxshi natija!"
    elif percentage >= 50:
        grade_badge = "👌 Qoniqarli natija!"
    else:
        grade_badge = "💪 Yana ko'proq tayyorlaning!"

    result_lines = [
        f"📊 <b>TEST NATIJASI</b>\n",
        f"👤 <b>O'quvchi:</b> {html.escape(full_name)}",
        f"🆔 <b>Test kodi:</b> <code>{html.escape(test_id)}</code>",
        f"🎯 <b>To'g'ri javoblar:</b> <b>{correct_count}</b> / {total_questions} ta",
        f"📈 <b>Natija:</b> <b>{percentage}%</b>",
        f"🏅 <b>Holat:</b> {grade_badge}\n"
    ]

    if not wrong_answers:
        result_lines.append("🎉 <b>Barcha javoblar to'g'ri! Sizni tabriklaymiz! 💯</b>")
    else:
        result_lines.append(f"❌ <b>Xato qilingan savollar ({len(wrong_answers)} ta):</b>")
        for item in wrong_answers:
            result_lines.append(
                f"  • {item['num']}-savol: Sizning javobingiz ({item['user']}) ➔ To'g'ri ({item['correct']})"
            )

    full_message = "\n".join(result_lines)

    # Telegram 4096 belgi chegarasi nazorati
    if len(full_message) <= 4000:
        await message.answer(full_message, parse_mode="HTML")
    else:
        # Xatolar ko'p bo'lganda qismlarga bo'lib yuborish
        chunk = ""
        for line in result_lines:
            if len(chunk) + len(line) + 1 > 4000:
                await message.answer(chunk, parse_mode="HTML")
                chunk = line + "\n"
            else:
                chunk += line + "\n"
        if chunk:
            await message.answer(chunk, parse_mode="HTML")
