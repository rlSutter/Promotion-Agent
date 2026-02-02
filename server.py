#!/usr/bin/env python3
"""
Web server for the promotion dashboard
Serves the HTML interface and provides API endpoints for interactions
"""

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

# Run from script directory so relative paths (dashboard.html, DB) always work
_script_dir = Path(__file__).resolve().parent
os.chdir(_script_dir)

# One-time: create .env from .env.example if missing (so users don't run Copy-Item manually)
_env_dir = _script_dir
_env_path = _env_dir / ".env"
_env_example = _env_dir / ".env.example"
if not _env_path.exists() and _env_example.exists():
    shutil.copy(_env_example, _env_path)
    print("Created .env from .env.example. Edit .env with your SUBSTACK_URL and ANTHROPIC_API_KEY, then restart.")
load_dotenv()

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = os.getenv("PROMOTION_AGENT_DB") or str(_script_dir / "promotion_agent.db")


DASHBOARD_HTML_PATH = _script_dir / "dashboard.html"

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    try:
        return send_file(str(DASHBOARD_HTML_PATH), mimetype="text/html")
    except (FileNotFoundError, PermissionError) as e:
        return (
            f"<h1>Dashboard unavailable</h1><p>Could not read dashboard.html: {e}</p>"
            "<p>Check file permissions or OneDrive sync (try &quot;Always keep on this device&quot; for this folder).</p>",
            503,
            {"Content-Type": "text/html"},
        )


REVIEW_DASHBOARD_PATH = _script_dir / "review_dashboard.json"

def _empty_dashboard():
    return jsonify({
        "generated_at": datetime.now().isoformat(),
        "pending_promotions": [],
        "commenting_suggestions": {},
        "weekly_tasks": []
    })

@app.route('/review_dashboard.json')
def dashboard_json():
    """Serve the dashboard JSON data"""
    try:
        return send_file(str(REVIEW_DASHBOARD_PATH), mimetype="application/json")
    except (FileNotFoundError, PermissionError) as e:
        # PermissionError can occur on Windows/OneDrive when file is locked or cloud-only
        if isinstance(e, PermissionError):
            print(f"Warning: Could not read {REVIEW_DASHBOARD_PATH} ({e}). Serving empty dashboard.", flush=True)
        return _empty_dashboard()


@app.route('/api/mark-published/<int:promotion_id>', methods=['POST'])
def mark_published(promotion_id):
    """Mark a promotion as published"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE promotions
        SET status = 'published', published_date = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), promotion_id))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "promotion_id": promotion_id})


@app.route('/api/skip-promotion/<int:promotion_id>', methods=['POST'])
def skip_promotion(promotion_id):
    """Mark a promotion as skipped"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE promotions
        SET status = 'skipped'
        WHERE id = ?
    """, (promotion_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "promotion_id": promotion_id})


@app.route('/api/complete-task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark a weekly task as complete"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE weekly_tasks
        SET status = 'completed'
        WHERE id = ?
    """, (task_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "task_id": task_id})


@app.route('/api/update-promotion/<int:promotion_id>', methods=['POST'])
def update_promotion(promotion_id):
    """Update the promotional post text after editing"""
    data = request.get_json()
    new_text = data.get('promotional_post')
    
    if not new_text:
        return jsonify({"error": "No text provided"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE promotions
        SET promotional_post = ?
        WHERE id = ?
    """, (new_text, promotion_id))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "promotion_id": promotion_id})


@app.route('/api/stats')
def stats():
    """Get statistics about the agent's activity"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e), "total_posts": 0, "promotions": {}, "recent_activity": {}}), 500

    try:
        # Count posts (table may not exist if agent hasn't run yet)
        try:
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            total_posts = 0

        # Count promotions by status
        try:
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM promotions
                GROUP BY status
            """)
            promo_stats = dict(cursor.fetchall())
        except sqlite3.OperationalError:
            promo_stats = {}

        # Recent activity
        try:
            cursor.execute("""
                SELECT activity_type, COUNT(*)
                FROM activity_log
                WHERE completed_date >= datetime('now', '-7 days')
                GROUP BY activity_type
            """)
            recent_activity = dict(cursor.fetchall())
        except sqlite3.OperationalError:
            recent_activity = {}
    finally:
        conn.close()

    return jsonify({
        "total_posts": total_posts,
        "promotions": promo_stats,
        "recent_activity": recent_activity
    })


if __name__ == '__main__':
    print("=== Promotion Dashboard Server ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"DB path: {DB_PATH}")
    print("Dashboard: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
