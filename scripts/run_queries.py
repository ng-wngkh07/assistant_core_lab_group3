#!/usr/bin/env python3
"""Execute SQL queries in sql/my_queries.sql and print results."""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path


def run_queries(db_path: str | Path, sql_path: str | Path | None = None) -> None:
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Database file not found: {db_file}", file=sys.stderr)
        sys.exit(1)

    if sql_path is None:
        sql_file = Path(__file__).resolve().parent.parent / "sql" / "my_queries.sql"
    else:
        sql_file = Path(sql_path)

    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Running queries from '{sql_file.name}' against '{db_file.name}'...\n")

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    content = sql_file.read_text(encoding="utf-8")

    # Split into sections by F1, F2, F3, H2 comments
    pattern = re.compile(r"(--\s*(?:F\d+|H\d+)[^\n]*\n(?:--[^\n]*\n)*)(SELECT[\s\S]*?;)", re.IGNORECASE)
    matches = pattern.findall(content)

    if not matches:
        # Fallback: execute statements ending with semicolon
        statements = [s.strip() for s in content.split(";") if s.strip()]
        matches = [(f"-- Query {i+1}", s + ";") for i, s in enumerate(statements)]

    for header, sql in matches:
        title_line = header.strip().split("\n")[0].replace("--", "").strip()
        print("=" * 60)
        print(f"Query: {title_line}")
        print("SQL:")
        print(sql.strip())
        print("-" * 60)
        try:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()

            # Format as simple table
            if columns:
                col_widths = [max(len(col), max((len(str(row[i])) for row in rows), default=0)) for i, col in enumerate(columns)]
                header_str = " | ".join(col.ljust(w) for col, w in zip(columns, col_widths))
                separator_str = "-+-".join("-" * w for w in col_widths)
                print(header_str)
                print(separator_str)
                for row in rows:
                    row_str = " | ".join(str(val if val is not None else "NULL").ljust(w) for val, w in zip(row, col_widths))
                    print(row_str)
            else:
                print("(No result set)")
            print(f"Total rows: {len(rows)}\n")
        except sqlite3.Error as e:
            print(f"Error executing query: {e}\n", file=sys.stderr)

    con.close()


def main() -> None:
    db_path = sys.argv[1] if len(sys.argv) > 1 else "assistant.db"
    sql_path = sys.argv[2] if len(sys.argv) > 2 else None
    run_queries(db_path, sql_path)


if __name__ == "__main__":
    main()
