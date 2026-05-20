# Deployment Guide

Step-by-step instructions for running the Blog Promotion Agent locally and deploying to cloud platforms.

> **Authentication note:** Any deployment reachable from the internet requires `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` to be set. Without them the dashboard is open to anyone with the URL. Local-only deployments can leave these blank.

---

## Local Deployment (Docker)

**Best for:** Personal use on your own machine, testing before cloud deploy.

**Pros:** No cloud account needed, full control, data stays on your machine, free  
**Cons:** Your computer must be on for the agent to run; no public URL by default

For a step-by-step verification checklist see [DOCKER_DEPLOYMENT_PLAN.md](DOCKER_DEPLOYMENT_PLAN.md).

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — includes Docker and Docker Compose
  - Windows: enable WSL 2 if prompted during install
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com/)
- Your Substack RSS feed URL (e.g. `https://yourname.substack.com/feed`)

### Steps

1. **Clone the repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/promotion-agent.git
   cd promotion-agent
   ```

2. **Create your config file**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   SUBSTACK_URL=https://yourname.substack.com/feed
   ANTHROPIC_API_KEY=sk-ant-api03-...
   # Leave DASHBOARD_USERNAME / DASHBOARD_PASSWORD blank for local use
   ```

3. **Start the agent**
   ```powershell
   docker-compose up -d
   ```
   The first run builds the Docker image (a few minutes), then starts the agent and dashboard server.  
   Dashboard: **http://localhost:5000**

4. **Build the article inventory** (one-time, for historical posts)
   - Click **🔨 Build / Refresh Inventory** in the Article Inventory section, **or**
   ```bash
   docker compose exec promotion-agent python agent.py --build-inventory
   ```
   Cost: ~$0.05–0.15 depending on back-catalog size. Idempotent — safe to re-run.

5. **Run in foreground** (useful for watching startup logs)
   ```powershell
   docker-compose up
   ```
   Stop with **Ctrl+C**, then use `docker-compose up -d` for background mode.

### Useful commands

| Command | Purpose |
|--------|--------|
| `docker-compose logs -f promotion-agent` | Follow live logs |
| `docker-compose ps` | Check container status |
| `docker-compose down` | Stop and remove container |
| `docker-compose up -d --build` | Rebuild image after code changes |
| `curl http://localhost:5000/api/stats` | Check API health |

### Data persistence

These files are mounted from your project folder so data survives container restarts:

- `./promotion_agent.db` — SQLite database
- `./review_dashboard.json` — Dashboard state
- `./article_inventory.md` — Exported inventory

Do not commit `.env`; it is in `.gitignore`.

---

## Railway (Recommended for Cloud)

**Pros:** Free tier, automatic deploys from GitHub, built-in HTTPS domain, easy setup  
**Cons:** SQLite database is not persistent across deploys on free tier (use volumes on paid tier)

### Steps

1. **Fork and push to GitHub**
   - Fork this repo to your own GitHub account
   - Or push your local copy:
     ```bash
     git remote add origin https://github.com/YOUR_USERNAME/promotion-agent.git
     git push -u origin main
     ```

2. **Sign up for Railway** at [railway.app](https://railway.app) using GitHub

3. **Create a new project**
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your fork

4. **Add environment variables**
   - Click your service → **Variables** tab
   - Add all required variables:
     ```
     SUBSTACK_URL=https://yourname.substack.com/feed
     ANTHROPIC_API_KEY=sk-ant-api03-...
     DASHBOARD_USERNAME=admin
     DASHBOARD_PASSWORD=choose-a-strong-password
     CHECK_INTERVAL_MINUTES=60
     ```

5. **Deploy** — Railway builds and deploys automatically. Get your URL from **Settings → Domains**.

6. **Build article inventory** — Open your Railway URL and click **🔨 Build / Refresh Inventory**.

### Making the database persistent

SQLite data is lost on each redeploy unless you use a volume:

- **Paid plan:** Add a Railway volume and set `PROMOTION_AGENT_DB=/data/promotion_agent.db`
- **Free plan:** Accept that you'll rebuild the inventory after each deploy, or migrate to PostgreSQL

---

## Render

**Pros:** Free tier with 1 GB persistent disk, no data loss  
**Cons:** Free tier sleeps after 15 min of inactivity

### Steps

1. **Fork and push to GitHub** (same as Railway step 1)

2. **Sign up for Render** at [render.com](https://render.com) using GitHub

3. **Create a Web Service**
   - Click **New +** → **Web Service**
   - Connect your GitHub repo
   - Set:
     - Environment: **Docker**
     - Branch: **main**
     - Region: closest to you

4. **Add environment variables**
   ```
   SUBSTACK_URL=https://yourname.substack.com/feed
   ANTHROPIC_API_KEY=sk-ant-api03-...
   DASHBOARD_USERNAME=admin
   DASHBOARD_PASSWORD=choose-a-strong-password
   ```

5. **Add a persistent disk**
   - Scroll to **Disk** → **Add Disk**
   - Name: `data`, Mount path: `/app/data`, Size: 1 GB

6. **Deploy** — click **Create Web Service**. Your URL appears in the dashboard.

7. **Build article inventory** — Open your Render URL and click **🔨 Build / Refresh Inventory**.

### Keeping it awake on the free tier

The free tier sleeps after 15 minutes of inactivity. Options:

- Add a cron job (from any server or service) to ping the health endpoint every 10 minutes:
  ```
  */10 * * * * curl -s https://your-app.onrender.com/api/stats
  ```
- Upgrade to the paid tier ($7/month) for always-on

---

## Fly.io

**Pros:** Generous free tier, persistent volumes, global regions, full CLI control  
**Cons:** Requires the `flyctl` CLI; more setup steps than Railway/Render

### Steps

1. **Install flyctl**
   ```bash
   # Mac
   brew install flyctl

   # Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Sign up**
   ```bash
   flyctl auth signup
   ```

3. **Initialize the app**
   ```bash
   flyctl launch
   ```
   When prompted: pick an app name and region; answer No to PostgreSQL and Redis.

4. **Edit `fly.toml`**
   ```toml
   app = "your-promotion-agent"
   primary_region = "sjc"

   [build]

   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true
     min_machines_running = 1

   [[vm]]
     cpu_kind = "shared"
     cpus = 1
     memory_mb = 256

   [mounts]
     source = "data"
     destination = "/app/data"
   ```

5. **Create a persistent volume**
   ```bash
   flyctl volumes create data --size 1
   ```

6. **Set secrets** (never put these in `fly.toml` or source control)
   ```bash
   flyctl secrets set SUBSTACK_URL="https://yourname.substack.com/feed"
   flyctl secrets set ANTHROPIC_API_KEY="sk-ant-api03-..."
   flyctl secrets set DASHBOARD_USERNAME="admin"
   flyctl secrets set DASHBOARD_PASSWORD="choose-a-strong-password"
   ```

7. **Deploy**
   ```bash
   flyctl deploy
   ```

8. **Open the dashboard**
   ```bash
   flyctl open
   ```

9. **Build article inventory** — click **🔨 Build / Refresh Inventory** in the dashboard.

### Useful Fly.io commands

```bash
flyctl logs          # View logs
flyctl status        # Check machine status
flyctl ssh console   # SSH into the machine
flyctl scale memory 512  # Increase memory if needed
```

---

## Google Cloud Run

**Pros:** Pay-per-use, scales to zero  
**Cons:** No built-in persistent storage; requires more configuration

### Steps

1. **Install and authenticate gcloud CLI**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable APIs and build image**
   ```bash
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/promotion-agent
   ```

3. **Deploy**
   ```bash
   gcloud run deploy promotion-agent \
     --image gcr.io/YOUR_PROJECT_ID/promotion-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars SUBSTACK_URL="https://yourname.substack.com/feed" \
     --set-env-vars ANTHROPIC_API_KEY="sk-ant-api03-..." \
     --set-env-vars DASHBOARD_USERNAME="admin" \
     --set-env-vars DASHBOARD_PASSWORD="choose-a-strong-password" \
     --min-instances 1 \
     --max-instances 1
   ```

4. **Add persistent storage** — Cloud Run does not support volumes natively. Options:
   - Use Cloud SQL (PostgreSQL) and update `agent.py`
   - Mount a Cloud Storage bucket via Cloud Run's volume mounting (preview feature)
   - Accept ephemeral storage and rebuild the inventory after each deploy

---

## AWS ECS Fargate

**Pros:** Enterprise-grade  
**Cons:** Most complex, higher cost

High-level steps:
1. Create an ECR repository and push your Docker image
2. Create an ECS cluster (Fargate launch type)
3. Define a task with 256 CPU / 512 MB memory, environment variables, and an EFS volume for persistence
4. Create a service (desired count: 1)
5. Access via load balancer URL or the task's public IP

---

## DigitalOcean App Platform

**Pros:** Simple UI, affordable  
**Cons:** Smaller free tier than Railway/Render

### Steps

1. Fork/push to GitHub
2. **Create App** in the DigitalOcean control panel → connect your repo
3. DigitalOcean detects the Dockerfile automatically
4. Add environment variables including `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`
5. Add a volume under Resources → Add Volume → mount path `/app/data`
6. Deploy (basic plan ~$5/mo)

---

## Platform Comparison

| Platform | Free Tier | Persistent Storage | Auth Required | Ease of Setup |
|---|---|---|---|---|
| **Local (Docker)** | ✅ | ✅ host disk | ❌ (local only) | ⭐⭐⭐⭐⭐ |
| Railway | ✅ | ⚠️ paid only | ✅ | ⭐⭐⭐⭐⭐ |
| Render | ✅ | ✅ 1 GB free | ✅ | ⭐⭐⭐⭐ |
| Fly.io | ✅ | ✅ | ✅ | ⭐⭐⭐ |
| Cloud Run | ✅ | ⚠️ complex | ✅ | ⭐⭐ |
| ECS Fargate | ❌ | ✅ | ✅ | ⭐ |
| DigitalOcean | ❌ | ✅ | ✅ | ⭐⭐⭐⭐ |

**Recommendations:**
- **Testing / personal use:** Local Docker — no cloud account, data stays on your machine
- **First cloud deployment:** Railway — easiest, auto-deploys from GitHub
- **Serious / persistent use:** Render — free persistent disk, reliable uptime on paid tier
- **Technical users who want control:** Fly.io — persistent volumes on free tier, global regions

---

## Post-Deployment Checklist

After deploying to any platform:

- [ ] Dashboard loads at your URL
- [ ] `/api/stats` returns JSON (confirms server + database are working)
- [ ] Login prompt appears if `DASHBOARD_USERNAME`/`DASHBOARD_PASSWORD` are set
- [ ] Agent logs show "Checking for new posts" (no crash loop)
- [ ] Build article inventory: click **🔨 Build / Refresh Inventory**
- [ ] `/api/inventory` returns your articles
- [ ] Publish a test post and confirm it appears in Pending Promotions within 1 hour

---

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Build fails | Check Dockerfile syntax and that `agent.py`, `server.py`, `dashboard.html`, `supervisord.conf`, `.env.example` all exist |
| Container exits immediately | Run `docker-compose up` (no `-d`) to see the full error; most common cause is a missing or invalid env variable |
| Port 5000 in use | Change the host port in `docker-compose.yml` to e.g. `"5001:5000"` |
| Dashboard returns 502 | Wait 15–20 s after start for the server to initialise; check logs |
| Dashboard asks for credentials I didn't set | `DASHBOARD_USERNAME` or `DASHBOARD_PASSWORD` is set in `.env` — remove or clear both to disable auth |
| Agent not detecting posts | Confirm `SUBSTACK_URL` ends in `/feed`; test with `curl $SUBSTACK_URL` |
| Inventory build returns 0 articles | Confirm `SUBSTACK_URL` is your real publication; check Anthropic API key has credits |
| Database resets on redeploy | Platform has no persistent storage — add a volume or set `PROMOTION_AGENT_DB` to a mounted path |

---

For day-to-day usage see [QUICK_REFERENCE.md](QUICK_REFERENCE.md). For a full step-by-step Docker verification checklist see [DOCKER_DEPLOYMENT_PLAN.md](DOCKER_DEPLOYMENT_PLAN.md).
