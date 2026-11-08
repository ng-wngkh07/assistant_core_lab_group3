#!/usr/bin/env python3
"""Run SQL migrations against SQLite database."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def run_migrations(db_path: str | Path) -> None:
    db_file = Path(db_path)
    migrations_dir = Path(__file__).resolve().parent.parent / "sql" / "migrations"

    if not migrations_dir.is_dir():
        print(f"Migrations directory not found: {migrations_dir}", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # Track applied migrations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    con.commit()

    cur.execute("SELECT name FROM _migrations")
    applied = {row[0] for row in cur.fetchall()}

    migration_files = sorted(migrations_dir.glob("*.sql"))
    for mf in migration_files:
        if mf.name not in applied:
            print(f"apply {mf.name}")
            with open(mf, encoding="utf-8") as f:
                sql_content = f.read()
            cur.executescript(sql_content)
            cur.execute("INSERT INTO _migrations (name) VALUES (?)", (mf.name,))
            con.commit()

    con.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate.py <db_path>")
        sys.exit(1)
    run_migrations(sys.argv[1])


if __name__ == "__main__":
    main()
