import html
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from database import get_test, save_submission

user_router = Router()


@user_router.message(CommandStart())
@user_router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    """Foydalanuvchiga botdan foydalanish yo'riqnomasini ko'rsatish."""
    name = html.escape(message.from_user.full_name if message.from_user else "Foydalanuvchi")
    
    await message.answer(
        f"Assalomu alaykum, <b>{name}</b>!\n\n"
        f"🤖 <b>Test Tekshiruvchi Botga xush kelibsiz!</b>\n\n"
        f"Ushbu bot orqali siz test natijalaringizni avtomatik va tezkor tekshirib olishingiz mumkin.\n\n"
        f"📝 <b>Javoblarni yuborish tartibi:</b>\n"
        f"Javoblarni quyidagi formatda yuboring:\n"
        f"<code>&lt;test_kodi&gt;*&lt;javoblar&gt;</code>\n\n"
        f"📌 <b>Masalan:</b>\n"
        f"<code>101*abcdabcdabcdabcdabcd</code>\n\n"
        f"🔹 <i>Harflar katta yoki kichik bo'lishining farqi yo'q (masalan: <b>A</b> yoki <b>a</b>).</i>\n"
        f"🔹 <i>Javoblar orasidagi bo'shliqlar (probellar) avtomatik tozalanadi.</i>\n\n"
        f"Boshlash uchun test kodi va javoblaringizni yuboring! 🎯",
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
