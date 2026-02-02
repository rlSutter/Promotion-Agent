# Quick Reference Card

Keep this handy for your daily workflow.

## Daily Workflow (15 minutes)

### When You Publish

```
1. Publish to Substack (as usual)
2. Wait ~1 hour (or restart agent for immediate processing)
3. Check dashboard: http://localhost:5000
4. Review → Edit (if needed) → Copy → Post
5. Mark as published
6. Do 10-min commenting (follow suggestions)
7. Done!
```

## Dashboard URL

**Local:**
```
http://localhost:5000
```

**Cloud (your deployment):**
```
https://your-app.railway.app
https://your-app.onrender.com
https://your-app.fly.dev
```

## Common Commands

### Docker (Local)

```bash
# Start agent
docker-compose up -d

# Stop agent
docker-compose down

# View logs
docker-compose logs -f

# Restart agent
docker-compose restart

# Check status
docker-compose ps

# Update after code changes
docker-compose up -d --build
```

### Database Queries

```bash
# Open database
sqlite3 promotion_agent.db

# See pending promotions
SELECT title, platform, created_date 
FROM promotions p 
JOIN posts ON p.post_id = posts.id 
WHERE p.status = 'pending_review';

# See all posts
SELECT title, published_date, status 
FROM posts 
ORDER BY published_date DESC;

# Count by status
SELECT status, COUNT(*) 
FROM promotions 
GROUP BY status;

# Exit
.quit
```

### Manual Triggers

```bash
# Force check now (Docker)
docker-compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().check_for_new_posts()"

# Regenerate dashboard
docker-compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().generate_review_dashboard()"

# Generate weekly on-ramp
docker-compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().generate_weekly_onramp_post()"
```

## Platform Posting Guide

### LinkedIn

```
1. Copy from dashboard
2. Go to LinkedIn
3. Click "Start a post"
4. Paste content
5. Post
6. Return to dashboard → Mark published
```

### Substack Notes

```
1. Copy from dashboard
2. Go to Substack
3. Click "Notes" in left sidebar
4. Click "New note"
5. Paste content
6. Post
7. Return to dashboard → Mark published
```

### Bluesky

```
1. Copy from dashboard
2. Go to Bluesky
3. Click "What's up?"
4. Paste content
5. Post
6. Return to dashboard → Mark published
```

## Commenting Workflow (10 min/day)

```
1. Check "Commenting Tasks" section in dashboard
2. Open Substack/LinkedIn/Bluesky
3. Search for relevant posts (use suggestions as guide)
4. Leave 2-3 thoughtful comments
5. Add value, don't promote
6. Done!
```

## Weekly Tasks (Mondays)

```
1. Check dashboard for weekly on-ramp post
2. Review the 3 suggested posts
3. Edit if needed
4. Copy to Substack Notes or main platform
5. Post
6. Mark as complete
```

## Troubleshooting Quick Fixes

### Agent not detecting posts
```bash
# Check RSS feed works
curl https://yoursubstack.substack.com/feed

# Restart agent
docker-compose restart

# Check logs
docker-compose logs agent
```

### Dashboard empty
```bash
# Wait 1 hour OR trigger manually
docker-compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().check_for_new_posts(); PromotionAgent().generate_review_dashboard()"
```

### Can't access dashboard
```bash
# Check server is running
docker-compose ps

# Check port
curl http://localhost:5000/api/stats

# Restart server
docker-compose restart server
```

### Database locked
```bash
# Stop everything
docker-compose down

# Start again
docker-compose up -d
```

## API Endpoints

```bash
# Get stats
curl http://localhost:5000/api/stats

# Get dashboard data
curl http://localhost:5000/review_dashboard.json

# Mark promotion published (replace 123 with ID)
curl -X POST http://localhost:5000/api/mark-published/123

# Skip promotion
curl -X POST http://localhost:5000/api/skip-promotion/123

# Complete task
curl -X POST http://localhost:5000/api/complete-task/123
```

## File Locations

```
promotion_agent.db          # Database (all state)
review_dashboard.json       # Dashboard data (regenerated hourly)
.env                       # Your config (secrets!)
docker-compose.yml         # Docker config
```

## Updating Substack URL

```bash
# Edit .env file
nano .env

# Change SUBSTACK_URL line
SUBSTACK_URL=https://new-url.substack.com/feed

# Restart
docker-compose restart
```

## Changing Check Interval

```bash
# Edit .env
CHECK_INTERVAL_MINUTES=30

# Restart
docker-compose restart
```

## Backup Your Data

```bash
# Backup database
cp promotion_agent.db promotion_agent_backup_$(date +%Y%m%d).db

# Restore from backup
cp promotion_agent_backup_20250115.db promotion_agent.db
docker-compose restart
```

## Monitoring

### Check if it's working

```bash
# Should show running containers
docker-compose ps

# Should show recent activity
docker-compose logs --tail=50 agent

# Should return JSON with stats
curl http://localhost:5000/api/stats
```

### Health check

```bash
# Everything OK if all pass:
✓ Agent container running
✓ Server container running  
✓ Dashboard loads in browser
✓ Database file exists
✓ API stats returns data
```

## Cost Tracking

```bash
# Rough estimate per month
Posts per week: ___
Posts per month: ___ × 4 = ___
API cost per post: $0.03
Monthly API cost: ___ × $0.03 = $___

# Add infrastructure
Railway/Render/Fly: $0-7/month
Total: $___/month
```

## Support Checklist

Before asking for help:

- [ ] Checked logs: `docker-compose logs`
- [ ] Verified .env file exists and has correct values
- [ ] Tested RSS feed: `curl https://yoursubstack.substack.com/feed`
- [ ] Restarted agent: `docker-compose restart`
- [ ] Checked database exists: `ls -lh promotion_agent.db`
- [ ] Verified dashboard loads: open `http://localhost:5000`

## Keyboard Shortcuts

In dashboard (browser):
- `Ctrl/Cmd + F` - Search for post title
- `Ctrl/Cmd + R` - Refresh dashboard
- `Ctrl/Cmd + C` - Copy selected text

## Browser Bookmarks to Add

- [ ] http://localhost:5000 (Dashboard)
- [ ] https://yoursubstack.substack.com/publish (Write)
- [ ] https://console.anthropic.com/ (API usage)
- [ ] https://linkedin.com (Post)
- [ ] https://yoursubstack.substack.com/notes (Notes)

---

**Print this page and keep it by your desk!**

Or save to: `/promotion-agent-reference.md`
