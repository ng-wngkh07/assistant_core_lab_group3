"""School database repository functions (Exercises D1–D3)."""

from __future__ import annotations

import sqlite3


def students_in_program(con: sqlite3.Connection, program: str) -> list[tuple[str]]:
    """Example function: Returns all student names in a program."""
    cur = con.execute("SELECT name FROM students WHERE program = ? ORDER BY name", (program,))
    return cur.fetchall()


def add_student(con: sqlite3.Connection, name: str, year: int, program: str) -> int:
    """D1: Add a new student and return their generated primary key id."""
    cur = con.execute(
        "INSERT INTO students (name, year, program) VALUES (?, ?, ?)",
        (name, year, program),
    )
    con.commit()
    return cur.lastrowid


def average_grade(con: sqlite3.Connection, code: str) -> float | None:
    """D2: Return average grade for a course, rounded to 2 decimals, or None if no grades."""
    cur = con.execute(
        "SELECT ROUND(AVG(grade), 2) FROM enrollments WHERE course_code = ?",
        (code,),
    )
    row = cur.fetchone()
    if row and row[0] is not None:
        return float(row[0])
    return None


def transcript(con: sqlite3.Connection, student_id: int) -> list[tuple[str, int, float | None]]:
    """D3: Return student transcript: list of (title, credits, grade), ordered by course title."""
    cur = con.execute(
        """
        SELECT c.title, c.credits, e.grade
        FROM enrollments e
        JOIN courses c ON c.code = e.course_code
        WHERE e.student_id = ?
        ORDER BY c.title
        """,
        (student_id,),
    )
    return cur.fetchall()
