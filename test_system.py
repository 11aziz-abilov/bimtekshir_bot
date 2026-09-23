import asyncio
import os
import shutil
from pathlib import Path

# Test database
TEST_DB_PATH = Path("test_run.db")

async def run_tests():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    from database import (
        init_db,
        add_or_update_test,
        get_test,
        get_all_tests,
        save_submission,
        get_test_submissions,
    )

    print("=== 1. Testing Database Initialization ===")
    await init_db(TEST_DB_PATH)
    assert TEST_DB_PATH.exists(), "DB file was not created!"
    print("Database initialized successfully.")

    print("\n=== 2. Testing Test Creation and Update ===")
    # Add new test
    test_id = "101"
    keys = "abcdabcd"
    await add_or_update_test(test_id, keys, db_path=TEST_DB_PATH)
    test_row = await get_test(test_id, db_path=TEST_DB_PATH)
    assert test_row is not None, "Test not found!"
    assert test_row["test_id"] == "101"
    assert test_row["keys"] == "abcdabcd"
    print(f"Created test: {test_row}")

    # Update keys
    await add_or_update_test(test_id, "abcdabcda", db_path=TEST_DB_PATH)
    test_row2 = await get_test(test_id, db_path=TEST_DB_PATH)
    assert test_row2["keys"] == "abcdabcda"
    print(f"Updated test keys: {test_row2['keys']}")

    # Reset back to 8 questions
    await add_or_update_test("101", "abcdabcd", db_path=TEST_DB_PATH)
    await add_or_update_test("102", "bbccdd", db_path=TEST_DB_PATH)

    all_tests = await get_all_tests(db_path=TEST_DB_PATH)
    assert len(all_tests) == 2
    print(f"All tests count: {len(all_tests)}")

    print("\n=== 3. Testing Submissions & Leaderboard ===")
    # Student 1: 8/8
    await save_submission("101", 1001, "Ali Valiyev", "ali_v", 8, 8, db_path=TEST_DB_PATH)
    # Student 2: 6/8
    await save_submission("101", 1002, "Olim Rahimov", "olim_r", 6, 8, db_path=TEST_DB_PATH)
    # Student 3: 7/8
    await save_submission("101", 1003, "Zarina Saidova", None, 7, 8, db_path=TEST_DB_PATH)
    # Student 2 retries and gets 8/8
    await save_submission("101", 1002, "Olim Rahimov", "olim_r", 8, 8, db_path=TEST_DB_PATH)

    submissions = await get_test_submissions("101", unique_user=True, db_path=TEST_DB_PATH)
    print("Leaderboard results:")
    for rank, sub in enumerate(submissions, 1):
        print(f"  {rank}. {sub['full_name']} (@{sub['username']}) - {sub['score']}/{sub['total']} pts")

    assert len(submissions) == 3, f"Expected 3 unique users, got {len(submissions)}"
    # First place should have 8 points
    assert submissions[0]["score"] == 8
    # Ali submitted 8 first, so he should be first or tied at 8
    print("Leaderboard test passed!")

    print("\n=== 4. Testing Answer Evaluation Logic ===")
    test = await get_test("101", db_path=TEST_DB_PATH)
    correct_keys = test["keys"]  # "abcdabcd"
    total_questions = len(correct_keys)

    # Test user input parsing: " 101 * A B C D A B C A "
    raw_input = " 101 * A B C D A B C A "
    parts = raw_input.split("*", 1)
    parsed_id = parts[0].strip()
    parsed_answers = "".join(parts[1].split()).lower()

    assert parsed_id == "101"
    assert parsed_answers == "abcdabca"

    # Evaluation
    correct_count = 0
    wrong_answers = []
    for i in range(total_questions):
        u_ch = parsed_answers[i]
        c_ch = correct_keys[i]
        if u_ch == c_ch:
            correct_count += 1
        else:
            wrong_answers.append({
                "num": i + 1,
                "user": u_ch.upper(),
                "correct": c_ch.upper()
            })

    percent = round((correct_count / total_questions) * 100, 1)
    print(f"Correct: {correct_count}/{total_questions} ({percent}%)")
    print(f"Wrong answers: {wrong_answers}")

    assert correct_count == 7
    assert len(wrong_answers) == 1
    assert wrong_answers[0]["num"] == 8
    assert wrong_answers[0]["user"] == "A"
    assert wrong_answers[0]["correct"] == "D"
    print("Evaluation logic test passed!")

    # Cleanup test db
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    print("\n=== 5. Testing Schedule Service & Keyboards ===")
    from unittest.mock import AsyncMock, MagicMock
    from schedule_service import CLASSES, DAYS, load_schedule_data, get_schedule
    from handlers.user import (
        get_main_menu_keyboard,
        get_main_menu_inline,
        get_classes_keyboard,
        get_days_keyboard,
        get_schedule_view_keyboard,
        cb_select_day
    )

    # 5.1 Test classes and data
    expected_classes = [
        "5-A", "5-B", "6-A", "6-B",
        "7-A", "7-T", "8-A", "8-T",
        "9-A", "9-B", "9-T", "10-A",
        "10-T", "11-A", "11-T"
    ]
    assert CLASSES == expected_classes, f"Classes mismatch: {CLASSES}"
    assert len(CLASSES) == 15

    sched_data = load_schedule_data()
    assert len(sched_data) == 15, f"Expected 15 classes in schedule.json, found {len(sched_data)}"

    for c in expected_classes:
        assert c in sched_data, f"Class {c} not found in schedule.json"
        for d in ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma"]:
            assert d in sched_data[c], f"Day {d} missing for {c}"
            assert len(sched_data[c][d]) > 0, f"No lessons for {c} on {d}"

    # 6.2 Test get_schedule
    lessons_5a_mon = get_schedule("5-A", "Dushanba")
    assert lessons_5a_mon is not None
    assert "1. Kelajak soati" in lessons_5a_mon[0]
    assert len(lessons_5a_mon) == 6

    # Saturday should be None / rest day
    lessons_5a_sat = get_schedule("5-A", "Shanba")
    assert lessons_5a_sat is None

    # Invalid class
    assert get_schedule("99-Z", "Dushanba") is None
    print("Schedule data and get_schedule tests passed!")

    # 6.3 Test Keyboards
    main_kb = get_main_menu_keyboard()
    assert len(main_kb.keyboard[0]) == 2
    assert main_kb.keyboard[0][0].text == "📝 Test tekshirish"
    assert main_kb.keyboard[0][1].text == "📅 Dars jadvali"

    classes_kb = get_classes_keyboard()
    # 5 rows of 3 + 1 back row = 6 rows
    assert len(classes_kb.inline_keyboard) == 6
    class_buttons = [btn.text for row in classes_kb.inline_keyboard[:-1] for btn in row]
    assert class_buttons == expected_classes
    assert classes_kb.inline_keyboard[-1][0].callback_data == "back_to_main"

    days_kb = get_days_keyboard("5-A")
    # 3 rows of 2 + 1 back row = 4 rows
    assert len(days_kb.inline_keyboard) == 4
    day_buttons = [btn.text for row in days_kb.inline_keyboard[:-1] for btn in row]
    assert day_buttons == DAYS

    view_kb = get_schedule_view_keyboard("5-A")
    assert view_kb.inline_keyboard[0][0].callback_data == "class:5-A"
    assert view_kb.inline_keyboard[0][1].callback_data == "menu_schedule"
    print("Keyboards generation tests passed!")

    # 6.4 Test cb_select_day callback handler
    cb_mock = MagicMock()
    cb_mock.data = "day:5-A:Dushanba"
    cb_mock.answer = AsyncMock()
    cb_mock.message.edit_text = AsyncMock()
    await cb_select_day(cb_mock)
    cb_mock.answer.assert_awaited_once()
    cb_mock.message.edit_text.assert_awaited_once()
    call_args = cb_mock.message.edit_text.call_args[0]
    assert "5-A sinfi — Dushanba" in call_args[0]
    assert "Kelajak soati" in call_args[0]

    # Test Saturday rest day message
    cb_mock.reset_mock()
    cb_mock.data = "day:5-A:Shanba"
    cb_mock.answer = AsyncMock()
    cb_mock.message.edit_text = AsyncMock()
    await cb_select_day(cb_mock)
    call_args_sat = cb_mock.message.edit_text.call_args[0]
    assert "Dam olish kuni" in call_args_sat[0]
    print("Schedule day selection handler tests passed!")

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! [SUCCESS]")

if __name__ == "__main__":
    asyncio.run(run_tests())

