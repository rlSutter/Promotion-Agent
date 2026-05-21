# Blog Promotion Agent

An autonomous agent that implements a "promote sentences, not articles" strategy for every Substack post you publish. It runs in the background, monitors your RSS feed, and drafts platform-specific promotional content for your review — so promotion takes 15 minutes instead of 45.

## Who This Is For

Independent Substack writers running their own promotion workflow. Solo operators, not teams. Writers who publish thoughtfully and hate the 45-minute post-publish ritual of crafting platform-specific copy, figuring out what to comment on in their ecosystem, and trying to remember what they've written before. The intended use is focused: open the dashboard after publishing, make decisions, copy drafts, close it. A 15-minute window, not an always-on tool.

## Why This Exists

Publishing on Substack is the hard part. Promotion is supposed to be the easy part — but in practice it takes 30 to 45 minutes per post, most of which is mechanical work that produces inconsistent results: picking what to quote, rewriting it for each platform's register, deciding where to comment this week, trying to remember what you wrote six months ago.

That friction compounds. Writers who promote consistently grow faster than writers who publish more but promote sporadically. The bottleneck is not ideas or audience — it is the post-publish ritual being unpleasant enough that it gets skipped.

The core insight behind this tool is that most of that ritual is *systematic*, not creative. There is a structure to a good LinkedIn post, a structure to a good Bluesky note, a structure to useful ecosystem commenting. Once you know the structure, the work is mostly substitution: plug in the post's core claim, format it for the platform, add the link. A machine can do that substitution better and faster than a writer who just finished publishing and wants to be done.

What a machine cannot do is judge whether the claim is stated well, whether the voice sounds right, or whether the generated post matches what the writer actually wanted to say. That judgment belongs to the writer, and this tool preserves it. Every piece of content passes through a review step before it goes anywhere. The agent handles the systematic; the writer handles the judgment.

The design reflects a specific workflow: open the dashboard after publishing, spend 15 minutes reviewing and copying, close it. Not an always-on command center. Not a social media management platform. A focused ritual replacement for a solo writer who publishes thoughtfully and wants promotion to match.

## What It Does

Every time you publish a post on Substack, the agent automatically:

1. **Extracts** the best "outward sentence" — the spine of the post that stands alone
2. **Routes** it to the right platform (LinkedIn, Substack Notes, or Bluesky) based on content type
3. **Generates** a complete promotional post (not a teaser)
4. **Creates** commenting suggestions for ecosystem engagement
5. **Adds** the post to your searchable article inventory
6. **Generates** weekly "start here" on-ramp posts every Monday
7. **Presents** everything in a review dashboard for you to approve and post

You review, edit if needed, copy, paste, and mark done. No direct posting — you stay in control.

---

## Prerequisites

Before you start, you need:

- **A Substack publication** with a public RSS feed (`https://yourname.substack.com/feed`)
- **An Anthropic API key** — get one free at [console.anthropic.com](https://console.anthropic.com/)
- **Docker Desktop** (recommended) — [download here](https://www.docker.com/products/docker-desktop/); or Python 3.11+ if you prefer to run without Docker

That's it. No Substack API key, no OAuth setup, no database to provision.

---

## Quick Start (Docker — 5 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/promotion-agent.git
cd promotion-agent

# 2. Create your config file
cp .env.example .env
# Edit .env — at minimum set SUBSTACK_URL and ANTHROPIC_API_KEY

# 3. Start the agent
docker-compose up -d

# 4. Open the dashboard
# http://localhost:5000
```

On first run, the agent checks your RSS feed immediately, then rechecks every hour. The dashboard is live at `http://localhost:5000`.

### First-Time Setup (one-time after start)

Build your article inventory to import your full publishing history:

- **Via dashboard:** Click **🔨 Build / Refresh Inventory** in the Article Inventory section
- **Via command line:**
  ```bash
  docker compose exec promotion-agent python agent.py --build-inventory
  ```

This costs ~$0.05–0.15 in API credits depending on how many articles you have. It's safe to re-run — already-imported articles are skipped.

---

## Configuration

All configuration lives in `.env`. Copy `.env.example` to get started:

```bash
cp .env.example .env
```

### Required

| Variable | Description | Example |
|---|---|---|
| `SUBSTACK_URL` | Your Substack RSS feed URL. Use `/feed`, not `/publish/home`. | `https://yourname.substack.com/feed` |
| `ANTHROPIC_API_KEY` | Your API key from [console.anthropic.com](https://console.anthropic.com/) | `sk-ant-api03-...` |

### Required for cloud / shared deployments

| Variable | Description |
|---|---|
| `DASHBOARD_USERNAME` | Username for dashboard login (HTTP Basic Auth) |
| `DASHBOARD_PASSWORD` | Password for dashboard login |

> **If you deploy to a public URL (Railway, Render, Fly.io, etc.), you must set both of these.** The dashboard is open to anyone who can reach the URL if they are not set. For local-only use they can be left blank.

### Optional

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model to use for all AI calls. See [AI Configuration](#ai-configuration) below. |
| `CHECK_INTERVAL_MINUTES` | `60` | How often the agent checks for new posts |
| `SUBSTACK_LINKEDIN_HANDLE` | *(none)* | Your LinkedIn handle — enables Substack profile stats (follower count, subscribers) in the Analytics section |
| `SUBSTACK_API_KEY` | *(none)* | Substack Developer API key — leave blank for now; the field is ready for when Substack issues keys |
| `PROMOTION_AGENT_DB` | `./promotion_agent.db` | Override the database path (useful on Windows/OneDrive where the default location may not be writable) |

### Example `.env` for local use

```
SUBSTACK_URL=https://yourname.substack.com/feed
ANTHROPIC_API_KEY=sk-ant-api03-...
CHECK_INTERVAL_MINUTES=60
```

### Example `.env` for cloud deployment

```
SUBSTACK_URL=https://yourname.substack.com/feed
ANTHROPIC_API_KEY=sk-ant-api03-...
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=choose-a-strong-password
CHECK_INTERVAL_MINUTES=60
```

---

## Setup Options

### Option 1: Docker (Recommended)

Works on Windows, Mac, and Linux. Everything runs in a container — no Python environment to manage.

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f promotion-agent

# Rebuild after code changes
docker-compose up -d --build
```

Dashboard: `http://localhost:5000`

### Option 2: Cloud Deployment

Deploy to Railway, Render, or Fly.io for a persistent public URL. Full instructions in [DEPLOYMENT.md](DEPLOYMENT.md).

**Summary for Railway (easiest):**
1. Fork this repo to your GitHub account
2. Create a new Railway project from your fork
3. Add environment variables (including `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`)
4. Railway auto-deploys; your dashboard URL appears under Settings → Domains

### Option 3: Local Python (no Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUBSTACK_URL="https://yourname.substack.com/feed"
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Terminal 1: run the agent
python agent.py

# Terminal 2: run the dashboard server
python server.py
```

Dashboard: `http://localhost:5000`

---

## Usage Workflow

### When You Publish

1. Agent detects new post (within 1 hour, or immediately on restart)
2. Dashboard shows a new promotion draft
3. Review the outward sentence and generated promotional post
4. Edit inline if needed
5. Copy → paste to the suggested platform → mark as published
6. Follow the commenting suggestions (10 min)

New article is also **automatically added to the article inventory** — nothing extra to do.

### Every Monday

The agent generates a "start here" on-ramp post suggesting 3 articles for new readers. Review, copy, and post.

---

## The Dashboard

Access at `http://localhost:5000` (or your cloud URL). All six sections are **collapsible** — click any heading. State is saved in your browser and restored on the next visit.

| Section | What's here |
|---|---|
| 📊 Analytics | Copy/publish/skip counts over 7 and 30 days; Substack profile stats if `SUBSTACK_LINKEDIN_HANDLE` is configured |
| 📝 Pending Promotions | Drafted promotional posts to review, edit, copy, and mark published |
| 💬 Commenting Tasks | Suggestions for where to comment and what angle to take |
| 📅 Weekly Tasks | Monday on-ramp posts for new readers |
| 📚 Article Inventory | Searchable catalog of every published article (keyword, topic, year filters) |
| 📦 Archive | Published and skipped items; recover any item back to pending |

---

## AI Configuration

The agent uses the [Anthropic API](https://console.anthropic.com/) for all content generation. No other AI service is required.

### Model

The default model is **`claude-sonnet-4-20250514`** (Claude Sonnet 4). This is the recommended choice: it produces high-quality promotional copy and handles nuanced extraction well, at a cost of roughly $0.03–0.05 per post.

To use a different model, set `ANTHROPIC_MODEL` in `.env`:

```
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

Available Claude models and their IDs are listed in the [Anthropic documentation](https://docs.anthropic.com/en/docs/about-claude/models). Haiku models cost less but produce noticeably shorter, less polished output; Opus models cost more with marginal improvement for this workload. Sonnet is the right balance.

### What the AI does

The agent makes five distinct API calls per new post, plus one on demand for the weekly task:

| Call | Method | Purpose | Max tokens |
|---|---|---|---|
| Outward sentence extraction | `extract_outward_sentence()` | Finds the single "spine" sentence that stands alone — the core claim of the post | 200 |
| Promotional post generation | `generate_promotional_post()` | Writes a platform-native post (claim → practical consequence → reflection → link) | 500 |
| Commenting suggestions | `generate_commenting_tasks()` | Suggests 2–3 topic areas and angles for ecosystem commenting | 400 |
| Article metadata extraction | `extract_article_metadata()` | Extracts subtitle, 3–6 topic tags, and a one-sentence core mechanism summary for the inventory | 300 |
| Weekly on-ramp post | `generate_weekly_onramp_post()` | Every Monday, selects 3 articles (frame / situational / bridge) and drafts a "start here" post | 600 |

Platform routing is **not** AI-based — it uses keyword matching against `PLATFORM_ROUTING` in `agent.py` (fast, free, predictable).

### Platform tone guidelines

Each platform gets a different brief passed to the promotional post prompt:

| Platform | Tone brief |
|---|---|
| LinkedIn | Professional, outcomes-focused, 2–3 sentences |
| Substack Notes | Thoughtful, complete idea, slightly more casual |
| Bluesky | Playful, gift-like, short and punchy |

Edit the `platform_guidelines` dict in `generate_promotional_post()` in `agent.py` to change these.

### Customizing the prompts

All prompts are plain Python f-strings in `agent.py`. The key methods and what to edit:

- **Outward sentence style** — `extract_outward_sentence()`: the three sentence shapes listed in the prompt (`If X then Y`, `People call it Z but it's W`, `This isn't about A it's about B`). Add or remove shapes here.
- **Promotional post structure** — `generate_promotional_post()`: the 4-step structure (claim → practical → reflection → link) and the constraint list. This is where to change the voice, add platform-specific rules, or adjust length.
- **Commenting suggestions** — `generate_commenting_tasks()`: change how many suggestions are requested or what format they're returned in.
- **Inventory metadata** — `extract_article_metadata()`: add or remove fields from the JSON schema. If you add a field, also add the corresponding column to the `article_inventory` table in `init_database()`.
- **Weekly on-ramp** — `generate_weekly_onramp_post()`: change the three post types (frame / situational / bridge), the intro language, or how many posts are included.

### API key and billing

Get your key at [console.anthropic.com](https://console.anthropic.com/). New accounts receive free credits. Usage is charged per token (input + output combined).

Estimated monthly cost at 2–3 posts/week:
- ~$0.03–0.05 per post × 10 posts/month ≈ **$0.30–0.50/month** for post processing
- One-time inventory build for a full back-catalog: **$0.05–0.15**
- Weekly on-ramp posts: **~$0.10/month**
- **Total: roughly $2–5/month** at regular publishing cadence

The agent logs an explicit error message with a link to the billing page if your credit balance is too low.

---

## Customization

### Platform routing

The agent routes content to platforms based on keywords in the post. Edit `PLATFORM_ROUTING` in `agent.py`:

```python
PLATFORM_ROUTING = {
    "linkedin": ["leadership", "power", "bias", "career", "management"],
    "substack_notes": ["ideas", "frames", "systems", "thinking"],
    "bluesky": ["playful", "culture", "gaming", "fun"],
}
```

### Check interval

```
CHECK_INTERVAL_MINUTES=30
```

### Promotional post style

Edit the Claude prompt in `generate_promotional_post()` in `agent.py`.

### Add a new platform

1. Add the platform and its keywords to `PLATFORM_ROUTING`
2. Add platform-specific tone guidelines in `generate_promotional_post()`
3. Add a CSS badge color in `dashboard.html`

### Substack profile stats (optional)

Set `SUBSTACK_LINKEDIN_HANDLE` to your LinkedIn handle (e.g. `johndoe` from `linkedin.com/in/johndoe`). The agent fetches your Substack follower count and subscriber stats daily and displays them in the Analytics section.

---

## Costs

**Anthropic API:**
- ~$0.03–0.05 per post processed (sentence extraction + promo + commenting suggestions + inventory metadata)
- One-time inventory build: ~$0.05–0.15 depending on back-catalog size
- Publishing 2–3×/week ≈ $2–5/month total

**Infrastructure:**
- Local: free
- Railway / Render / Fly.io: free tier is sufficient to start; ~$5–7/month for always-on paid tier

---

## Monitoring

```bash
# Follow live logs (Docker)
docker compose logs -f promotion-agent

# Check API health
curl http://localhost:5000/api/stats

# Check article inventory
curl http://localhost:5000/api/inventory
```

### Manual triggers

```bash
# Force an RSS check right now
docker compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().check_for_new_posts()"

# Regenerate dashboard JSON
docker compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().generate_review_dashboard()"

# Build / refresh article inventory
docker compose exec promotion-agent python agent.py --build-inventory

# Re-export article_inventory.md without API calls
docker compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().export_inventory_to_markdown()"
```

### Database queries

```bash
# Interactive SQL shell (no sqlite3 CLI required)
python db_shell.py
```

```sql
-- Pending promotions
SELECT posts.title, p.platform, p.created_date
FROM promotions p JOIN posts ON p.post_id = posts.id
WHERE p.status = 'pending_review';

-- Article inventory
SELECT title, topics, core_mechanism FROM article_inventory ORDER BY published_date DESC;
```

---

## Troubleshooting

**Agent not detecting posts**
- Make sure `SUBSTACK_URL` ends in `/feed`, not `/publish/home`
- Verify the feed works: `curl https://yourname.substack.com/feed` should return XML
- Check logs: `docker compose logs promotion-agent`

**Dashboard is empty after starting**
- The agent checks immediately on startup, but processing takes a moment. Refresh after 30 seconds.
- Or trigger manually: `docker compose exec promotion-agent python -c "from agent import PromotionAgent; PromotionAgent().check_for_new_posts()"`

**Dashboard asks for a username/password I didn't set**
- `DASHBOARD_USERNAME` and/or `DASHBOARD_PASSWORD` are set in your `.env`. Clear them (set both to empty or remove the lines) if you're running locally and don't want auth.

**"unable to open database file" on Windows/OneDrive**
- Right-click the project folder → "Always keep on this device"
- Or set `PROMOTION_AGENT_DB` in `.env` to a path outside OneDrive (e.g. `C:/Temp/promotion_agent.db`)
- Or run `python create_db.py` to create the database manually

**Inventory build fails or returns 0 articles**
- Confirm `SUBSTACK_URL` points to your real publication, not the placeholder
- Check API key credits at [console.anthropic.com](https://console.anthropic.com/)
- The build is idempotent — safe to retry

**Port 5000 already in use**
- Change the host port in `docker-compose.yml` (e.g. `"5001:5000"`) or stop the other process

**API key errors**
- Verify your key at [console.anthropic.com](https://console.anthropic.com/)

---

## Database Schema

SQLite (`promotion_agent.db`) with seven tables:

| Table | Contents |
|---|---|
| `posts` | All discovered blog posts from RSS feed |
| `promotions` | Generated promotional content per post |
| `weekly_tasks` | Monday on-ramp posts |
| `activity_log` | Commenting suggestions |
| `analytics_events` | Dashboard interaction tracking |
| `substack_profile` | Cached profile stats when `SUBSTACK_LINKEDIN_HANDLE` is set |
| `article_inventory` | All published articles: title, subtitle, URL, date, topics, core mechanism |

---

## Project Structure

```
promotion-agent/
├── agent.py              # Core agent: RSS monitor, AI extraction, scheduling
├── server.py             # Flask dashboard server and REST API
├── dashboard.html        # Single-page review interface
├── create_db.py          # Standalone DB initializer (run if agent hasn't run yet)
├── db_shell.py           # Interactive SQL shell
├── requirements.txt      # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── supervisord.conf      # Runs agent.py + server.py inside the container
├── .env.example          # Configuration template
├── .gitignore
├── article_inventory.md  # Auto-generated inventory export
├── README.md
├── DEPLOYMENT.md         # Cloud deployment guide (Railway, Render, Fly.io, etc.)
└── QUICK_REFERENCE.md    # Daily workflow cheat sheet
```

---

## Security

- Never commit `.env` — it is listed in `.gitignore`
- Your Anthropic API key gives billing access to your account; keep it secret
- **Set `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` for any deployment reachable from the internet.** Without them the dashboard and all API endpoints are publicly accessible to anyone with the URL.
- The dashboard has no rate limiting — use firewall rules or your cloud platform's access controls if you need additional protection

---

## Example Output

When you publish a post, the agent processes it and drafts everything for your review. Here's what that looks like for a post about leadership:

**Post:** "The Likability Tax on Technical Leadership"

**Extracted outward sentence** (the spine of the post, stands alone without context):
> "The likability tax isn't about interpersonal skills — it's about the cognitive load of managing others' comfort while making hard decisions."

**Platform routing:** LinkedIn (matched keywords: leadership, technical leadership, workplace, bias)

**Generated promotional post:**
```
The likability tax isn't about interpersonal skills — it's about
the cognitive load of managing others' comfort while making hard decisions.

For technical leaders, every "no" requires emotional labor. Every priority
call gets filtered through "will this make me seem difficult?" This creates
analysis paralysis and trains leaders to optimize for consensus over outcomes.

If you've felt this, you know how it compounds.

[link]
```

**Commenting suggestions:**
- Posts about engineering management transitions — add the nuance that the transition isn't just about new responsibilities; it's about learning to navigate the likability tax that comes with authority.
- Discussions of psychological safety — distinguish between safety and the expectation that leaders make everyone comfortable.

**Inventory entry** (auto-added, no action needed):
```
Topics:          leadership · women in tech · cognitive load · decision-making
Core mechanism:  Managing others' emotional comfort compounds into a
                 decision-making tax that slows technical leaders
```

Everything lands in the dashboard for review. You edit if needed, copy, paste, and mark done.

---

## Philosophy

Five principles that explain why the tool works the way it does:

1. **Content before chrome.** The promotional copy is the product. The interface is infrastructure. If a UI element isn't helping the writer evaluate or publish a draft, it has no reason to exist.
2. **Workflow, not performance.** Every decision — layout, spacing, interaction — exists to reduce friction in the review-edit-copy-publish loop. Nothing to impress; everything to accelerate.
3. **Writer voice.** The tool is an extension of the writer's creative process. It should feel like their notebook, not a SaaS dashboard.
4. **Calm clarity.** One section at a time, unambiguous state (pending, published, skipped), no urgency theater. The writer is already done with the hard work of publishing; this tool should feel like winding down, not ramping up.
5. **Personal scale.** Built for one person. Not scalable to a team, not designed to impress stakeholders.

The dashboard meets WCAG AA contrast requirements, is keyboard navigable, and respects `prefers-reduced-motion`.

---

## License

MIT — use freely, modify as needed, no warranty.

---

**Pro tip:** Review the first few generated promotional posts closely and edit them to match your voice. The patterns you establish inform future generations.
