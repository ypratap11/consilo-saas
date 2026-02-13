# Consilo Quick Start - 30 Minutes to Running

**Goal:** Get Consilo running locally in 30 minutes

---

## Prerequisites (5 minutes)
- Docker installed
- Jira account with API access
- Terminal/command line

---

## Step 1: Setup (5 minutes)

```bash
# Navigate to consilo-saas directory
cd consilo-saas

# Copy environment template
cp .env.example .env

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env:
# ENCRYPTION_KEY=<paste-output-here>
```

---

## Step 2: Start Services (10 minutes)

```bash
# Start Docker Compose
docker-compose up -d

# Wait ~2 minutes for services to start

# Check health
curl http://localhost:8080/health

# Expected: {"status": "healthy", ...}
```

---

## Step 3: Create Tenant (5 minutes)

Get Jira API token:
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy token

Create tenant:
```bash
curl -X POST http://localhost:8080/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "My Company",
    "jira_url": "https://mycompany.atlassian.net",
    "jira_email": "me@company.com",
    "jira_token": "ATATT3xFf...",
    "daily_rate_per_person": 2500
  }'
```

**Save the `id` from response - this is your tenant ID**

---

## Step 4: Analyze Issue (5 minutes)

```bash
curl -X POST http://localhost:8080/api/analyze/issue \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <your-tenant-id>" \
  -d '{
    "issue_key": "ENG-123",
    "template": "executive"
  }'
```

---

## Step 5: Explore API (5 minutes)

Open in browser: http://localhost:8080/docs

This is interactive API documentation where you can:
- See all endpoints
- Try them out directly
- View request/response schemas

---

## Done! 🎉

You now have Consilo running locally.

**Next steps:**
1. Read full README.md
2. Run test suite: `python test_local.py`
3. Deploy to production (see DEPLOYMENT.md)

---

## Common Issues

**"Connection refused"**
→ Docker not started: `docker-compose up -d`

**"Database connection failed"**
→ Wait 30 seconds for PostgreSQL: `docker-compose logs postgres`

**"FinBERT download slow"**
→ First analysis downloads 500MB model (one-time, ~5 minutes)

**"Invalid credentials"**
→ Check Jira URL has no trailing slash
→ Verify API token is correct

---

## Quick Commands

```bash
# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Restart fresh
docker-compose down -v && docker-compose up -d

# Access database
docker exec -it consilo-db psql -U consilo -d consilo
```

---

## What You Just Built

✅ Multi-tenant SaaS backend  
✅ AI-powered Jira analysis  
✅ Usage tracking  
✅ Historical trends  
✅ RESTful API  
✅ PostgreSQL database  

**Total time:** 30 minutes  
**Total cost (local):** $0  
**Production cost:** $27/month on DigitalOcean  

---

**Ready for production?** See DEPLOYMENT.md
