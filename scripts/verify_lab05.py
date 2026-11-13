#!/usr/bin/env python3
"""End-to-end verification script for Lab 5 (Parts A–F).

Runs all quality checks and tests for Member 4 deliverable:
- Practice SQL Q1–Q15 (check.py)
- Practice Python D1–D3 (pytest practice/test_school_repo.py)
- Migration & Seeding pipeline (migrate.py & seed.py)
- Part F Analytical Queries (sql/my_queries.sql)
- Full Assistant API, Database, Persistence & Statistics test suite (pytest tests/)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_step(title: str, cmd: list[str], cwd: Path) -> bool:
    print("\n==================================================")
    print(f"-> {title}")
    print(f"   Command: {' '.join(cmd)} (in {cwd.name})")
    print("==================================================")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode == 0:
        print(f"[OK] {title} passed successfully.")
        return True
    else:
        print(f"[FAIL] {title} failed with exit code {result.returncode}.", file=sys.stderr)
        return False


def main():
    practice_dir = ROOT_DIR / "practice"
    app_dir = ROOT_DIR

    all_passed = True

    # 1. Check Practice SQL Q1–Q15
    if not run_step("Practice SQL (Q1–Q15)", [sys.executable, "check.py"], practice_dir):
        all_passed = False

    # 2. Check Practice Python D1–D3
    cmd_d = [sys.executable, "-m", "pytest", "-q", "test_school_repo.py"]
    if not run_step("Practice Python Repo D1–D3", cmd_d, practice_dir):
        all_passed = False

    # 3. Migrations
    test_db = ROOT_DIR / "assistant_verify.db"
    if test_db.exists():
        test_db.unlink()
    if not run_step("Database Migrations", [sys.executable, "scripts/migrate.py", str(test_db)], ROOT_DIR):
        all_passed = False

    # 4. Seeding
    cmd_seed = [sys.executable, "scripts/seed.py", str(test_db), "300"]
    if not run_step("Data Seeding (300 interactions)", cmd_seed, ROOT_DIR):
        all_passed = False

    # Clean up verify db
    if test_db.exists():
        test_db.unlink()

    # 5. Full Assistant Test Suite (51 tests: API, DB, Persistence, Stats)
    cmd_pytest = [sys.executable, "-m", "pytest", "-v"]
    if not run_step("Assistant Core & Database Test Suite (Parts E–F)", cmd_pytest, app_dir):
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("ALL LAB 5 VERIFICATIONS PASSED (100% GREEN)!")
    else:
        print("SOME VERIFICATION STEPS FAILED. Check output above.", file=sys.stderr)
    print("=" * 50)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
