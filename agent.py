#!/usr/bin/env python3
"""
Autonomous Blog Promotion Agent
Monitors Substack RSS, extracts promotional sentences, routes to platforms,
and provides a review/release dashboard.
"""

import os
import sys
import io
import shutil
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import anthropic
import feedparser
import schedule
import time
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

# Windows cp1252 stdout breaks on any non-Latin Unicode (post titles, arrows, etc.)
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower().replace('-', '') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths: use script directory so DB and files work from any cwd (Windows/OneDrive)
_script_dir = Path(__file__).resolve().parent

# One-time: create .env from .env.example if missing (so users don't run Copy-Item manually)
_env_path = _script_dir / ".env"
_env_example = _script_dir / ".env.example"
if not _env_path.exists() and _env_example.exists():
    shutil.copy(_env_example, _env_path)
    print("Created .env from .env.example. Edit .env with your SUBSTACK_URL and ANTHROPIC_API_KEY, then restart.")
load_dotenv()

# Configuration
_raw_substack = os.getenv("SUBSTACK_URL", "https://yoursubstack.substack.com/feed")

# Fix common mistake: /publish/home (private dashboard) -> /feed (public RSS)
if "/publish" in _raw_substack or (_raw_substack.rstrip("/").endswith("substack.com") and "/feed" not in _raw_substack):
    from urllib.parse import urlparse
    parsed = urlparse(_raw_substack)
    _raw_substack = f"{parsed.scheme}://{parsed.netloc}/feed"
    print(f"SUBSTACK_URL was a publish/dashboard URL; using RSS feed instead: {_raw_substack}")

_db_path = os.getenv("PROMOTION_AGENT_DB") or str(_script_dir / "promotion_agent.db")
_substack_api_key = (os.getenv("SUBSTACK_API_KEY") or "").strip()
_substack_linkedin = (os.getenv("SUBSTACK_LINKEDIN_HANDLE") or "").strip()
CONFIG = {
    "substack_url": _raw_substack,
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
    "db_path": _db_path,
    "review_dashboard_path": str(Path(_db_path).parent / "review_dashboard.json"),
    "check_interval_minutes": int(os.getenv("CHECK_INTERVAL_MINUTES", "60")),
    "substack_api_key": _substack_api_key if _substack_api_key else None,
    "substack_linkedin_handle": _substack_linkedin if _substack_linkedin else None,
}

# Platform routing rules based on keywords/topics
PLATFORM_ROUTING = {
    "linkedin": [
        "leadership", "technical leadership", "management", "bias", "execution",
        "power", "workplace", "career", "engineering management", "tech leadership"
    ],
    "substack_notes": [
        "psychological safety", "technical debt", "framework", "mental model",
        "cognitive load", "thinking", "ideas", "concepts", "patterns"
    ],
    "bluesky": [
        "bike-shedding", "law of triviality", "cognitive bias",
        "playful", "brain", "psychology", "curiosity"
    ],
}


class PromotionAgent:
    def __init__(self):
        self.db_path = CONFIG["db_path"]
        # Create database and tables first (before Anthropic client), so DB exists even if API key is missing
        self.init_database()
        self.anthropic_client = anthropic.Anthropic(
            api_key=CONFIG["anthropic_api_key"]
        )
    
    def init_database(self):
        """Initialize SQLite database for tracking posts and promotions"""
        try:
            conn = self._db_connect()
        except sqlite3.OperationalError as e:
            # Fallback for Windows/OneDrive: use file URI with forward slashes
            uri = "file:///" + Path(self.db_path).resolve().as_posix().replace("\\", "/") + "?mode=rwc"
            try:
                conn = sqlite3.connect(uri, uri=True)
                self._db_uri = uri
                self._use_db_uri = True
            except sqlite3.OperationalError as e2:
                print(f"[DB] Error: Could not create database at {self.db_path}", flush=True)
                print(f"[DB] First error: {e}", flush=True)
                print(f"[DB] URI fallback error: {e2}", flush=True)
                print("[DB] Try: right-click project folder -> 'Always keep on this device' (OneDrive); check permissions.", flush=True)
                raise
        else:
            self._use_db_uri = False
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

        # Analytics (clicks, engagement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
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
            )
        """)

        # Substack Developer API profile cache (follower count, subscribers, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS substack_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at TEXT NOT NULL,
                identity_handle TEXT,
                profile_url TEXT,
                follower_count INTEGER,
                rough_num_free_subscribers INTEGER,
                bestseller_tier TEXT,
                leaderboard_rank INTEGER,
                leaderboard_publication_name TEXT,
                leaderboard_label TEXT,
                leaderboard_ranking TEXT,
                raw_json TEXT
            )
        """)

        # Article inventory (all published posts with extracted metadata)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_inventory (
                id TEXT PRIMARY KEY,
                title TEXT,
                subtitle TEXT,
                url TEXT,
                published_date TEXT,
                topics TEXT,
                core_mechanism TEXT,
                added_date TEXT
            )
        """)

        conn.commit()
        conn.close()
        print(f"[DB] Database initialized at: {self.db_path}")

    def _db_connect(self):
        """Open DB connection (uses URI fallback on Windows/OneDrive if needed)."""
        if getattr(self, "_use_db_uri", False):
            return sqlite3.connect(self._db_uri, uri=True)
        return sqlite3.connect(self.db_path)

    def fetch_substack_profile(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Substack profile stats from the Developer API (by LinkedIn handle).
        https://support.substack.com/hc/en-us/articles/45099095296916
        Posts are still retrieved via RSS; this returns profile-level stats only.
        """
        handle = CONFIG.get("substack_linkedin_handle")
        if not handle:
            return None
        url = f"https://substack.com/profile/search/linkedin/{handle.strip()}"
        try:
            req = Request(url, method="GET")
            req.add_header("User-Agent", "PromotionAgent/1.0")
            api_key = CONFIG.get("substack_api_key")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except (HTTPError, URLError, json.JSONDecodeError, OSError) as e:
            print(f"[Substack API] Could not fetch profile: {e}", flush=True)
            return None
        results = data.get("results") or []
        if not results:
            print("[Substack API] No profile found for LinkedIn handle.", flush=True)
            return None
        profile = results[0]
        ls = profile.get("leaderboardStatus") or {}
        fetched_at = datetime.now().isoformat()
        row = {
            "fetched_at": fetched_at,
            "identity_handle": profile.get("identityHandle"),
            "profile_url": profile.get("profileUrl"),
            "follower_count": profile.get("followerCount"),
            "rough_num_free_subscribers": profile.get("roughNumFreeSubscribers"),
            "bestseller_tier": profile.get("bestsellerTier"),
            "leaderboard_rank": ls.get("rank"),
            "leaderboard_publication_name": ls.get("publicationName"),
            "leaderboard_label": ls.get("label"),
            "leaderboard_ranking": ls.get("ranking"),
            "raw_json": json.dumps(profile),
        }
        conn = self._db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO substack_profile (
                fetched_at, identity_handle, profile_url, follower_count,
                rough_num_free_subscribers, bestseller_tier, leaderboard_rank,
                leaderboard_publication_name, leaderboard_label, leaderboard_ranking, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["fetched_at"], row["identity_handle"], row["profile_url"],
            row["follower_count"], row["rough_num_free_subscribers"], row["bestseller_tier"],
            row["leaderboard_rank"], row["leaderboard_publication_name"],
            row["leaderboard_label"], row["leaderboard_ranking"], row["raw_json"],
        ))
        conn.commit()
        conn.close()
        print(f"[Substack API] Profile stored: @{row['identity_handle']} — {row['follower_count'] or 0} followers, {row['rough_num_free_subscribers'] or 0} free subs", flush=True)
        return row

    def check_for_new_posts(self):
        """Monitor Substack RSS feed for new posts"""
        print(f"[{datetime.now()}] Checking for new posts...")
        
        feed = feedparser.parse(CONFIG["substack_url"])
        conn = self._db_connect()
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
            print(f"  -> New post detected: {entry.title}")
        
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
            model=CONFIG["anthropic_model"],
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
            model=CONFIG["anthropic_model"],
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
    
    def process_new_post(self, post: Dict):
        """Process a new post: extract sentence, route platform, generate promo"""
        
        print(f"\n[Processing] {post['title']}")
        
        try:
            self._process_new_post_impl(post)
        except anthropic.BadRequestError as e:
            err_msg = str(e).lower()
            if "credit" in err_msg or "billing" in err_msg or "balance" in err_msg:
                print("\n[ERROR] Anthropic API: Your credit balance is too low.")
                print("  -> Go to https://console.anthropic.com/ -> Plans & Billing")
                print("  -> Add credits or upgrade, then restart the agent.")
            raise
        except anthropic.APIStatusError as e:
            print(f"\n[ERROR] Anthropic API error ({e.status_code}): {e}")
            raise

    def _process_new_post_impl(self, post: Dict):
        """Implementation of process_new_post (called inside try/except for API errors)."""
        # Step 1: Extract outward sentence
        print("  -> Extracting outward sentence...")
        outward_sentence = self.extract_outward_sentence(post["title"], post["content"])
        print(f"     '{outward_sentence}'")

        # Step 2: Determine platform
        platform = self.determine_platform(post["title"], post["content"])
        print(f"  -> Routed to: {platform}")

        # Step 3: Generate promotional post
        print("  -> Generating promotional post...")
        promo_post = self.generate_promotional_post(
            post["title"], post["content"], outward_sentence, platform, post["url"]
        )

        # Step 4: Save to database
        conn = self._db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO promotions (post_id, platform, outward_sentence, promotional_post, created_date)
            VALUES (?, ?, ?, ?, ?)
        """, (post["id"], platform, outward_sentence, promo_post, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        print("  -> Saved to review dashboard")

        # Generate ecosystem commenting suggestions
        self.generate_commenting_tasks(post["id"], post["title"], platform)

        # Add to article inventory
        print("  -> Adding to article inventory...")
        self.add_article_to_inventory(
            post["id"], post["title"], post["url"],
            post["published_date"], "", post["content"]
        )

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
            model=CONFIG["anthropic_model"],
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        
        suggestions = message.content[0].text.strip()
        
        conn = self._db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (post_id, activity_type, details, completed_date)
            VALUES (?, ?, ?, ?)
        """, (post_id, "commenting_suggestions", suggestions, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def generate_review_dashboard(self):
        """Generate JSON file with pending promotions for review"""
        
        conn = self._db_connect()
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
        
        with open(CONFIG["review_dashboard_path"], "w") as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"\n[Dashboard] Generated with {len(pending)} pending promotions")
        
        return dashboard
    
    def mark_promotion_published(self, promotion_id: int):
        """Mark a promotion as published (called via API or manually)"""
        conn = self._db_connect()
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
        
        conn = self._db_connect()
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
            model=CONFIG["anthropic_model"],
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        onramp_content = message.content[0].text.strip()
        
        # Save as weekly task
        conn = self._db_connect()
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
    
    def _get_substack_base_url(self) -> str:
        """Extract scheme+host from the configured Substack URL."""
        from urllib.parse import urlparse
        parsed = urlparse(CONFIG["substack_url"])
        return f"{parsed.scheme}://{parsed.netloc}"

    def extract_article_metadata(self, title: str, subtitle: str, content: str) -> Dict[str, Any]:
        """Use Claude to extract subtitle, topics, and core mechanism for the inventory."""
        prompt = f"""Extract structured metadata from this blog article.

Title: {title}
Subtitle: {subtitle or "(none provided)"}
Content excerpt:
{content[:2500]}

Return a JSON object with exactly these fields:
- "subtitle": The best subtitle (use provided if clear, else write one under 12 words)
- "topics": Array of 3-6 lowercase topic tags (e.g. ["leadership", "execution", "management"])
- "core_mechanism": One sentence under 20 words capturing the core insight or mechanism

Return ONLY valid JSON. No markdown fences, no explanation."""

        message = self.anthropic_client.messages.create(
            model=CONFIG["anthropic_model"],
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    def fetch_all_substack_posts_via_api(self) -> List[Dict[str, Any]]:
        """Paginate the Substack /api/v1/posts endpoint to retrieve all published posts."""
        base_url = self._get_substack_base_url()
        if "yoursubstack.substack.com" in base_url:
            print("[Inventory] SUBSTACK_URL is still the placeholder — set it in .env first.", flush=True)
            return []

        all_posts: List[Dict[str, Any]] = []
        offset = 0
        limit = 25

        while True:
            url = f"{base_url}/api/v1/posts?offset={offset}&limit={limit}&sort=new"
            try:
                req = Request(url, method="GET")
                req.add_header("User-Agent", "PromotionAgent/1.0")
                with urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
            except (HTTPError, URLError, json.JSONDecodeError, OSError) as e:
                print(f"[Inventory] API fetch failed at offset {offset}: {e}", flush=True)
                break

            page = data if isinstance(data, list) else data.get("posts", [])
            if not page:
                break

            all_posts.extend(page)
            print(f"[Inventory] Fetched {len(all_posts)} posts so far...", flush=True)

            if len(page) < limit:
                break
            offset += limit

        return all_posts

    def add_article_to_inventory(self, post_id: str, title: str, url: str,
                                  published_date: str, subtitle: str, content: str,
                                  skip_export: bool = False):
        """Upsert one article into article_inventory and optionally re-export the Markdown."""
        try:
            metadata = self.extract_article_metadata(title, subtitle, content)
            final_subtitle = metadata.get("subtitle") or subtitle or ""
            topics_raw = metadata.get("topics", [])
            topics = ", ".join(topics_raw) if isinstance(topics_raw, list) else str(topics_raw)
            core_mechanism = metadata.get("core_mechanism", "")
        except Exception as e:
            print(f"[Inventory] Metadata extraction failed for '{title}': {e}", flush=True)
            final_subtitle = subtitle or ""
            topics = ""
            core_mechanism = ""

        conn = self._db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO article_inventory
                (id, title, subtitle, url, published_date, topics, core_mechanism, added_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (post_id, title, final_subtitle, url, published_date,
              topics, core_mechanism, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        if not skip_export:
            self.export_inventory_to_markdown()
        print(f"[Inventory] Added: {title}", flush=True)

    def build_article_inventory(self):
        """One-time build pass: fetch all historical posts from Substack API and populate inventory."""
        print("[Inventory] Starting full inventory build...", flush=True)
        posts = self.fetch_all_substack_posts_via_api()
        print(f"[Inventory] {len(posts)} posts found via API", flush=True)

        added = 0
        skipped = 0
        for post in posts:
            url = post.get("canonical_url", "")
            if not url:
                continue
            post_id = hashlib.md5(url.encode()).hexdigest()

            conn = self._db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM article_inventory WHERE id = ?", (post_id,))
            exists = cursor.fetchone() is not None
            conn.close()

            if exists:
                skipped += 1
                continue

            title = post.get("title") or ""
            subtitle = post.get("subtitle") or ""
            published_date = post.get("post_date") or ""
            content = post.get("truncated_body_text") or post.get("description") or ""

            try:
                self.add_article_to_inventory(
                    post_id, title, url, published_date, subtitle, content,
                    skip_export=True
                )
                added += 1
            except Exception as e:
                print(f"[Inventory] Failed to add '{title}': {e}", flush=True)

        self.export_inventory_to_markdown()
        print(f"[Inventory] Build complete: {added} added, {skipped} already in inventory.", flush=True)

    def export_inventory_to_markdown(self):
        """Write article_inventory.md to the project folder."""
        try:
            conn = self._db_connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, subtitle, url, published_date, topics, core_mechanism
                FROM article_inventory
                ORDER BY published_date DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            md_path = _script_dir / "article_inventory.md"
            now_str = datetime.now().strftime("%Y-%m-%d")
            count = len(rows)

            lines = [
                "# Article Inventory",
                "",
                f"*Last updated: {now_str} · {count} article{'s' if count != 1 else ''}*",
                "",
                "---",
                "",
            ]

            for title, subtitle, url, published_date, topics, core_mechanism in rows:
                pub_str = ""
                if published_date:
                    try:
                        clean = published_date.replace("Z", "").split("+")[0].split("T")[0]
                        d = datetime.strptime(clean, "%Y-%m-%d")
                        pub_str = d.strftime("%B %d, %Y")
                    except Exception:
                        pub_str = published_date[:10]

                lines.append(f"## [{title}]({url})")
                if pub_str:
                    lines.append(f"**Published:** {pub_str}")
                if subtitle:
                    lines.append(f"**Subtitle:** {subtitle}")
                if topics:
                    tag_str = " · ".join(
                        f"`{t.strip()}`" for t in topics.split(",") if t.strip()
                    )
                    lines.append(f"**Topics:** {tag_str}")
                if core_mechanism:
                    lines.append(f"**Summary:** {core_mechanism}")
                lines.append("")
                lines.append("---")
                lines.append("")

            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            print(f"[Inventory] Exported {count} articles to {md_path}", flush=True)
        except Exception as e:
            print(f"[Inventory] Markdown export failed: {e}", flush=True)

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
        if CONFIG.get("substack_linkedin_handle"):
            schedule.every().day.at("06:00").do(self.fetch_substack_profile)
            self.fetch_substack_profile()
        
        # Run forever
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    import sys
    agent = PromotionAgent()
    if "--build-inventory" in sys.argv:
        agent.build_article_inventory()
    else:
        agent.run()
