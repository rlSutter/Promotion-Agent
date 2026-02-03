#!/usr/bin/env python3
"""
Create promotion_agent.db and tables only (no Anthropic, no feed).
Run this if agent.py fails before creating the database (e.g. missing API key).

  python create_db.py
"""
import os
import sqlite3
import shutil
from pathlib import Path
from urllib.request import pathname2url

_script_dir = Path(__file__).resolve().parent
db_path = str(_script_dir / "promotion_agent.db")

def _uri_for_path(path_str):
    """File URI for Windows/OneDrive (handles spaces and drive letters)."""
    # pathname2url expects a str; returns e.g. /C:/Users/... on Windows
    resolved = str(Path(path_str).resolve())
    return "file://" + pathname2url(resolved) + "?mode=rwc"

def _try_connect(path_str, use_uri=False):
    """Try to open DB at path; return (conn, None) on success or (None, error) on failure."""
    try:
        if use_uri:
            uri = _uri_for_path(path_str)
            return (sqlite3.connect(uri, uri=True), None)
        return (sqlite3.connect(path_str), None)
    except sqlite3.OperationalError as e:
        return (None, e)

def main():
    print(f"Target: {db_path}")
    conn = None
    used_path = None

    # 1) Direct path
    conn, err = _try_connect(db_path)
    if conn:
        used_path = db_path
    else:
        # 2) URI (handles spaces in path)
        conn, err2 = _try_connect(db_path, use_uri=True)
        if conn:
            used_path = db_path
        else:
            # 3) Fallbacks: try several writable locations (often not on OneDrive)
            home = Path.home()
            fallback_dirs = [
                os.environ.get("TEMP"),
                os.environ.get("TMP"),
                str(home),
                str(home / "AppData" / "Local" / "Temp"),
            ]
            for d in fallback_dirs:
                if not d or not Path(d).exists():
                    continue
                d = Path(d)
                candidate = d / "promotion_agent.db"
                print(f"Trying: {candidate}")
                conn, _ = _try_connect(str(candidate))
                if conn:
                    used_path = str(candidate)
                    break
            if not conn:
                print("Error (direct):", err)
                print("Error (URI):", err2)
                print("Error (fallbacks): All locations failed.")
                print("Try: (1) Right-click project folder → 'Always keep on this device' (OneDrive)")
                print("     (2) Run PowerShell as Administrator and run create_db.py again")
                print("     (3) Move project to C:\\Programming\\Promotion Agent (outside OneDrive)")
                return 1

    if used_path != db_path:
        print(f"Created in: {used_path}")
        conn.close()
        conn = None
        try:
            shutil.copy(used_path, db_path)
            conn = sqlite3.connect(db_path)
            print("Copied to project folder.")
        except (OSError, PermissionError) as e:
            conn = sqlite3.connect(used_path)
            print("Could not copy to project folder:", e)
            print("Using database at:", used_path)
        except sqlite3.OperationalError:
            # Copy may have succeeded but opening in project folder fails (OneDrive)
            try:
                conn = sqlite3.connect(used_path)
            except sqlite3.OperationalError as e:
                print("Could not re-open database:", e)
                return 1
            print("Project folder not openable (OneDrive?). Using database at:")
            print(" ", used_path)
            print("To use this DB with the agent, add to .env:")
            print("  PROMOTION_AGENT_DB=" + used_path.replace("\\", "/"))
            print("Or copy that file into the project folder when OneDrive allows.")

    if conn is None:
        print("Error: No database connection.")
        return 1
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS posts (id TEXT PRIMARY KEY, title TEXT, url TEXT, content TEXT, published_date TEXT, discovered_date TEXT, status TEXT DEFAULT 'new')")
    cur.execute("""CREATE TABLE IF NOT EXISTS promotions (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id TEXT, platform TEXT, outward_sentence TEXT, promotional_post TEXT, status TEXT DEFAULT 'pending_review', created_date TEXT, published_date TEXT, FOREIGN KEY (post_id) REFERENCES posts(id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS weekly_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT, content TEXT, due_date TEXT, status TEXT DEFAULT 'pending', created_date TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id TEXT, activity_type TEXT, details TEXT, completed_date TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS analytics_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        promotion_id INTEGER,
        task_id INTEGER,
        post_id TEXT,
        platform TEXT,
        extra TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (promotion_id) REFERENCES promotions(id),
        FOREIGN KEY (task_id) REFERENCES weekly_tasks(id)
    )""")
    conn.commit()
    conn.close()
    print("Database created successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
