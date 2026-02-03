# Blog Promotion Agent

An autonomous agent that implements your "promote sentences, not articles" strategy for every blog post you publish.

## What It Does

Every time you publish a post on Substack, this agent automatically:

1. **Extracts** the best "outward sentence" from your post
2. **Routes** it to the optimal platform (LinkedIn, Substack Notes, or Bluesky)
3. **Generates** a complete promotional post (not a teaser)
4. **Creates** commenting suggestions for ecosystem engagement
5. **Generates** weekly "start here" on-ramp posts
6. **Presents** everything in a review dashboard for you to approve and post

## Features

### ✅ Daily Automation
- Monitors your Substack RSS feed hourly
- Extracts the "spine" sentence that stands alone
- Routes based on content (power/bias → LinkedIn, ideas/frames → Substack Notes, playful → Bluesky)
- Generates platform-native promotional posts
- Creates commenting task suggestions

### ✅ Weekly Automation
- Every Monday: generates "start here" on-ramp post
- Suggests 3 posts for new readers (frame + situational + bridge)

### ✅ Review & Release Dashboard
- Clean web interface to review all drafts
- Edit promotional posts inline
- Copy with one click
- Mark as published to track what you've done
- No direct platform posting (respects your workflow)

### ✅ Activity Tracking
- SQLite database tracks all posts and promotions
- Knows what's pending, published, or skipped
- Prevents duplicates

## Architecture

```
Substack RSS Feed
      ↓
[Agent monitors every hour]
      ↓
[Claude extracts outward sentence]
      ↓
[Routes to platform based on content]
      ↓
[Generates promotional post]
      ↓
[Saves to database + dashboard JSON]
      ↓
[Web Dashboard] ← You review and approve
      ↓
[You copy/paste to platforms]
      ↓
[Mark as published in dashboard]
```

## Setup Instructions

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- Anthropic API key ([get one here](https://console.anthropic.com/))

**Steps:**

1. Clone or download this directory

2. Run the setup script:

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

If `.env` does not exist, it is created automatically from `.env.example` the first time you run the agent or `docker-compose up`. Edit `.env` with your values:
```
SUBSTACK_URL=https://yoursubstack.substack.com/feed   # Use /feed, not /publish/home
ANTHROPIC_API_KEY=sk-ant-your-key-here
# Optional: Substack Developer API (profile stats). Add when Substack provides your API key.
# SUBSTACK_API_KEY=
# SUBSTACK_LINKEDIN_HANDLE=yourlinkedin   # e.g. johndoe from linkedin.com/in/johndoe
```

3. Start the agent:
```bash
docker-compose up -d
```

5. Access the dashboard:
```
http://localhost:5000
```

The agent is now running in the background, checking for new posts every hour.

### Option 2: Cloud Deployment (Railway, Render, Fly.io)

**For Railway:**

1. Create new project from GitHub repo
2. Add environment variables:
   - `SUBSTACK_URL`
   - `ANTHROPIC_API_KEY`
3. Deploy
4. Railway will provide a public URL for your dashboard

**For Render:**

1. Create new Web Service
2. Connect your repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `supervisord -c supervisord.conf`
5. Add environment variables
6. Deploy

**For Fly.io:**

1. Install flyctl CLI
2. Run `fly launch`
3. Set secrets: `fly secrets set ANTHROPIC_API_KEY=sk-ant-...`
4. Deploy: `fly deploy`

### Option 3: Local/VPS Python

**Prerequisites:**
- Python 3.11+
- pip

**Steps:**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export SUBSTACK_URL="https://yoursubstack.substack.com/feed"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

3. Run both processes (in separate terminals):
```bash
# Terminal 1: Agent
python agent.py

# Terminal 2: Dashboard server
python server.py
```

4. Access dashboard at `http://localhost:5000`

## Usage Workflow

### When You Publish

1. **Agent detects new post** (within 1 hour)
2. **Dashboard updates** with new promotion draft
3. **You review** the generated content:
   - Check the extracted outward sentence
   - Review the promotional post
   - Edit if needed (inline editing)
4. **Copy and post** to the suggested platform
5. **Mark as published** in dashboard
6. **Follow commenting suggestions** (10 min that day)

### Weekly Tasks

Every Monday morning, the agent generates:
- "Start here" on-ramp post suggesting 3 posts for new readers
- You review, copy, and post

### The Dashboard

**Main sections:**

1. **Pending Promotions** - Review and approve promotional posts
   - Platform badge shows where to post
   - Outward sentence highlighted
   - Edit inline if needed
   - One-click copy
   - Mark published when done

2. **Commenting Tasks** - 10-minute ecosystem engagement
   - Suggestions for where to comment
   - What angle to contribute
   - Helps you become familiar in the right rooms

3. **Weekly Tasks** - On-ramp posts and larger efforts
   - Generated every Monday
   - Copy and post when ready

## Customization

### Change Platform Routing

Edit `PLATFORM_ROUTING` in `agent.py`:

```python
PLATFORM_ROUTING = {
    "linkedin": ["your", "keywords", "here"],
    "substack_notes": ["different", "keywords"],
    "bluesky": ["more", "keywords"],
}
```

### Substack Developer API (optional)

The agent gets **posts** from your Substack RSS feed. For **profile statistics** (follower count, free subscribers, leaderboard), you can use the [Substack Developer API](https://support.substack.com/hc/en-us/articles/45099095296916-Substack-Developer-API). It is queried by your **LinkedIn handle** (e.g. `johndoe` from `linkedin.com/in/johndoe`). Add to `.env` when ready:

- **SUBSTACK_LINKEDIN_HANDLE** – Your LinkedIn handle so the agent can fetch your Substack profile stats. When set, the agent fetches profile data daily and the dashboard shows followers and subscribers in the Analytics section.
- **SUBSTACK_API_KEY** – Leave empty for now; add when Substack provides an API key (e.g. for authenticated requests). The code sends it as `Authorization: Bearer <key>` when set.

### Adjust Check Interval

Change in `.env`:
```
CHECK_INTERVAL_MINUTES=30  # Check every 30 minutes instead of 60
```

### Modify Promotional Post Style

Edit the prompt in `generate_promotional_post()` method in `agent.py`.

### Add New Platforms

1. Add platform to `PLATFORM_ROUTING` dictionary
2. Add platform-specific guidelines in `generate_promotional_post()`
3. Update dashboard CSS for new platform badge color

## Database Schema

SQLite database (`promotion_agent.db`) with tables:

- **posts** - All discovered blog posts (from RSS)
- **promotions** - Generated promotional content per post
- **weekly_tasks** - On-ramp posts and weekly efforts
- **activity_log** - Commenting suggestions and completed activities
- **analytics_events** - Dashboard clicks and engagement
- **substack_profile** - Cached Substack Developer API profile (followers, subscribers) when `SUBSTACK_LINKEDIN_HANDLE` is set

## Costs

**Anthropic API usage:**
- ~$0.02-0.05 per post processed
- Expect $2-5/month if publishing 2-3 posts per week
- Uses Claude Sonnet 4 for quality extraction and generation

**Infrastructure:**
- Free tier sufficient on Railway, Render, or Fly.io
- ~$5/month for basic cloud hosting if needed

## Monitoring

### Check Agent Health

```bash
# Docker
docker-compose logs -f promotion-agent

# View stats
curl http://localhost:5000/api/stats
```

### Manual Database Queries

**All platforms (Python has sqlite3 built in):**
```powershell
python db_shell.py
```
Then type SQL, e.g. `SELECT * FROM promotions WHERE status = 'pending_review';` — type `.quit` to exit.

**If you have the sqlite3 CLI installed** (e.g. Mac/Linux, or [SQLite for Windows](https://www.sqlite.org/download.html)):
```bash
sqlite3 promotion_agent.db
# See pending promotions: SELECT * FROM promotions WHERE status = 'pending_review';
# See all posts: SELECT title, published_date FROM posts ORDER BY published_date DESC;
```

## Debugging server.py

If the server fails to start or you want to step through code:

1. **Run from the project folder** (paths are relative):
   ```powershell
   cd "path\to\Promotion Agent"
   python server.py
   ```
   On startup the server prints its working directory and DB path so you can confirm it found files.

2. **Use the debugger in Cursor/VS Code**
   - Open **Run and Debug** (Ctrl+Shift+D)
   - Choose **"Debug server.py"**
   - Set breakpoints in `server.py` (click in the gutter)
   - Press F5 to start; the server will stop on breakpoints

3. **Common failures**
   - **"unable to open database file"** — Server now runs from its script directory and uses an absolute DB path; if it still fails, ensure the agent has run once so `promotion_agent.db` exists.
   - **Database not created** — The agent now creates the DB and tables before initializing the Anthropic client, so the DB should be created even if the API key is missing. If it still isn't, run `python create_db.py` to create it, then run the agent again.
   - **Missing tables** — `/api/stats` no longer crashes if `activity_log` (or other tables) don't exist yet; it returns empty counts.
   - **Port 5000 in use** — Change the port in the last line of `server.py` (e.g. `port=5001`) or stop the other process using 5000.

## Troubleshooting

**Agent not detecting posts:**
- Use the **feed** URL (`https://yoursubstack.substack.com/feed`), not the publish URL (`/publish/home`—that page is private and returns no RSS).
- Verify: `curl https://yoursubstack.substack.com/feed` should return XML.
- Check agent logs for errors.
- Ensure agent is running: `docker-compose ps`.

**Dashboard shows nothing / Permission denied:**
- Wait up to 1 hour for first check (or restart agent to trigger immediate check)
- Verify `review_dashboard.json` exists and is readable
- **Permission denied** on Windows/OneDrive: The server now falls back to an empty dashboard if it can't read the file. To fix: right-click the project folder → "Always keep on this device" (OneDrive); or ensure the file isn't open/locked elsewhere; or clear Read-only on the file.
- Check browser console for errors

**API key errors:**
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check key hasn't expired at https://console.anthropic.com/

**Can't access dashboard:**
- Ensure port 5000 isn't blocked by firewall
- For cloud deployment, use the provided public URL
- Check server logs: `docker-compose logs server`

## Security Notes

- Never commit `.env` file (already in `.gitignore`)
- API key gives access to your Anthropic account - keep it secret
- Dashboard has no authentication - use firewall rules if hosting publicly
- Consider adding basic auth if deploying to public cloud

## Future Enhancements (Optional)

Potential additions you could make:

- [ ] Direct platform API integration (auto-posting)
- [ ] Email notifications when new promotions ready
- [ ] Analytics tracking (clicks, engagement)
- [ ] A/B testing different outward sentences
- [ ] Mobile app for review-on-the-go
- [ ] Slack/Discord notifications
- [ ] Multi-user support for team blogs

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review agent logs: `docker-compose logs`
3. Check database state: `python db_shell.py` (or sqlite3 CLI if installed)
4. Verify environment variables are set correctly

## License

Use freely for your own blog promotion. Modify as needed.

---

**Pro tip:** The agent gets smarter as it processes more posts. Review the first few promotional posts closely and provide feedback by editing them. The patterns you establish will inform future generations.
