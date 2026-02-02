# Cloud Deployment Guide

Detailed instructions for deploying the Blog Promotion Agent to various cloud platforms.

## Railway (Recommended - Easiest)

**Pros:** Free tier, automatic deployments, built-in domain, excellent for beginners
**Cons:** Database not persistent across deploys on free tier (use external DB for production)

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/rlSutter/Promotion-Agent/promotion-agent.git
   git push -u origin main
   ```

2. **Sign up for Railway**
   - Go to https://railway.app
   - Sign up with GitHub

3. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

4. **Configure Environment**
   - Click on your service
   - Go to "Variables" tab
   - Add variables:
     ```
     SUBSTACK_URL=https://yoursubstack.substack.com/feed
     ANTHROPIC_API_KEY=sk-ant-your-key-here
     CHECK_INTERVAL_MINUTES=60
     ```

5. **Configure Port**
   - Railway auto-detects port 5000
   - No action needed

6. **Deploy**
   - Railway automatically deploys
   - Wait for build to complete
   - Get your URL from "Settings" → "Domains"

7. **Access Dashboard**
   - Visit your Railway URL
   - Dashboard should be live

### Making It Persistent:

To keep your database across deploys:

1. Add Railway Postgres plugin
2. Update `agent.py` to use Postgres instead of SQLite
3. Or: Use Railway volumes (paid feature)

---

## Render

**Pros:** Free tier with persistent disk, PostgreSQL included
**Cons:** Apps sleep after 15 min of inactivity on free tier

### Steps:

1. **Push to GitHub** (same as Railway)

2. **Sign up for Render**
   - Go to https://render.com
   - Sign up with GitHub

3. **Create Web Service**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repo

4. **Configure Service**
   - Name: `promotion-agent`
   - Environment: `Docker`
   - Branch: `main`
   - Region: Choose closest to you

5. **Set Environment Variables**
   - Add variables:
     ```
     SUBSTACK_URL=https://yoursubstack.substack.com/feed
     ANTHROPIC_API_KEY=sk-ant-your-key-here
     ```

6. **Add Persistent Disk** (Important!)
   - Scroll to "Disk"
   - Click "Add Disk"
   - Name: `data`
   - Mount Path: `/app/data`
   - Size: 1GB (free tier)

7. **Update docker-compose.yml**
   ```yaml
   volumes:
     - /app/data:/app/data
   ```

8. **Deploy**
   - Click "Create Web Service"
   - Wait for build
   - Get URL from dashboard

### Keeping It Awake:

Free tier sleeps after 15 min. Options:

1. **Cron job to ping it:**
   ```bash
   # Add to crontab
   */10 * * * * curl https://your-app.onrender.com/api/stats
   ```

2. **Upgrade to paid tier** ($7/month, never sleeps)

---

## Fly.io

**Pros:** Great free tier, persistent volumes, runs anywhere
**Cons:** Requires CLI tool, more technical

### Steps:

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

3. **Create fly.toml**
   ```bash
   flyctl launch
   ```
   
   When prompted:
   - App name: `your-promotion-agent`
   - Region: Choose closest
   - PostgreSQL: No (we use SQLite)
   - Redis: No

4. **Edit fly.toml**
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

5. **Create Volume**
   ```bash
   flyctl volumes create data --size 1
   ```

6. **Set Secrets**
   ```bash
   flyctl secrets set SUBSTACK_URL="https://yoursubstack.substack.com/feed"
   flyctl secrets set ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```

7. **Deploy**
   ```bash
   flyctl deploy
   ```

8. **Access Dashboard**
   ```bash
   flyctl open
   ```

### Useful Commands:

```bash
# View logs
flyctl logs

# SSH into machine
flyctl ssh console

# Check status
flyctl status

# Scale (if needed)
flyctl scale memory 512
```

---

## Google Cloud Run

**Pros:** Only pay for actual usage, scales to zero
**Cons:** More complex setup, may need VPC for persistence

### Steps:

1. **Install gcloud CLI**
   - Follow: https://cloud.google.com/sdk/docs/install

2. **Authenticate**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build and Push Image**
   ```bash
   # Enable APIs
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com

   # Build
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/promotion-agent

   # Or use Docker
   docker build -t gcr.io/YOUR_PROJECT_ID/promotion-agent .
   docker push gcr.io/YOUR_PROJECT_ID/promotion-agent
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy promotion-agent \
     --image gcr.io/YOUR_PROJECT_ID/promotion-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars SUBSTACK_URL="https://yoursubstack.substack.com/feed" \
     --set-env-vars ANTHROPIC_API_KEY="sk-ant-your-key-here" \
     --min-instances 1 \
     --max-instances 1
   ```

5. **Add Persistent Disk** (Complex)
   - Cloud Run doesn't support volumes directly
   - Options:
     - Use Cloud SQL (PostgreSQL)
     - Use Cloud Firestore
     - Use mounted Cloud Storage bucket
     - Or accept ephemeral storage

6. **Access Dashboard**
   - URL provided after deploy
   - Format: `https://promotion-agent-xxxxx-uc.a.run.app`

---

## AWS (ECS Fargate)

**Pros:** Enterprise-grade, integrates with other AWS services
**Cons:** Most complex, more expensive

### High-Level Steps:

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name promotion-agent
   ```

2. **Build and Push Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag
   docker build -t promotion-agent .
   docker tag promotion-agent:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/promotion-agent:latest

   # Push
   docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/promotion-agent:latest
   ```

3. **Create ECS Cluster**
   - Use AWS Console or CLI
   - Select Fargate launch type

4. **Create Task Definition**
   - CPU: 256 (.25 vCPU)
   - Memory: 512 MB
   - Add environment variables
   - Add EFS volume for persistence

5. **Create Service**
   - Desired tasks: 1
   - Load balancer: Optional (for custom domain)

6. **Access Dashboard**
   - Through load balancer URL or task public IP

---

## Digital Ocean App Platform

**Pros:** Simple, good documentation, affordable
**Cons:** Less free tier than Railway/Render

### Steps:

1. **Push to GitHub**

2. **Create App**
   - Go to Digital Ocean
   - Apps → Create App
   - Connect GitHub repo

3. **Configure**
   - Dockerfile detected automatically
   - Set environment variables
   - Choose basic plan ($5/mo)

4. **Add Volume** (for persistence)
   - Under Resources
   - Add Volume
   - Mount path: `/app/data`

5. **Deploy**
   - Click "Create Resources"
   - Wait for deployment
   - Get URL from dashboard

---

## Comparison Matrix

| Platform | Free Tier | Persistent Storage | Ease of Use | Best For |
|----------|-----------|-------------------|-------------|----------|
| Railway | ✅ Yes | ⚠️ Paid only | ⭐⭐⭐⭐⭐ | Beginners |
| Render | ✅ Yes | ✅ Yes (1GB) | ⭐⭐⭐⭐ | Most users |
| Fly.io | ✅ Yes | ✅ Yes | ⭐⭐⭐ | Technical users |
| Cloud Run | ✅ Yes | ⚠️ Complex | ⭐⭐ | GCP users |
| ECS | ❌ No | ✅ Yes | ⭐ | Enterprise |
| Digital Ocean | ❌ No | ✅ Yes | ⭐⭐⭐⭐ | Simple paid option |

## Recommendations

**For beginners:** Railway
- Easiest setup
- Auto-deploys from GitHub
- Great free tier
- Just accept ephemeral DB or upgrade for $5/mo

**For serious use:** Render
- Free persistent disk
- Won't lose data
- Sleeps but wakes quickly
- Upgrade to $7/mo for always-on

**For technical users:** Fly.io
- Most control
- Global deployment
- Great CLI tools
- Persistent volumes free

**For existing cloud users:**
- GCP → Cloud Run
- AWS → ECS or Lambda
- Azure → Container Apps

## Post-Deployment Checklist

After deploying anywhere:

- [ ] Verify agent is running: Check logs
- [ ] Test RSS feed detection: Publish a test post
- [ ] Access dashboard: Visit URL
- [ ] Test API endpoints: `/api/stats`
- [ ] Set up monitoring: Health checks
- [ ] Configure custom domain (optional)
- [ ] Set up SSL/HTTPS (most platforms auto)
- [ ] Add to browser bookmarks
- [ ] Set phone reminder to check dashboard

## Troubleshooting

**Build fails:**
- Check Dockerfile syntax
- Verify requirements.txt
- Check logs for specific error

**Agent not detecting posts:**
- Verify SUBSTACK_URL is correct
- Check agent logs
- Test RSS feed manually: `curl $SUBSTACK_URL`

**Dashboard not loading:**
- Check if port 5000 is exposed
- Verify server.py is running
- Check firewall rules

**Database resets:**
- Platform doesn't have persistent storage
- Add volume/disk
- Or migrate to PostgreSQL

**Out of memory:**
- Increase memory allocation
- Default 256MB should be enough
- Check for memory leaks in logs

---

Need help? Check the troubleshooting section in README.md or review the platform-specific documentation.
