#!/usr/bin/env python3
"""
Interactive SQL shell for promotion_agent.db.
Use this when sqlite3 CLI is not installed (e.g. on Windows).

Run: python db_shell.py
Then type SQL (e.g. SELECT * FROM posts LIMIT 5;) and press Enter.
Type .quit or .exit to exit.
"""
import sqlite3
import sys
import os
from pathlib import Path

# Prefer same directory as this script; fall back to current working directory
_script_dir = Path(__file__).resolve().parent
DB_PATH = _script_dir / "promotion_agent.db"
if not DB_PATH.exists():
    DB_PATH = Path(os.getcwd()) / "promotion_agent.db"
db_str = str(DB_PATH.resolve())

def main():
    if not DB_PATH.exists():
        print(f"Database not found: {db_str}", file=sys.stderr)
        print("Run the agent first (e.g. docker-compose up or python agent.py) to create it.", file=sys.stderr)
        sys.exit(1)
    try:
        conn = sqlite3.connect(db_str)
    except sqlite3.OperationalError:
        # Fallback for Windows/OneDrive: use file URI with forward slashes
        uri = "file:///" + Path(db_str).resolve().as_posix().replace("\\", "/") + "?mode=rw"
        conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    print(f"Connected to {DB_PATH}")
    print("Type SQL and press Enter. .quit or .exit to exit.\n")

    buffer = []
    while True:
        try:
            line = input("sqlite> " if not buffer else "   ...> ")
        except EOFError:
            break
        line = line.strip()
        if not line:
            continue
        if line.lower() in (".quit", ".exit", "quit", "exit"):
            break
        if line.lower() == ".tables":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            print(" ".join(r[0] for r in cur.fetchall()))
            continue
        if line.startswith("."):
            print("Unknown command. Use .quit to exit.")
            continue
        buffer.append(line)
        stmt = " ".join(buffer)
        if stmt.endswith(";"):
            buffer.clear()
            try:
                cur.execute(stmt)
                conn.commit()
                rows = cur.fetchall()
                if rows:
                    for row in rows:
                        print(dict(row))
                elif cur.description:
                    print("(0 rows)")
                else:
                    print("Done.")
            except sqlite3.Error as e:
                print(f"Error: {e}")
        else:
            print("(statement continues; end with ;)")

    conn.close()
    print("Bye.")

if __name__ == "__main__":
    main()
