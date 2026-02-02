#!/usr/bin/env python3
"""
Web server for the promotion dashboard
Serves the HTML interface and provides API endpoints for interactions
"""

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "promotion_agent.db"


@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return send_file('dashboard.html')


@app.route('/review_dashboard.json')
def dashboard_json():
    """Serve the dashboard JSON data"""
    try:
        return send_file('review_dashboard.json')
    except FileNotFoundError:
        return jsonify({
            "generated_at": datetime.now().isoformat(),
            "pending_promotions": [],
            "commenting_suggestions": {},
            "weekly_tasks": []
        })


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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count posts
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]
    
    # Count promotions by status
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM promotions 
        GROUP BY status
    """)
    promo_stats = dict(cursor.fetchall())
    
    # Recent activity
    cursor.execute("""
        SELECT activity_type, COUNT(*)
        FROM activity_log
        WHERE completed_date >= datetime('now', '-7 days')
        GROUP BY activity_type
    """)
    recent_activity = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        "total_posts": total_posts,
        "promotions": promo_stats,
        "recent_activity": recent_activity
    })


if __name__ == '__main__':
    print("=== Promotion Dashboard Server ===")
    print("Dashboard available at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
