# DigitalOcean Deployment Guide - Consilo SaaS

**Complete step-by-step guide to deploy Consilo to production on DigitalOcean**

Estimated time: 45 minutes  
Cost: $27/month

---

## Prerequisites

- DigitalOcean account
- GitHub account (to connect your repo)
- Credit card for DigitalOcean billing

---

## Step 1: Push Code to GitHub (5 minutes)

### 1.1 Create GitHub Repository

```bash
# In your consilo-saas directory
git init
git add .
git commit -m "Initial commit - Consilo SaaS v1.0"
```

Go to GitHub → New Repository → Name it `consilo-saas` → Create

```bash
git remote add origin https://github.com/YOUR_USERNAME/consilo-saas.git
git push -u origin main
```

---

## Step 2: Create Managed PostgreSQL Database (10 minutes)

### 2.1 Navigate to Databases

1. Log into DigitalOcean
2. Click **Databases** in left sidebar
3. Click **Create Database Cluster**

### 2.2 Configure Database

- **Database Engine:** PostgreSQL
- **Version:** 15
- **Datacenter Region:** Choose closest to you (San Francisco - SFO3)
- **Size:** Development (1 GB RAM / 1 vCPU / 10 GB Disk) - $15/month
- **Name:** `consilo-db`

Click **Create Database Cluster**

⏱️ Wait 3-5 minutes for provisioning...

### 2.3 Configure Connection Security

1. Click **Settings** tab
2. Under **Trusted Sources**, add:
   - Your IP (for testing)
   - DigitalOcean App Platform (auto-added)

### 2.4 Get Connection String

1. Click **Connection Details**
2. Select **Connection String**
3. Copy the full string - looks like:
   ```
   postgresql://doadmin:XXXX@consilo-db-do-user-XXXX.ondigitalocean.com:25060/defaultdb?sslmode=require
   ```

**SAVE THIS - you'll need it in Step 3**

### 2.5 Create Consilo Database

```bash
# SSH into database (use connection string from above)
psql "postgresql://doadmin:XXXX@..."

# Create database
CREATE DATABASE consilo;
\q
```

Update your connection string to use `consilo` database instead of `defaultdb`:
```
postgresql://doadmin:XXXX@.../consilo?sslmode=require
```

---

## Step 3: Deploy Backend API (15 minutes)

### 3.1 Navigate to App Platform

1. Click **Apps** in left sidebar
2. Click **Create App**

### 3.2 Connect GitHub

1. Choose **GitHub**
2. Click **Authorize DigitalOcean**
3. Select your repository: `consilo-saas`
4. Select branch: `main`
5. Click **Next**

### 3.3 Configure Service

DigitalOcean will auto-detect your Dockerfile.

1. **Resource Type:** Web Service
2. **Name:** `consilo-api`
3. **Source Directory:** `/backend`
4. **Dockerfile Path:** `backend/Dockerfile`
5. **HTTP Port:** `8080`
6. **Instance Size:** Basic (512MB / $5/month)

Click **Next**

### 3.4 Add Environment Variables

Click **Edit** next to consilo-api → **Environment Variables**

Add these variables:

```bash
# Database (from Step 2.4)
DATABASE_URL=postgresql://doadmin:XXXX@consilo-db-do-user-XXXX.ondigitalocean.com:25060/consilo?sslmode=require

# Generate new encryption key
ENCRYPTION_KEY=<generate-new-key>

# CORS (we'll add frontend URL in Week 3)
CORS_ORIGINS=*
```

**To generate ENCRYPTION_KEY:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3.5 Review and Deploy

1. **App Name:** `consilo`
2. **Region:** Same as database (e.g., San Francisco)
3. **Plan:** Basic ($12/month)

Click **Create Resources**

⏱️ Wait 5-10 minutes for build and deployment...

### 3.6 Get Your API URL

Once deployed, you'll see:
```
https://consilo-xxxxx.ondigitalocean.app
```

**SAVE THIS URL**

### 3.7 Verify Deployment

```bash
curl https://consilo-xxxxx.ondigitalocean.app/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Consilo API",
  "version": "1.0.0"
}
```

✅ **Backend deployed successfully!**

---

## Step 4: Seed Database (5 minutes)

### 4.1 SSH into App

DigitalOcean doesn't give SSH access to App Platform directly.

Instead, use the **Console** feature:

1. Go to your app in DigitalOcean
2. Click on `consilo-api` component
3. Click **Console** tab
4. Click **Launch Console**

### 4.2 Run Seed Script

In the console:
```bash
cd /app
python seed.py
```

You should see:
```
🌱 Seeding database with initial data...
Created plan: Starter ($49.0/mo)
Created plan: Growth ($149.0/mo)
Created plan: Enterprise ($499.0/mo)

✅ Subscription plans seeded successfully!
```

---

## Step 5: Create Your First Tenant (5 minutes)

### 5.1 Get Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Name it "Consilo"
4. Copy the token

### 5.2 Create Tenant via API

```bash
curl -X POST https://consilo-xxxxx.ondigitalocean.app/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Your Company Name",
    "jira_url": "https://yourcompany.atlassian.net",
    "jira_email": "you@company.com",
    "jira_token": "ATATT3xFf...",
    "daily_rate_per_person": 2500
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "Your Company Name",
  "jira_url": "https://yourcompany.atlassian.net",
  "jira_email": "you@company.com",
  "plan": "starter",
  "status": "trial",
  "created_at": "2025-02-11T...",
  "monthly_issue_limit": 200,
  ...
}
```

**SAVE THE `id` - this is your X-Tenant-ID**

---

## Step 6: Test Production API (5 minutes)

### 6.1 Analyze an Issue

```bash
curl -X POST https://consilo-xxxxx.ondigitalocean.app/api/analyze/issue \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "issue_key": "ENG-123",
    "template": "executive"
  }'
```

### 6.2 Check Usage Stats

```bash
curl https://consilo-xxxxx.ondigitalocean.app/api/tenants/550e8400-e29b-41d4-a716-446655440000/usage
```

Response:
```json
{
  "tenant_id": "550e8400-...",
  "period": "2025-02",
  "issue_analyses": 1,
  "sprint_analyses": 0,
  "portfolio_analyses": 0,
  "total_calls": 1,
  "issue_limit": 200,
  "issue_remaining": 199,
  ...
}
```

✅ **Consilo is now live in production!**

---

## Step 7: Enable Auto-Deploy (2 minutes)

In DigitalOcean App Platform:

1. Go to your app
2. Click **Settings**
3. Under **App-Level Settings** → **Auto Deploy**
4. Enable **Auto Deploy**

Now every push to `main` branch will auto-deploy.

---

## Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| App Platform | Basic (512MB) | $12/month |
| Managed PostgreSQL | Development | $15/month |
| **Total** | | **$27/month** |

---

## Monitoring & Logs

### View Logs

1. Go to your app in DigitalOcean
2. Click on `consilo-api` component
3. Click **Runtime Logs** tab

### View Metrics

1. Click **Metrics** tab
2. See:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

---

## Troubleshooting

### App won't start

**Check logs:**
1. DigitalOcean → Your App → consilo-api → Runtime Logs
2. Look for error messages

**Common fixes:**
- Verify `DATABASE_URL` is correct
- Verify `ENCRYPTION_KEY` is set
- Check Dockerfile path is correct

### Database connection fails

**Check:**
1. Database is running (DigitalOcean → Databases)
2. Connection string is correct
3. SSL mode is enabled (`?sslmode=require`)

### API returns 500 errors

**Check:**
1. Runtime logs for stack trace
2. Database connection
3. Environment variables are set

### Out of memory errors

**Solution:**
Upgrade App Platform instance:
1. App Settings → Component Settings
2. Change size to **Professional** (1GB / $12/month)

---

## Scaling (Future)

When you get 100+ customers:

### Horizontal Scaling
- Increase **Instance Count** to 2-4 workers
- Cost: $12/worker/month

### Database Scaling
- Upgrade PostgreSQL to **Production** tier
- Cost: $60/month (4GB RAM, High Availability)

### Add Redis Cache
- For session management (Week 2)
- Cost: $15/month

---

## Security Checklist

- [ ] Change `ENCRYPTION_KEY` from example
- [ ] Database has SSL enabled (`sslmode=require`)
- [ ] Database connection limited to App Platform IP
- [ ] Environment variables stored securely (not in code)
- [ ] CORS origins restricted (add in Week 3)
- [ ] API docs disabled in production (set `docs_url=None` in main.py)

---

## Next Steps

✅ Week 1 Complete - Backend deployed to production!

**Week 2 Tasks:**
- Add Clerk.dev authentication
- Add Stripe billing
- Add webhook handlers
- Test payment flow

**Week 3 Tasks:**
- Deploy Next.js frontend
- Connect to this backend API
- Add authentication flow

---

## Support

If deployment fails:

1. **Check DigitalOcean Status:** https://status.digitalocean.com
2. **Review Build Logs:** App → Activity tab
3. **Check Docker Image:** Ensure Dockerfile builds locally
4. **Database Connectivity:** Test connection string with psql

---

**Deployment Complete!** 🚀

Your Consilo backend is now running in production on DigitalOcean.

API Endpoint: `https://consilo-xxxxx.ondigitalocean.app`
