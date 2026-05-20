# Docker Deployment and Verification Plan

Step-by-step plan to deploy the Promotion Agent in Docker and confirm it is running correctly.

---

## Phase 1: Prerequisites

- [ ] **Docker Desktop** installed and running  
  - Windows: [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) (WSL 2 if prompted)  
  - Mac: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- [ ] **Project** on disk (cloned or extracted) with `.env` configured
- [ ] **`.env`** in project root with:
  - `SUBSTACK_URL=https://yoursubstack.substack.com/feed`
  - `ANTHROPIC_API_KEY=sk-ant-...`
  - Optional: `CHECK_INTERVAL_MINUTES=60`
  - **For cloud / shared deployments:** `DASHBOARD_USERNAME=admin` and `DASHBOARD_PASSWORD=your-password`

---

## Phase 2: Build and Run

1. **Open a terminal** in the project folder:
   ```powershell
   cd "C:\Users\hciadmin\OneDrive - educritical.com\Programming\Promotion Agent"
   ```
   (Use your actual path.)

2. **Build the image** (first time or after code changes):
   ```powershell
   docker-compose build
   ```
   - Expect: "Successfully built" and "Successfully tagged".
   - If build fails: fix reported errors (e.g. missing files, Dockerfile syntax).

3. **Start the stack** (detached):
   ```powershell
   docker-compose up -d
   ```
   - Expect: "Container promotion-agent Started" (or "Created" then "Started").

4. **Optional – run in foreground** to watch logs:
   ```powershell
   docker-compose up
   ```
   - Stop with **Ctrl+C** when done; use `docker-compose up -d` again for background.

---

## Phase 3: Verification

### 3.1 Container is running

- [ ] **List containers:**
  ```powershell
  docker-compose ps
  ```
  - Expect: `promotion-agent` with state **Up** and port `0.0.0.0:5000->5000/tcp`.

- [ ] **Inspect once** (optional):
  ```powershell
  docker inspect promotion-agent --format "{{.State.Status}}"
  ```
  - Expect: `running`.

### 3.2 Dashboard is reachable

- [ ] **Open in browser:** [http://localhost:5000](http://localhost:5000)  
  - Expect: Promotion Agent dashboard with six collapsible sections (Analytics, Pending Promotions, Commenting Tasks, Weekly Tasks, Article Inventory, Archive).

- [ ] **Dashboard JSON** (optional):  
  [http://localhost:5000/review_dashboard.json](http://localhost:5000/review_dashboard.json)  
  - Expect: JSON with `generated_at`, `pending_promotions`, `commenting_suggestions`, `weekly_tasks` (can be empty at first).

### 3.3 API health

- [ ] **Stats endpoint:**
  ```powershell
  curl http://localhost:5000/api/stats
  ```
  - Expect: JSON like `{"total_posts": ..., "promotions": {...}, "recent_activity": {...}}`.  
  - Status 200; numbers can be zero before any posts are processed.

- [ ] **Inventory endpoint:**
  ```powershell
  curl http://localhost:5000/api/inventory
  ```
  - Expect: JSON like `{"items": [], "count": 0}` before the inventory build; populated after the build.

### 3.4 Logs (agent and server)

- [ ] **Follow logs:**
  ```powershell
  docker-compose logs -f promotion-agent
  ```
  - Expect: Lines from both agent and server (e.g. "Promotion Agent Started", "Monitoring: …", "Checking for new posts…", "Running on http://…").  
  - Stop with **Ctrl+C**.

- [ ] **Last 50 lines** (no follow):
  ```powershell
  docker-compose logs --tail=50 promotion-agent
  ```
  - Use to confirm no repeated errors or crashes.

### 3.5 Healthcheck (if configured)

- [ ] **Container health** (Docker reports it when healthcheck is defined):
  ```powershell
  docker inspect promotion-agent --format "{{.State.Health.Status}}"
  ```
  - Expect: `healthy` after the start period (e.g. 10–30 seconds).  
  - If `unhealthy`: check logs and that `http://localhost:5000/api/stats` returns 200 from the host.

### 3.6 Data persistence (after first run)

- [ ] **Project folder** should contain (or container will create via mounts):
  - `./data/` (directory)
  - `./promotion_agent.db` (SQLite DB; created when agent runs)
  - `./review_dashboard.json` (created when agent generates dashboard)
  - `./article_inventory.md` (created after the inventory build; auto-updated on new posts)
- [ ] **Restart and re-check:**  
  `docker-compose restart promotion-agent` then open [http://localhost:5000](http://localhost:5000) again and confirm dashboard still loads (and stats if you had any).

---

## Phase 4: Build Article Inventory (one-time)

After confirming the agent is running correctly, populate your full article back-catalog.

**Via dashboard (easiest):**
- Open [http://localhost:5000](http://localhost:5000)
- Scroll to the 📚 Article Inventory section
- Click **"🔨 Build / Refresh Inventory"**
- Watch the status message — build runs in the background
- When complete, the table populates with all your articles

**Via command line:**
```powershell
docker compose exec promotion-agent python agent.py --build-inventory
```

**Expected outcome:**
- All published articles appear in the inventory table
- `article_inventory.md` created in project folder
- `/api/inventory` returns all articles with topics and core mechanism summaries

**Notes:**
- Cost: ~$0.05–0.15 depending on back-catalog size
- The build is idempotent — re-running skips articles already in the inventory
- New articles are added automatically as the agent processes each new post

---

## Phase 5: Quick verification checklist

| Check | Command or action | Expected |
|-------|-------------------|----------|
| Container up | `docker-compose ps` | `promotion-agent` **Up** |
| Dashboard | Open http://localhost:5000 | Dashboard with 6 sections loads |
| API | `curl http://localhost:5000/api/stats` | JSON, HTTP 200 |
| Inventory API | `curl http://localhost:5000/api/inventory` | JSON with items array |
| Logs | `docker-compose logs --tail=30 promotion-agent` | No crash loop; "Monitoring" / "Checking for new posts" |
| Inventory file | Check project folder for `article_inventory.md` | File exists after build |

---

## Phase 6: Troubleshooting

| Symptom | What to do |
|--------|------------|
| Build fails | Fix Dockerfile/requirements; ensure all copied files exist (e.g. `agent.py`, `server.py`, `dashboard.html`, `supervisord.conf`, `.env.example`). |
| Container exits immediately | Run `docker-compose up` (no `-d`) and read the traceback; fix missing env (e.g. `ANTHROPIC_API_KEY`) or Python errors. |
| Port 5000 in use | Change host port in `docker-compose.yml` (e.g. `"5001:5000"`) or stop the other process using 5000. |
| Dashboard 502 / connection refused | Wait 10–20 s after start; check `docker-compose logs` for server errors; ensure port mapping is `5000:5000`. |
| `/api/stats` 500 | Often DB or tables missing; ensure container has write access to mounted volume (e.g. `./data`, `./promotion_agent.db`). On Windows/OneDrive, see DEPLOYMENT.md for optional temp DB path. |
| Agent not processing posts | Confirm `SUBSTACK_URL` in `.env` is the **feed** URL (e.g. `https://yoursubstack.substack.com/feed`); check logs for API (e.g. Anthropic) errors; ensure API key has credits. |
| Dashboard prompts for login unexpectedly | `DASHBOARD_USERNAME` or `DASHBOARD_PASSWORD` is set in `.env`. Clear both to disable auth for local use. |
| Inventory build fails | Confirm `SUBSTACK_URL` is your real Substack URL (not the placeholder). Check logs. Re-run — it's idempotent. |
| Inventory shows 0 articles after build | Check that `SUBSTACK_URL` resolves to an active publication; check logs for API errors; verify Anthropic API key has credits. |

---

## Phase 7: Stop and remove (optional)

- **Stop containers:**
  ```powershell
  docker-compose down
  ```
- **Remove containers and image** (clean slate):
  ```powershell
  docker-compose down
  docker rmi promotionagent-promotion-agent 2>$null; docker-compose build --no-cache
  ```
  (Image name may vary; use `docker images` to confirm.)

---

## Summary

1. **Prerequisites:** Docker Desktop, `.env` with `SUBSTACK_URL` and `ANTHROPIC_API_KEY`.  
2. **Deploy:** `docker-compose build` then `docker-compose up -d`.  
3. **Verify:** Container up → http://localhost:5000 loads with 6 sections → `curl http://localhost:5000/api/stats` returns JSON → logs show agent and server running without crash loops.  
4. **Build inventory:** Click "🔨 Build / Refresh Inventory" in the Article Inventory section (one-time; auto-updates on new posts thereafter).  
5. **Ongoing:** Use `docker-compose logs -f promotion-agent` and the dashboard to confirm new posts are processed once the agent has run and Anthropic API has sufficient credits.

For cloud deployment (Railway, Render, Fly.io, etc.), see **DEPLOYMENT.md**.
