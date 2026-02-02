#!/usr/bin/env python3
"""
Autonomous Blog Promotion Agent
Monitors Substack RSS, extracts promotional sentences, routes to platforms,
and provides a review/release dashboard.
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import anthropic
import feedparser
import schedule
import time
from typing import Dict, List, Optional, Tuple

# Configuration
CONFIG = {
    "substack_url": os.getenv("SUBSTACK_URL", "https://yoursubstack.substack.com/feed"),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    "db_path": "promotion_agent.db",
    "review_dashboard_path": "review_dashboard.json",
    "check_interval_minutes": 60,
}

# Platform routing rules based on keywords/topics
PLATFORM_ROUTING = {
    "linkedin": [
        "leadership", "technical leadership", "management", "bias", "execution",
        "power", "workplace", "career", "engineering management", "tech leadership"
    ],
    "substack_notes": [
        "psychological safety", "technical debt", "framework", "mental model",
        "cognitive", "thinking", "ideas", "concepts", "patterns"
    ],
    "bluesky": [
        "bike-shedding", "law of triviality", "cognitive bias", "thinking",
        "playful", "brain", "psychology", "curiosity"
    ],
}


class PromotionAgent:
    def __init__(self):
        self.db_path = CONFIG["db_path"]
        self.anthropic_client = anthropic.Anthropic(
            api_key=CONFIG["anthropic_api_key"]
        )
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for tracking posts and promotions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                content TEXT,
                published_date TEXT,
                discovered_date TEXT,
                status TEXT DEFAULT 'new'
            )
        """)
        
        # Promotions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                platform TEXT,
                outward_sentence TEXT,
                promotional_post TEXT,
                status TEXT DEFAULT 'pending_review',
                created_date TEXT,
                published_date TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        """)
        
        # Weekly tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                content TEXT,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                created_date TEXT
            )
        """)
        
        # Activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                activity_type TEXT,
                details TEXT,
                completed_date TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def check_for_new_posts(self):
        """Monitor Substack RSS feed for new posts"""
        print(f"[{datetime.now()}] Checking for new posts...")
        
        feed = feedparser.parse(CONFIG["substack_url"])
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_posts = []
        for entry in feed.entries:
            post_id = hashlib.md5(entry.link.encode()).hexdigest()
            
            # Check if we've seen this post
            cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
            if cursor.fetchone():
                continue
            
            # New post found
            post_data = {
                "id": post_id,
                "title": entry.title,
                "url": entry.link,
                "content": entry.get("summary", ""),
                "published_date": entry.get("published", ""),
                "discovered_date": datetime.now().isoformat(),
            }
            
            cursor.execute("""
                INSERT INTO posts (id, title, url, content, published_date, discovered_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (post_id, post_data["title"], post_data["url"], 
                  post_data["content"], post_data["published_date"], 
                  post_data["discovered_date"]))
            
            new_posts.append(post_data)
            print(f"  → New post detected: {entry.title}")
        
        conn.commit()
        conn.close()
        
        # Process each new post
        for post in new_posts:
            self.process_new_post(post)
    
    def extract_outward_sentence(self, title: str, content: str) -> str:
        """Use Claude to extract the best outward sentence from the post"""
        
        prompt = f"""You are helping extract the perfect "outward sentence" from a blog post for promotion.

Blog Title: {title}

Blog Content (excerpt):
{content[:3000]}

Your task: Extract ONE sentence (or at most two) that:
1. Can stand alone without context
2. Sounds true even to someone who hasn't read the post yet
3. Has one of these shapes:
   - "If X, then Y (and that's why execution breaks)."
   - "People call it Z, but it's actually W."
   - "This isn't about A; it's about B."

The sentence should be the "spine" of the post, not a teaser. It should make a complete claim.

Return ONLY the sentence(s), nothing else."""

        message = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
    
    def determine_platform(self, title: str, content: str) -> str:
        """Determine the best platform based on content"""
        
        text = (title + " " + content).lower()
        
        scores = {}
        for platform, keywords in PLATFORM_ROUTING.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            scores[platform] = score
        
        # Return platform with highest score, default to substack_notes
        if max(scores.values()) == 0:
            return "substack_notes"
        
        return max(scores, key=scores.get)
    
    def generate_promotional_post(self, title: str, content: str, 
                                   outward_sentence: str, platform: str, url: str) -> str:
        """Generate the promotional post for the chosen platform"""
        
        platform_guidelines = {
            "linkedin": "Professional, outcomes-focused. 2-3 sentences. LinkedIn tone.",
            "substack_notes": "Thoughtful, complete idea. 2-3 sentences. Can be slightly more casual.",
            "bluesky": "Playful, gift-like. Short and punchy. Conversational.",
        }
        
        prompt = f"""You are drafting a promotional post for a blog article.

Platform: {platform}
Platform style: {platform_guidelines.get(platform, "Clear and conversational")}

Article title: {title}
Outward sentence (the core claim): {outward_sentence}

Article excerpt:
{content[:2000]}

Create a promotional post following this structure:
1. The claim (the outward sentence)
2. A second sentence that makes it practical (the execution consequence)
3. Optional: a third sentence that invites reflection
4. Link at the end with a low-key transition like "I wrote the longer version here:"

Important constraints:
- NO teasing or "here's a snippet" language
- Make it a complete thought that stands alone
- Keep it platform-native in length and tone
- No cringe, no hype, no "you won't believe"
- Sound like a human sharing an idea, not marketing

Return ONLY the promotional post text, including the link at the end ({url})."""

        message = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
    
    def process_new_post(self, post: Dict):
        """Process a new post: extract sentence, route platform, generate promo"""
        
        print(f"\n[Processing] {post['title']}")
        
        # Step 1: Extract outward sentence
        print("  → Extracting outward sentence...")
        outward_sentence = self.extract_outward_sentence(post["title"], post["content"])
        print(f"     '{outward_sentence}'")
        
        # Step 2: Determine platform
        platform = self.determine_platform(post["title"], post["content"])
        print(f"  → Routed to: {platform}")
        
        # Step 3: Generate promotional post
        print("  → Generating promotional post...")
        promo_post = self.generate_promotional_post(
            post["title"], post["content"], outward_sentence, platform, post["url"]
        )
        
        # Step 4: Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO promotions (post_id, platform, outward_sentence, promotional_post, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (post["id"], platform, outward_sentence, promo_post, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        print("  → Saved to review dashboard")
        
        # Generate ecosystem commenting suggestions
        self.generate_commenting_tasks(post["id"], post["title"], platform)
    
    def generate_commenting_tasks(self, post_id: str, title: str, platform: str):
        """Generate suggestions for ecosystem commenting"""
        
        prompt = f"""You are helping identify where to leave thoughtful comments for blog promotion.

Blog post title: {title}
Target platform: {platform}

Suggest 2-3 specific types of posts or topics (not specific URLs, but types of content) where a thoughtful comment would:
1. Be genuinely relevant and add value
2. Help the author become a familiar name in the right communities
3. Feel natural, not spammy

For each suggestion, provide:
- Topic/type of post to look for
- What angle or nuance to contribute in a comment

Return as a brief numbered list."""

        message = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        
        suggestions = message.content[0].text.strip()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (post_id, activity_type, details, completed_date)
            VALUES (?, ?, ?, ?)
        """, (post_id, "commenting_suggestions", suggestions, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def generate_review_dashboard(self):
        """Generate JSON file with pending promotions for review"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pending promotions
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
        
        # Get commenting suggestions
        cursor.execute("""
            SELECT post_id, details
            FROM activity_log
            WHERE activity_type = 'commenting_suggestions'
            AND post_id IN (SELECT post_id FROM promotions WHERE status = 'pending_review')
        """)
        
        commenting_tasks = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get weekly tasks
        cursor.execute("""
            SELECT id, task_type, content, due_date, created_date
            FROM weekly_tasks
            WHERE status = 'pending'
            ORDER BY due_date
        """)
        
        weekly_tasks = []
        for row in cursor.fetchall():
            weekly_tasks.append({
                "task_id": row[0],
                "task_type": row[1],
                "content": row[2],
                "due_date": row[3],
                "created_date": row[4],
            })
        
        conn.close()
        
        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "pending_promotions": pending,
            "commenting_suggestions": commenting_tasks,
            "weekly_tasks": weekly_tasks,
        }
        
        with open(CONFIG["review_dashboard_path"], "w") as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"\n[Dashboard] Generated with {len(pending)} pending promotions")
        
        return dashboard
    
    def mark_promotion_published(self, promotion_id: int):
        """Mark a promotion as published (called via API or manually)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE promotions
            SET status = 'published', published_date = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), promotion_id))
        conn.commit()
        conn.close()
    
    def generate_weekly_onramp_post(self):
        """Generate the weekly 'start here' routing post"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent published posts
        cursor.execute("""
            SELECT title, url, content
            FROM posts
            WHERE status != 'archived'
            ORDER BY published_date DESC
            LIMIT 10
        """)
        
        posts = cursor.fetchall()
        conn.close()
        
        if len(posts) < 3:
            print("[Weekly task] Not enough posts yet for on-ramp")
            return
        
        posts_text = "\n".join([f"- {p[0]}: {p[1]}" for p in posts])
        
        prompt = f"""You are creating a weekly "on-ramp" post to help new readers discover the best starting points.

Recent posts:
{posts_text}

Select 3 posts that work as an on-ramp:
1. One "frame" post (backbone, core mental model)
2. One "situational" post (addresses a current pain point)
3. One "bridge" post (widens the audience)

Then write a short post (Substack Note or platform post) with:
- Brief intro: "If you're new here, start with:"
- The 3 posts with one-line descriptions
- Keep it helpful, not salesy

Return the complete post text with links."""

        message = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        onramp_content = message.content[0].text.strip()
        
        # Save as weekly task
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weekly_tasks (task_type, content, due_date, created_date)
            VALUES (?, ?, ?, ?)
        """, ("onramp_post", onramp_content, 
              (datetime.now() + timedelta(days=7)).isoformat(),
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        print("[Weekly task] On-ramp post generated")
    
    def run(self):
        """Main agent loop"""
        print("=== Promotion Agent Started ===")
        print(f"Monitoring: {CONFIG['substack_url']}")
        print(f"Check interval: {CONFIG['check_interval_minutes']} minutes")
        
        # Schedule tasks
        schedule.every(CONFIG["check_interval_minutes"]).minutes.do(self.check_for_new_posts)
        schedule.every().hour.do(self.generate_review_dashboard)
        schedule.every().monday.at("09:00").do(self.generate_weekly_onramp_post)
        
        # Initial check
        self.check_for_new_posts()
        self.generate_review_dashboard()
        
        # Run forever
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    agent = PromotionAgent()
    agent.run()
