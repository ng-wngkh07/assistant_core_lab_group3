"""Unit tests for school_repo.py (Exercises D1–D3)."""

import sqlite3

import pytest
from school_repo import (
    add_student,
    average_grade,
    students_in_program,
    transcript,
)


@pytest.fixture
def con():
    """Create a fresh in-memory database with schema and sample seed."""
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            year INTEGER NOT NULL,
            program TEXT NOT NULL
        );
        CREATE TABLE courses (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL
        );
        CREATE TABLE enrollments (
            student_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            grade REAL,
            PRIMARY KEY (student_id, course_code),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_code) REFERENCES courses(code)
        );
        INSERT INTO students (id, name, year, program) VALUES
            (1, 'An', 1, 'CS'),
            (2, 'Binh', 2, 'SE'),
            (3, 'Chi', 2, 'CS');
        INSERT INTO courses (code, title, credits) VALUES
            ('CSC10001', 'Intro CS', 4),
            ('CSC10004', 'OOP', 4);
        INSERT INTO enrollments (student_id, course_code, grade) VALUES
            (1, 'CSC10001', 8.5),
            (1, 'CSC10004', 7.5),
            (2, 'CSC10004', 6.0),
            (3, 'CSC10004', NULL);
    """)
    yield c
    c.close()


def test_example_students_in_program(con):
    rows = students_in_program(con, "CS")
    assert rows == [("An",), ("Chi",)]


def test_d1_add_student(con):
    sid = add_student(con, "Dung", 3, "AI")
    assert sid == 4
    row = con.execute("SELECT name, year, program FROM students WHERE id = ?", (sid,)).fetchone()
    assert row == ("Dung", 3, "AI")


def test_d1_no_sql_injection(con):
    """Placeholder ? guarantees that injection strings are treated purely as string literals."""
    payload = "Hacker', 1, 'CS'); DROP TABLE students;--"
    sid = add_student(con, payload, 1, "CS")
    assert sid is not None

    # Table students must still exist and payload is stored as literal name
    row = con.execute("SELECT name FROM students WHERE id = ?", (sid,)).fetchone()
    assert row[0] == payload
    count = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    assert count == 4


def test_d2_average_grade(con):
    avg = average_grade(con, "CSC10004")
    # Graded rows: 7.5 and 6.0 (NULL skipped) -> (7.5 + 6.0) / 2 = 6.75
    assert avg == 6.75

    # Course with no enrollments
    assert average_grade(con, "NONEXISTENT") is None


def test_d3_transcript(con):
    rows = transcript(con, 1)
    assert len(rows) == 2
    assert rows[0] == ("Intro CS", 4, 8.5)
    assert rows[1] == ("OOP", 4, 7.5)
