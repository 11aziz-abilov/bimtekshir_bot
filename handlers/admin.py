import html
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from filters import IsAdmin
from database import add_or_update_test, get_test, get_all_tests, get_test_submissions

admin_router = Router()
# Ushbu routerdagi barcha xabarlar faqat admin uchun
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("new"))
async def cmd_new_test(message: Message) -> None:
    """
    Yangi test qo'shish yoki eskisini yangilash.
    Format: /new <test_id> <keys>
    Misol: /new 101 abcdabcdabcd
    """
    text = (message.text or "").strip()
    parts = text.split()

    if len(parts) < 3:
        await message.answer(
            "⚠️ <b>Noto'g'ri buyruq formati!</b>\n\n"
            "Format: <code>/new &lt;test_kodi&gt; &lt;kalitlar&gt;</code>\n"
            "Misol: <code>/new 101 abcdabcdabcd</code>\n\n"
            "<i>Eslatma: Kalitlar katta yoki kichik harflarda kiritilishi mumkin.</i>",
            parse_mode="HTML"
        )
        return

    test_id = parts[1].strip()
    # Kalitlardagi ortiqcha probellarni tozalab, bitta qatorga birlashtiramiz va kichik harfga o'tkazamiz
    raw_keys = "".join(parts[2:]).strip().lower()

    # Faqat harflar yoki raqamlardan iboratligini tekshirish
    if not raw_keys.isalnum():
        await message.answer(
            "⚠️ <b>Xatolik:</b> Test kalitlarida faqat harf va raqamlar qatnashishi kerak!",
            parse_mode="HTML"
        )
        return

    await add_or_update_test(test_id, raw_keys)

    await message.answer(
        f"✅ <b>Test muvaffaqiyatli saqlandi!</b>\n\n"
        f"🆔 <b>Test kodi:</b> <code>{html.escape(test_id)}</code>\n"
        f"📝 <b>Savollar soni:</b> <code>{len(raw_keys)}</code> ta\n"
        f"🔑 <b>Kalitlar:</b> <code>{html.escape(raw_keys.upper())}</code>\n\n"
        f"O'quvchilar javob yuborish formati:\n"
        f"<code>{html.escape(test_id)}*{html.escape(raw_keys)}</code>",
        parse_mode="HTML"
    )


@admin_router.message(Command("list"))
async def cmd_list_tests(message: Message) -> None:
    """Bazadagi barcha faol testlar va ularning savollar sonini ko'rish."""
    tests = await get_all_tests()

    if not tests:
        await message.answer(
            "📂 <b>Hozircha bazada birorta ham test mavjud emas.</b>\n\n"
            "Yangi test qo'shish uchun: <code>/new &lt;test_id&gt; &lt;kalitlar&gt;</code>",
            parse_mode="HTML"
        )
        return

    lines = ["📋 <b>Bazada mavjud testlar ro'yxati:</b>\n"]
    for idx, test in enumerate(tests, start=1):
        t_id = test["test_id"]
        t_keys = test["keys"]
        q_count = len(t_keys)
        created = str(test["created_at"])[:16]
        lines.append(
            f"<b>{idx}.</b> 🆔 <b>Kodi:</b> <code>{html.escape(t_id)}</code> | "
            f"📝 <b>Savollar:</b> {q_count} ta\n"
            f"     📅 <i>{created}</i> | Natijalar: /results_{html.escape(t_id)}"
        )

    lines.append(
        "\n💡 <i>Natijalarni ko'rish uchun <code>/results &lt;test_id&gt;</code> buyrug'idan foydalaning.</i>"
    )

    await message.answer("\n".join(lines), parse_mode="HTML")


@admin_router.message(Command(commands=["results"]))
async def cmd_test_results(message: Message) -> None:
    """
    Test bo'yicha o'quvchilar reytingini chiqarish.
    Format: /results <test_id> yoki /results_<test_id>
    """
    text = (message.text or "").strip()
    test_id = ""

    # /results_101 formatini ham qo'llab-quvvatlaymiz
    if text.startswith("/results_"):
        test_id = text.split("/results_")[1].strip()
    else:
        parts = text.split()
        if len(parts) >= 2:
            test_id = parts[1].strip()

    if not test_id:
        await message.answer(
            "⚠️ <b>Test kodini kiriting!</b>\n\n"
            "Format: <code>/results &lt;test_kodi&gt;</code>\n"
            "Misol: <code>/results 101</code>",
            parse_mode="HTML"
        )
        return

    # Test mavjudligini tekshiramiz
    test = await get_test(test_id)
    if not test:
        await message.answer(
            f"❌ <code>{html.escape(test_id)}</code> kodli test topilmadi!\n"
            f"Barcha testlarni ko'rish uchun: /list",
            parse_mode="HTML"
        )
        return

    submissions = await get_test_submissions(test_id, unique_user=True)

    if not submissions:
        await message.answer(
            f"📊 <b>Test kodi:</b> <code>{html.escape(test_id)}</code>\n"
            f"📝 <b>Savollar soni:</b> {len(test['keys'])} ta\n\n"
            f"ℹ️ <i>Hozircha ushbu test bo'yicha hech kim javob topshirmagan.</i>",
            parse_mode="HTML"
        )
        return

    total_questions = len(test["keys"])
    lines = [
        f"🏆 <b>«{html.escape(test_id)}» testi bo'yicha o'quvchilar reytingi:</b>",
        f"📝 Jami savollar soni: <b>{total_questions}</b> ta\n"
    ]

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for idx, sub in enumerate(submissions, start=1):
        place_icon = medals.get(idx, f"<b>{idx}.</b>")
        name = html.escape(sub["full_name"] or "Noma'lum")
        username_str = f" (@{html.escape(sub['username'])})" if sub["username"] else ""
        score = sub["score"]
        total = sub["total"]
        percent = round((score / total) * 100, 1) if total > 0 else 0
        submitted_at = str(sub["submitted_at"])[:16]

        lines.append(
            f"{place_icon} <b>{name}</b>{username_str}\n"
            f"   └ 🎯 Natija: <b>{score}/{total}</b> ({percent}%) | ⏱ <i>{submitted_at}</i>"
        )

    lines.append(f"\n👥 <b>Jami qatnashchilar:</b> {len(submissions)} nafar")

    # Telegram xabar uzunligi chegarasi 4096 belgi
    full_text = "\n".join(lines)
    if len(full_text) <= 4000:
        await message.answer(full_text, parse_mode="HTML")
    else:
        # Uzun bo'lsa qismlarga bo'lib yuboramiz
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > 4000:
                await message.answer(chunk, parse_mode="HTML")
                chunk = line + "\n"
            else:
                chunk += line + "\n"
        if chunk:
            await message.answer(chunk, parse_mode="HTML")
