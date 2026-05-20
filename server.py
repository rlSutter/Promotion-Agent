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

from flask import Flask, jsonify, send_file, request, Response
import hmac
import json
import sqlite3
import threading
from datetime import datetime

app = Flask(__name__)

_DASHBOARD_USER = os.getenv("DASHBOARD_USERNAME", "")
_DASHBOARD_PASS = os.getenv("DASHBOARD_PASSWORD", "")
_AUTH_ENABLED = bool(_DASHBOARD_USER or _DASHBOARD_PASS)

def _check_auth(username: str, password: str) -> bool:
    user_ok = hmac.compare_digest(username.encode(), _DASHBOARD_USER.encode())
    pass_ok = hmac.compare_digest(password.encode(), _DASHBOARD_PASS.encode())
    return user_ok and pass_ok

@app.before_request
def _require_auth():
    if not _AUTH_ENABLED:
        return
    auth = request.authorization
    if not auth or not _check_auth(auth.username, auth.password):
        return Response(
            "Authentication required.",
            401,
            {"WWW-Authenticate": 'Basic realm="Promotion Dashboard"'},
        )

DB_PATH = os.getenv("PROMOTION_AGENT_DB") or str(_script_dir / "promotion_agent.db")
# Dashboard JSON lives next to the DB (so when DB is in temp, dashboard is writable too)
REVIEW_DASHBOARD_PATH = Path(DB_PATH).parent / "review_dashboard.json"

def _regenerate_dashboard_json():
    """Regenerate review_dashboard.json from DB so UI refresh shows updated list."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.post_id, posts.title, posts.url, p.platform,
                   p.outward_sentence, p.promotional_post, p.created_date
            FROM promotions p
            JOIN posts ON p.post_id = posts.id
            WHERE p.status = 'pending_review'
            ORDER BY p.created_date DESC
        """)
        pending = []
        for row in cursor.fetchall():
            pending.append({
                "promotion_id": row[0],
                "post_id": row[1],
                "post_title": row[2],
                "post_url": row[3],
                "platform": row[4],
                "outward_sentence": row[5],
                "promotional_post": row[6],
                "created_date": row[7],
            })
        cursor.execute("""
            SELECT post_id, details FROM activity_log
            WHERE activity_type = 'commenting_suggestions'
            AND post_id IN (SELECT post_id FROM promotions WHERE status = 'pending_review')
        """)
        commenting_tasks = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT id, task_type, content, due_date, created_date
            FROM weekly_tasks WHERE status = 'pending' ORDER BY due_date
        """)
        weekly_tasks = [
            {"task_id": r[0], "task_type": r[1], "content": r[2], "due_date": r[3], "created_date": r[4]}
            for r in cursor.fetchall()
        ]
        # Archived: skipped or published (not in working list, can be recovered)
        cursor.execute("""
            SELECT p.id, p.post_id, posts.title, posts.url, p.platform,
                   p.outward_sentence, p.promotional_post, p.created_date, p.status, p.published_date
            FROM promotions p
            JOIN posts ON p.post_id = posts.id
            WHERE p.status IN ('skipped', 'published')
            ORDER BY COALESCE(p.published_date, p.created_date) DESC
        """)
        archived = []
        for row in cursor.fetchall():
            archived.append({
                "promotion_id": row[0],
                "post_id": row[1],
                "post_title": row[2],
                "post_url": row[3],
                "platform": row[4],
                "outward_sentence": row[5],
                "promotional_post": row[6],
                "created_date": row[7],
                "status": row[8],
                "published_date": row[9],
            })
        conn.close()
        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "pending_promotions": pending,
            "commenting_suggestions": commenting_tasks,
            "weekly_tasks": weekly_tasks,
            "archived_promotions": archived,
        }
        with open(REVIEW_DASHBOARD_PATH, "w") as f:
            json.dump(dashboard, f, indent=2)
    except (sqlite3.OperationalError, OSError):
        pass

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
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE promotions
            SET status = 'published', published_date = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), promotion_id))
        conn.commit()
        conn.close()
        _regenerate_dashboard_json()
        return jsonify({"status": "success", "promotion_id": promotion_id})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/api/skip-promotion/<int:promotion_id>', methods=['POST'])
def skip_promotion(promotion_id):
    """Mark a promotion as skipped"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE promotions
            SET status = 'skipped'
            WHERE id = ?
        """, (promotion_id,))
        conn.commit()
        conn.close()
        _regenerate_dashboard_json()
        return jsonify({"status": "success", "promotion_id": promotion_id})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/api/analytics/track', methods=['POST'])
def analytics_track():
    """Record an analytics event (click, engagement)."""
    try:
        data = request.get_json() or {}
        event_type = (data.get("event_type") or "").strip()
        if not event_type:
            return jsonify({"error": "event_type required", "status": "error"}), 400
        promotion_id = data.get("promotion_id")
        task_id = data.get("task_id")
        post_id = data.get("post_id")
        platform = data.get("platform")
        extra = data.get("extra")
        if extra is not None and not isinstance(extra, str):
            extra = json.dumps(extra) if extra else None
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_events (event_type, promotion_id, task_id, post_id, platform, extra)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_type, promotion_id, task_id, post_id, platform, extra))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return jsonify({"status": "success", "event_id": event_id})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route('/api/recover-promotion/<int:promotion_id>', methods=['POST'])
def recover_promotion(promotion_id):
    """Move a promotion from archive back to pending (recover to working list)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE promotions
            SET status = 'pending_review', published_date = NULL
            WHERE id = ?
        """, (promotion_id,))
        conn.commit()
        conn.close()
        _regenerate_dashboard_json()
        return jsonify({"status": "success", "promotion_id": promotion_id})
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e), "status": "error"}), 500


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
        hint = " Set PROMOTION_AGENT_DB in .env to your DB path (e.g. C:/Users/You/AppData/Local/Temp/promotion_agent.db) if the DB is in temp or another folder."
        return jsonify({
            "error": str(e),
            "hint": hint.strip(),
            "db_path": DB_PATH,
            "total_posts": 0,
            "promotions": {},
            "recent_activity": {}
        }), 500

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

        # Analytics: event counts (last 7 and 30 days)
        try:
            cursor.execute("""
                SELECT event_type, COUNT(*)
                FROM analytics_events
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY event_type
            """)
            analytics_7d = dict(cursor.fetchall())
        except sqlite3.OperationalError:
            analytics_7d = {}
        try:
            cursor.execute("""
                SELECT event_type, COUNT(*)
                FROM analytics_events
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY event_type
            """)
            analytics_30d = dict(cursor.fetchall())
        except sqlite3.OperationalError:
            analytics_30d = {}

        # Substack Developer API profile (latest fetch)
        substack_profile = None
        try:
            cursor.execute("""
                SELECT fetched_at, identity_handle, profile_url, follower_count,
                       rough_num_free_subscribers, bestseller_tier, leaderboard_rank,
                       leaderboard_publication_name, leaderboard_label, leaderboard_ranking
                FROM substack_profile
                ORDER BY fetched_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                substack_profile = {
                    "fetched_at": row[0],
                    "identity_handle": row[1],
                    "profile_url": row[2],
                    "follower_count": row[3],
                    "rough_num_free_subscribers": row[4],
                    "bestseller_tier": row[5],
                    "leaderboard_rank": row[6],
                    "leaderboard_publication_name": row[7],
                    "leaderboard_label": row[8],
                    "leaderboard_ranking": row[9],
                }
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()

    return jsonify({
        "total_posts": total_posts,
        "promotions": promo_stats,
        "recent_activity": recent_activity,
        "analytics": {
            "last_7_days": analytics_7d,
            "last_30_days": analytics_30d,
        },
        "substack_profile": substack_profile,
    })


_inventory_build_state = {"running": False, "last_run": None, "count": 0, "error": None}
_inventory_build_lock = threading.Lock()


def _run_inventory_build_thread():
    global _inventory_build_state
    with _inventory_build_lock:
        _inventory_build_state["running"] = True
        _inventory_build_state["error"] = None
    try:
        from agent import PromotionAgent
        agent = PromotionAgent()
        agent.build_article_inventory()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM article_inventory")
        count = c.fetchone()[0]
        conn.close()
        with _inventory_build_lock:
            _inventory_build_state["running"] = False
            _inventory_build_state["last_run"] = datetime.now().isoformat()
            _inventory_build_state["count"] = count
    except Exception as e:
        with _inventory_build_lock:
            _inventory_build_state["running"] = False
            _inventory_build_state["error"] = str(e)
        print(f"[Inventory] Build failed: {e}", flush=True)


@app.route('/api/inventory')
def get_inventory():
    """Return all article inventory items as JSON."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, subtitle, url, published_date, topics, core_mechanism, added_date
            FROM article_inventory
            ORDER BY published_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        items = [
            {
                "id": r[0], "title": r[1], "subtitle": r[2], "url": r[3],
                "published_date": r[4], "topics": r[5], "core_mechanism": r[6],
                "added_date": r[7],
            }
            for r in rows
        ]
        return jsonify({"items": items, "count": len(items)})
    except sqlite3.OperationalError as e:
        return jsonify({"items": [], "count": 0, "error": str(e)})


@app.route('/api/inventory/build', methods=['POST'])
def trigger_inventory_build():
    """Start a background inventory build pass (fetches all Substack posts via API)."""
    with _inventory_build_lock:
        if _inventory_build_state["running"]:
            return jsonify({"status": "already_running"})
    t = threading.Thread(target=_run_inventory_build_thread, daemon=True)
    t.start()
    return jsonify({"status": "started"})


@app.route('/api/inventory/status')
def inventory_build_status():
    """Return the current state of the inventory build."""
    with _inventory_build_lock:
        return jsonify(dict(_inventory_build_state))


@app.route('/api/inventory/export', methods=['POST'])
def export_inventory_markdown():
    """Re-export article_inventory.md from current DB state."""
    try:
        from agent import PromotionAgent
        agent = PromotionAgent()
        agent.export_inventory_to_markdown()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    print("=== Promotion Dashboard Server ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"DB path: {DB_PATH}")
    print("Dashboard: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
