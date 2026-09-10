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
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! [SUCCESS]")

if __name__ == "__main__":
    asyncio.run(run_tests())
