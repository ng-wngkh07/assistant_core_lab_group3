#!/usr/bin/env python3
"""Check SQL queries in my_answers.sql against school.db."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

EXPECTED_QUERIES = {
    "Q1": "SELECT * FROM students;",
    "Q2": "SELECT name, year FROM students;",
    "Q3": "SELECT name FROM students WHERE program = 'CS';",
    "Q4": "SELECT name, year FROM students WHERE year >= 3;",
    "Q5": "SELECT name FROM students ORDER BY name DESC;",
    "Q6": "SELECT title, credits FROM courses WHERE credits = 4 ORDER BY title;",
    "Q7": "SELECT COUNT(*) FROM students;",
    "Q8": "SELECT program, COUNT(*) FROM students GROUP BY program ORDER BY program;",
    "Q9": "SELECT ROUND(AVG(grade), 2) FROM enrollments WHERE course_code = 'CSC10004';",
    "Q10": "SELECT student_id, course_code FROM enrollments WHERE grade IS NULL ORDER BY student_id;",
    "Q11": (
        "SELECT s.name, e.grade FROM enrollments e "
        "JOIN students s ON s.id = e.student_id "
        "WHERE e.course_code = 'CSC10014' AND e.grade IS NOT NULL ORDER BY s.name;"
    ),
    "Q12": (
        "SELECT c.title, COUNT(e.student_id) FROM courses c "
        "JOIN enrollments e ON e.course_code = c.code "
        "GROUP BY c.code, c.title ORDER BY COUNT(e.student_id) DESC, c.title;"
    ),
    "Q13": (
        "SELECT DISTINCT s.name FROM students s "
        "JOIN enrollments e ON e.student_id = s.id "
        "WHERE e.grade < 5 ORDER BY s.name;"
    ),
    "Q14": (
        "SELECT s.name, SUM(c.credits) AS credits FROM enrollments e "
        "JOIN students s ON s.id = e.student_id "
        "JOIN courses c ON c.code = e.course_code "
        "GROUP BY s.id, s.name ORDER BY credits DESC, s.name;"
    ),
    "Q15": (
        "SELECT s.name FROM students s "
        "LEFT JOIN enrollments e ON e.student_id = s.id AND e.course_code = 'CSC10014' "
        "WHERE e.student_id IS NULL ORDER BY s.name;"
    ),
}


def load_student_answers(sql_file: Path) -> dict[str, str]:
    content = sql_file.read_text(encoding="utf-8")
    blocks = re.split(r"--\s*(Q\d+)", content)
    answers = {}
    for i in range(1, len(blocks), 2):
        q_id = blocks[i].strip()
        sql = blocks[i + 1].strip()
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        if stmts:
            answers[q_id] = stmts[0] + ";"
    return answers


def run_checks():
    db_file = Path(__file__).parent / "school.db"
    sql_file = Path(__file__).parent / "my_answers.sql"

    if not db_file.exists():
        from make_school_db import create_school_db

        create_school_db(db_file)

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    student_answers = load_student_answers(sql_file)
    score = 0
    total = len(EXPECTED_QUERIES)

    for i in range(1, total + 1):
        q_id = f"Q{i}"
        ref_sql = EXPECTED_QUERIES[q_id]
        cur.execute(ref_sql)
        expected_rows = cur.fetchall()

        if q_id not in student_answers or not student_answers[q_id]:
            print(f"{q_id} .. not answered yet")
            continue

        try:
            cur.execute(student_answers[q_id])
            got_rows = cur.fetchall()
            if got_rows == expected_rows:
                print(f"{q_id} OK")
                score += 1
            else:
                print(f"{q_id} NO expected {expected_rows[:3]}, got {got_rows[:3]}")
        except sqlite3.Error as e:
            print(f"{q_id} ERROR: {e}")

    con.close()
    print(f"\nScore: {score}/{total}")
    return score == total


if __name__ == "__main__":
    run_checks()
