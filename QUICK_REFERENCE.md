# Quick Reference

A cheat sheet for daily use once the agent is running.

---

## Dashboard

| Deployment | URL |
|---|---|
| Local (Docker or Python) | `http://localhost:5000` |
| Railway | `https://your-app.railway.app` |
| Render | `https://your-app.onrender.com` |
| Fly.io | `https://your-app.fly.dev` |

If `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` are set in `.env`, your browser will prompt for credentials on first visit.

---

## First-Time Setup

```bash
# 1. Copy config template
cp .env.example .env
# Edit .env — set SUBSTACK_URL, ANTHROPIC_API_KEY, and (for cloud) DASHBOARD_USERNAME/PASSWORD

# 2. Start (Docker)
docker-compose up -d

# 3. Build article inventory (one-time)
# Via dashboard: click "🔨 Build / Refresh Inventory"
# Or via CLI:
docker compose exec promotion-agent python agent.py --build-inventory
```

---

## Daily Workflow (15 minutes)

```
1. Publish to Substack as usual
2. Wait ~1 hour (agent checks hourly; restarts trigger an immediate check)
3. Open dashboard
4. Review → Edit if needed → Copy → Paste to platform → Mark published
5. Do 10-min commenting (follow suggestions in Commenting Tasks)
```

New articles are **automatically added to the inventory** — nothing extra to do.

---

## Dashboard Sections

All sections are **collapsible** — click any heading. State saves across page loads.

| Section | Purpose |
|---|---|
| 📊 Analytics | Copy/publish/skip activity; Substack profile stats (if configured) |
| 📝 Pending Promotions | Review and approve drafted posts |
| 💬 Commenting Tasks | Where to comment and what angle to take |
| 📅 Weekly Tasks | Monday on-ramp posts for new readers |
| 📚 Article Inventory | Searchable catalog of every published article |
| 📦 Archive | Published/skipped items; recover any item to pending |

---

## Configuration

All settings live in `.env`. Key variables:

| Variable | Required | Notes |
|---|---|---|
| `SUBSTACK_URL` | ✅ always | Must end in `/feed` |
| `ANTHROPIC_API_KEY` | ✅ always | From console.anthropic.com |
| `DASHBOARD_USERNAME` | ✅ for cloud | Blank = no auth (local only) |
| `DASHBOARD_PASSWORD` | ✅ for cloud | Blank = no auth (local only) |
| `ANTHROPIC_MODEL` | optional | Default: `claude-sonnet-4-20250514`. See README AI Configuration section. |
| `CHECK_INTERVAL_MINUTES` | optional | Default: 60 |
| `SUBSTACK_LINKEDIN_HANDLE` | optional | Enables profile stats in Analytics |

After changing `.env`, restart the agent: `docker-compose restart`

---

## Docker Commands

```bash
docker-compose up -d              # Start in background
docker-compose down               # Stop
docker-compose restart            # Restart all services
docker-compose logs -f            # Follow all logs
docker-compose logs -f promotion-agent  # Follow agent + server logs
docker-compose ps                 # Check container status
docker-compose up -d --build      # Rebuild image after code changes
```

---

## Manual Triggers

```bash
# Force RSS check right now
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().check_for_new_posts()"

# Regenerate dashboard JSON
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().generate_review_dashboard()"

# Generate weekly on-ramp post
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().generate_weekly_onramp_post()"

# Build / refresh article inventory
docker compose exec promotion-agent python agent.py --build-inventory

# Re-export article_inventory.md (no API calls)
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().export_inventory_to_markdown()"
```

---

## Article Inventory

### First-time build
```bash
# Dashboard button: "🔨 Build / Refresh Inventory"
# Or:
docker compose exec promotion-agent python agent.py --build-inventory
```
~$0.05–0.15 one-time cost. Idempotent — re-running skips existing articles. New articles are added automatically going forward.

### Searching
In the Article Inventory section of the dashboard:
- **Keyword** — searches title, subtitle, and core mechanism summary; matched text is highlighted
- **Topic** — filter by topic tag
- **Year** — filter by publication year
- **✕ Clear** — reset all filters

### Re-export Markdown
```bash
# Dashboard button: "⬇ Re-export Markdown"
# Or:
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().export_inventory_to_markdown()"
```
Writes `article_inventory.md` to the project folder.

---

## API Endpoints

```bash
# Health / stats
curl http://localhost:5000/api/stats

# Dashboard data
curl http://localhost:5000/review_dashboard.json

# Article inventory
curl http://localhost:5000/api/inventory

# Trigger inventory build (runs in background)
curl -X POST http://localhost:5000/api/inventory/build

# Check build status
curl http://localhost:5000/api/inventory/status

# Re-export article_inventory.md
curl -X POST http://localhost:5000/api/inventory/export

# Mark promotion published (replace 123 with ID)
curl -X POST http://localhost:5000/api/mark-published/123

# Skip promotion
curl -X POST http://localhost:5000/api/skip-promotion/123

# Complete weekly task
curl -X POST http://localhost:5000/api/complete-task/123
```

If auth is enabled, add credentials: `curl -u admin:password http://localhost:5000/api/stats`

---

## Database Queries

```bash
# Interactive SQL shell (no sqlite3 CLI needed)
python db_shell.py
# Type .quit to exit
```

```sql
-- Pending promotions
SELECT posts.title, p.platform, p.created_date
FROM promotions p JOIN posts ON p.post_id = posts.id
WHERE p.status = 'pending_review';

-- All posts discovered
SELECT title, published_date, status FROM posts ORDER BY published_date DESC;

-- Promotion counts by status
SELECT status, COUNT(*) FROM promotions GROUP BY status;

-- Article inventory
SELECT title, topics, core_mechanism FROM article_inventory ORDER BY published_date DESC;

-- Inventory count
SELECT COUNT(*) FROM article_inventory;
```

---

## Platform Posting Steps

**LinkedIn:** Start a post → paste → post → return to dashboard → Mark published

**Substack Notes:** Notes (left sidebar) → New note → paste → post → Mark published

**Bluesky:** "What's up?" → paste → post → Mark published

---

## Troubleshooting Quick Fixes

**No pending promotions after publishing**
```bash
# Trigger check manually
docker compose exec promotion-agent python -c \
  "from agent import PromotionAgent; PromotionAgent().check_for_new_posts()"
# Then refresh dashboard
```

**Can't reach dashboard**
```bash
docker-compose ps                        # Is container running?
curl http://localhost:5000/api/stats     # Does API respond?
docker-compose logs --tail=30            # Any errors?
```

**Database locked or "unable to open database file"**
```bash
docker-compose down && docker-compose up -d   # Full restart
# On Windows/OneDrive: right-click project folder → "Always keep on this device"
```

**Forgot dashboard password**
- Open `.env`, find `DASHBOARD_PASSWORD`, reset it to a new value, then `docker-compose restart`

**Inventory build fails**
```bash
# Check logs
docker compose logs promotion-agent
# Verify your real Substack URL is set (not the placeholder)
# Check API key has credits at console.anthropic.com
# Retry — the build is idempotent
docker compose exec promotion-agent python agent.py --build-inventory
```

---

## Key Files

```
.env                   Your config (never commit this)
promotion_agent.db     SQLite database
review_dashboard.json  Dashboard data (regenerated hourly)
article_inventory.md   Exported inventory (regenerated on updates)
```

---

## Cost Estimate

```
Posts per week × 4 = posts per month
Posts per month × $0.04 average ≈ monthly API cost

Example: 2 posts/week → 8/month → ~$0.32/month API
Add cloud hosting: $0 (free tier) to $7/month (paid tier)
```

---

## Health Checklist

```
✓ docker-compose ps shows container "Up"
✓ http://localhost:5000 loads the dashboard
✓ /api/stats returns JSON
✓ Logs show "Checking for new posts" with no crash loop
✓ Article inventory has entries (after build)
✓ New post appears in Pending Promotions within 1 hour of publishing
```
