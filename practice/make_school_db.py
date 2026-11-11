#!/usr/bin/env python3
"""Create and populate school.db practice database."""

import sqlite3
from pathlib import Path


def create_school_db(db_path: Path | str = "school.db") -> None:
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            program TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE courses (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE enrollments (
            student_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            grade REAL,
            PRIMARY KEY (student_id, course_code),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_code) REFERENCES courses(code)
        );
    """)

    students_data = [
        (1, "An", 1, "CS"),
        (2, "Binh", 2, "SE"),
        (3, "Chi", 2, "CS"),
        (4, "Dung", 3, "AI"),
        (5, "Giang", 3, "SE"),
        (6, "Hoa", 4, "CS"),
        (7, "Khoa", 2, "AI"),
        (8, "Lan", 1, "DS"),
    ]

    courses_data = [
        ("CSC10001", "Introduction to Computer Science", 4),
        ("CSC10004", "Object-Oriented Programming", 4),
        ("CSC10014", "Practical Software Engineering", 4),
        ("MTH00001", "Calculus 1", 3),
        ("MTH00003", "Linear Algebra", 3),
    ]

    enrollments_data = [
        (1, "CSC10001", 8.5),
        (1, "MTH00003", 6.0),
        (1, "CSC10014", 9.0),
        (2, "CSC10014", None),  # un-graded
        (2, "CSC10004", 7.0),
        (3, "CSC10001", 7.5),
        (3, "CSC10004", 8.0),
        (3, "CSC10014", 6.5),
        (4, "CSC10004", 4.0),  # grade < 5
        (4, "MTH00001", 5.5),
        (5, "CSC10014", 8.0),
        (5, "CSC10004", 4.5),  # grade < 5
        (6, "CSC10001", 9.5),
        (6, "CSC10004", 9.0),
        (7, "MTH00001", None),  # un-graded
        (7, "CSC10004", 6.5),
        (8, "MTH00003", 7.0),   # Lan not enrolled in CSC10014
    ]

    cur.executemany("INSERT INTO students (id, name, year, program) VALUES (?, ?, ?, ?)", students_data)
    cur.executemany("INSERT INTO courses (code, title, credits) VALUES (?, ?, ?)", courses_data)
    cur.executemany("INSERT INTO enrollments (student_id, course_code, grade) VALUES (?, ?, ?)", enrollments_data)

    con.commit()

    cur.execute("SELECT COUNT(*) FROM students")
    s_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM courses")
    c_cnt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrollments")
    e_cnt = cur.fetchone()[0]

    print(f"students    {s_cnt} rows")
    print(f"courses     {c_cnt} rows")
    print(f"enrollments {e_cnt} rows")

    con.close()


if __name__ == "__main__":
    create_school_db()
