# Week 1 Execution Checklist - Consilo SaaS

**Goal:** Deploy production-ready multi-tenant backend to DigitalOcean by Day 7

Total time investment: 12-15 hours over 7 days (~2 hours/day)

---

## Day 1-2: Setup & Local Development (4 hours)

### Day 1 Morning (2 hours)
- [ ] Review complete codebase structure
- [ ] Read README.md thoroughly
- [ ] Install Docker Desktop
- [ ] Clone/download Consilo code
- [ ] Copy `.env.example` to `.env`
- [ ] Generate encryption key:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] Add encryption key to `.env`

### Day 1 Afternoon (2 hours)
- [ ] Start Docker Compose:
  ```bash
  docker-compose up -d
  ```
- [ ] Verify PostgreSQL is running:
  ```bash
  docker ps
  ```
- [ ] Verify API is running:
  ```bash
  curl http://localhost:8080/health
  ```
- [ ] Run local tests:
  ```bash
  python test_local.py
  ```

### Day 2 Morning (2 hours)
- [ ] Get Jira API token from Atlassian
- [ ] Create first tenant via API
- [ ] Save tenant ID
- [ ] Test issue analysis with real Jira issue
- [ ] Test sprint analysis
- [ ] Verify usage tracking works

### Day 2 Afternoon (2 hours)
- [ ] Review database schema
- [ ] Connect to local PostgreSQL:
  ```bash
  docker exec -it consilo-db psql -U consilo -d consilo
  ```
- [ ] Inspect tenant table: `SELECT * FROM tenants;`
- [ ] Inspect usage_logs: `SELECT * FROM usage_logs;`
- [ ] Verify data is being stored correctly
- [ ] Test all API endpoints via Swagger docs (http://localhost:8080/docs)

---

## Day 3-4: Production Setup (4 hours)

### Day 3 Morning (2 hours)
- [ ] Create DigitalOcean account (if needed)
- [ ] Add payment method
- [ ] Create PostgreSQL managed database
  - Size: Development (1GB RAM) - $15/month
  - Region: Choose closest to you
  - Name: consilo-db
- [ ] Wait for database provisioning (~5 minutes)
- [ ] Copy connection string
- [ ] Test connection locally:
  ```bash
  psql "postgresql://..."
  CREATE DATABASE consilo;
  ```

### Day 3 Afternoon (2 hours)
- [ ] Create GitHub repository
- [ ] Push Consilo code to GitHub:
  ```bash
  git init
  git add .
  git commit -m "Initial commit - Consilo v1.0"
  git remote add origin https://github.com/YOUR_USERNAME/consilo-saas.git
  git push -u origin main
  ```
- [ ] Verify code is on GitHub
- [ ] Review DEPLOYMENT.md guide

### Day 4 Morning (2 hours)
- [ ] Create App Platform app in DigitalOcean
- [ ] Connect to GitHub repo
- [ ] Configure web service:
  - Name: consilo-api
  - Port: 8080
  - Instance: Basic (512MB) - $12/month
- [ ] Add environment variables:
  - DATABASE_URL (from Day 3)
  - ENCRYPTION_KEY (generate new one for prod)
  - CORS_ORIGINS=*
- [ ] Review and deploy

### Day 4 Afternoon (2 hours)
- [ ] Wait for deployment to complete (~10 minutes)
- [ ] Get production API URL
- [ ] Test health endpoint:
  ```bash
  curl https://consilo-xxxxx.ondigitalocean.app/health
  ```
- [ ] Seed database with subscription plans:
  - Use App Console in DigitalOcean
  - Run: `python seed.py`
- [ ] Verify plans were created

---

## Day 5: Production Testing (2 hours)

### Day 5 Morning (1 hour)
- [ ] Create production tenant via API
- [ ] Save production tenant ID
- [ ] Test issue analysis in production
- [ ] Verify analysis is stored in database
- [ ] Check usage logs are being created

### Day 5 Afternoon (1 hour)
- [ ] Test all endpoints in production:
  - [ ] POST /api/tenants
  - [ ] GET /api/tenants/{id}
  - [ ] GET /api/tenants/{id}/usage
  - [ ] POST /api/analyze/issue
  - [ ] GET /api/analyze/issue/{key}/raw
  - [ ] GET /api/analyze/history/{key}
- [ ] Document any issues found
- [ ] Test usage limits enforcement

---

## Day 6: Monitoring & Documentation (2 hours)

### Day 6 Morning (1 hour)
- [ ] Review DigitalOcean metrics:
  - CPU usage
  - Memory usage
  - Request count
- [ ] Review runtime logs
- [ ] Set up log alerts (optional)
- [ ] Test error handling:
  - Invalid tenant ID
  - Invalid issue key
  - Exceeded usage limits

### Day 6 Afternoon (1 hour)
- [ ] Document your Jira custom fields (if any)
- [ ] Create internal docs:
  - API endpoints
  - Environment variables
  - Database schema
- [ ] Test disaster recovery:
  - Database backup
  - App redeployment
- [ ] Enable auto-deploy on GitHub push

---

## Day 7: Polish & Handoff Prep (2 hours)

### Day 7 Morning (1 hour)
- [ ] Perform full end-to-end test:
  - Create tenant
  - Analyze 10 issues
  - Analyze sprint
  - Check usage stats
  - Verify history storage
- [ ] Stress test:
  - Analyze 20 issues rapidly
  - Check performance metrics
- [ ] Document any performance bottlenecks

### Day 7 Afternoon (1 hour)
- [ ] Clean up test data (optional)
- [ ] Review all checklist items
- [ ] Update README with production URLs
- [ ] Take screenshots for portfolio
- [ ] Celebrate Week 1 completion! 🎉

---

## Week 1 Success Criteria

At end of Week 1, you should have:

✅ **Working local development environment**
- Docker Compose running
- PostgreSQL database
- All tests passing

✅ **Production deployment on DigitalOcean**
- Backend API running
- Managed PostgreSQL database
- Health endpoint responding

✅ **Multi-tenant functionality**
- Can create tenants
- Credentials encrypted
- Usage tracking works

✅ **Core analysis features**
- Issue analysis working
- Sprint analysis working
- Results stored in history

✅ **Monitoring & logs**
- Can view runtime logs
- Can check metrics
- Errors are logged

✅ **Documentation**
- README complete
- DEPLOYMENT guide complete
- Environment variables documented

---

## Common Issues & Solutions

### Docker won't start
**Solution:**
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Database connection fails
**Check:**
- DATABASE_URL is correct
- SSL mode enabled (`?sslmode=require`)
- Database is running
- Trusted sources configured

### DigitalOcean build fails
**Check:**
- Dockerfile path is correct
- requirements.txt has all dependencies
- Environment variables are set
- GitHub repo is accessible

### Analysis takes too long
**Expected:**
- First analysis: 30-60 seconds (FinBERT downloads)
- Subsequent: 5-10 seconds
- If slower: upgrade instance size

### Out of memory
**Solution:**
Upgrade App Platform to Professional (1GB):
- DigitalOcean → Your App → Settings
- Component Settings → Size → Professional
- Cost: $12/month → $24/month

---

## Time Tracking

Track your actual time spent:

| Day | Planned | Actual | Notes |
|-----|---------|--------|-------|
| 1 | 2h | | |
| 2 | 2h | | |
| 3 | 2h | | |
| 4 | 2h | | |
| 5 | 2h | | |
| 6 | 2h | | |
| 7 | 2h | | |
| **Total** | **14h** | | |

---

## Week 1 Complete! 🚀

**What you built:**
- Production-ready multi-tenant SaaS backend
- AI-powered Jira analysis engine
- Usage tracking for billing
- Historical trend storage
- Deployed to DigitalOcean cloud
- Monitoring and logging

**Ready for Week 2:**
- Clerk.dev authentication
- Stripe billing integration
- Subscription plan enforcement
- Webhook handlers

**Current MRR:** $0  
**Target after Week 2:** $490 (10 beta customers @ $49/month)  
**Target after Month 3:** $2,450 (50 customers)

---

## Questions to Answer Before Week 2

- [ ] What's your target customer? (CTO, PM, Director)
- [ ] What problem are you solving for them?
- [ ] What's your elevator pitch?
- [ ] What makes Consilo different from Jira dashboards?
- [ ] What's your pricing strategy reasoning?

Write these down - you'll need them for landing page (Week 4).

---

**Week 1 Status:** ⬜ In Progress → ✅ Complete

Next: Week 2 - Authentication & Billing
