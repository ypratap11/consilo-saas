# Consilo SaaS - Production Backend

**AI-Powered Delivery Risk Intelligence for Engineering Teams**

Complete multi-tenant SaaS backend built in Week 1 of the 30-day execution plan.

## 🏗️ Architecture

```
Frontend (Next.js - Week 3)
        ↓
FastAPI Backend ← You are here
        ↓
PostgreSQL (DigitalOcean Managed DB)
        ↓
Jira API + FinBERT AI
```

## 📦 What's Included (Week 1)

✅ Multi-tenant architecture with encrypted credentials  
✅ PostgreSQL database with SQLAlchemy ORM  
✅ Consilo analysis engine (adapted from your original code)  
✅ Sprint & portfolio aggregation  
✅ Usage tracking for billing  
✅ Analysis history for trend charts  
✅ RESTful API with FastAPI  
✅ Docker containerization  
✅ Ready for DigitalOcean deployment

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local testing without Docker)
- PostgreSQL (auto-installed via Docker Compose)

### 1. Clone and Setup

```bash
cd consilo-saas
cp .env.example .env
```

### 2. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and add to `.env`:
```
ENCRYPTION_KEY=gAAAAABl...your-key-here
```

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL on `localhost:5432`
- Consilo API on `localhost:8080`

### 4. Verify Health

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Consilo API",
  "version": "1.0.0"
}
```

### 5. Create Your First Tenant

```bash
curl -X POST http://localhost:8080/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Your Company",
    "jira_url": "https://yourcompany.atlassian.net",
    "jira_email": "you@company.com",
    "jira_token": "your-jira-api-token",
    "daily_rate_per_person": 2500
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "Your Company",
  ...
}
```

**Save the `id` - this is your `X-Tenant-ID` for all future requests.**

### 6. Analyze Your First Issue

```bash
curl -X POST http://localhost:8080/api/analyze/issue \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "issue_key": "ENG-123",
    "template": "executive"
  }'
```

## 📡 API Endpoints

### Tenant Management
- `POST /api/tenants` - Create tenant
- `GET /api/tenants/{tenant_id}` - Get tenant info
- `PUT /api/tenants/{tenant_id}` - Update tenant
- `GET /api/tenants/{tenant_id}/usage` - Get usage stats

### Analysis
- `POST /api/analyze/issue` - Analyze single issue
- `GET /api/analyze/issue/{issue_key}/raw` - Get raw analysis (JSON)
- `POST /api/analyze/sprint` - Analyze sprint
- `POST /api/analyze/portfolio` - Analyze portfolio
- `GET /api/analyze/history/{issue_key}` - Get historical analyses
- `GET /api/analyze/trends/{issue_key}` - Get trend data

### Health
- `GET /health` - Health check

**Full API docs:** http://localhost:8080/docs

## 🗄️ Database Schema

### Tenants Table
Stores customer accounts with encrypted Jira credentials.

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  company_name VARCHAR(255),
  jira_url VARCHAR(500),
  jira_email VARCHAR(255),
  jira_token_encrypted TEXT,
  plan VARCHAR(50) DEFAULT 'starter',
  status VARCHAR(50) DEFAULT 'trial',
  monthly_issue_limit INT DEFAULT 200,
  monthly_sprint_limit INT DEFAULT 5,
  monthly_portfolio_limit INT DEFAULT 1,
  daily_rate_per_person FLOAT DEFAULT 2500.0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Usage Logs Table
Tracks every API call for billing.

```sql
CREATE TABLE usage_logs (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  action_type VARCHAR(50),  -- issue, sprint, portfolio
  resource_key VARCHAR(255),
  processing_time_ms INT,
  created_at TIMESTAMP
);
```

### Analysis History Table
Stores analysis results for trend tracking.

```sql
CREATE TABLE analysis_history (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(id),
  issue_key VARCHAR(50),
  project_key VARCHAR(50),
  risk_score INT,
  daily_cost FLOAT,
  blocker_count INT,
  sentiment_negative_pct FLOAT,
  age_days INT,
  analysis_json JSONB,
  analyzed_at TIMESTAMP
);
```

## 🔐 Multi-Tenant Security

Every API request (except tenant creation) requires:

```
X-Tenant-ID: <tenant-uuid>
```

The middleware:
1. Validates tenant exists
2. Checks tenant status (trial/active)
3. Loads tenant's Jira credentials
4. Decrypts Jira token
5. Enforces usage limits

## 📊 Usage Limits (by Plan)

| Plan | Issue Analyses | Sprint Analyses | Portfolio Analyses |
|------|----------------|-----------------|-------------------|
| Starter | 200/month | 5/month | 1/month |
| Growth | Unlimited | 20/month | 5/month |
| Enterprise | Unlimited | Unlimited | Unlimited |

## 🧪 Testing Locally

### Run without Docker (for development)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (if not using Docker)
# (Install PostgreSQL separately)

# Run migrations (if using Alembic - Week 2)
# alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8080
```

### Test Suite (add in Week 2)
```bash
pytest tests/
```

## 🚢 Deploy to DigitalOcean (Week 1 Final Steps)

### Step 1: Create Managed PostgreSQL

1. Go to DigitalOcean → Databases
2. Create PostgreSQL 15 cluster
3. Choose smallest size ($15/month) for testing
4. Copy connection string

### Step 2: Create App Platform App

1. Go to App Platform → Create App
2. Connect GitHub repo
3. Configure:
   - **Type:** Web Service
   - **Dockerfile Path:** `backend/Dockerfile`
   - **HTTP Port:** 8080
   - **Environment Variables:**
     - `DATABASE_URL` = (from managed DB)
     - `ENCRYPTION_KEY` = (generate new one)

### Step 3: Deploy

Click "Deploy" - DigitalOcean will:
- Build Docker image
- Deploy to their infrastructure
- Give you a URL: `https://consilo-xxxxx.ondigitalocean.app`

### Step 4: Test Production

```bash
# Create first tenant
curl -X POST https://consilo-xxxxx.ondigitalocean.app/api/tenants \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

## 💰 Cost Breakdown (Week 1)

- **DigitalOcean App Platform:** $12/month (Basic plan)
- **Managed PostgreSQL:** $15/month (smallest cluster)
- **Total:** $27/month

**Note:** You already have $12/month droplet. This replaces it.

## 📈 Metrics Dashboard (Week 3 TODO)

Once deployed, you can track:
- Tenants created
- Analyses run per day
- Average processing time
- Popular features
- Usage by plan

## 🔮 What's Next

### Week 2 (Days 8-14):
- ✅ Clerk.dev authentication
- ✅ Stripe billing integration
- ✅ Webhook handlers
- ✅ Subscription plan enforcement

### Week 3 (Days 15-21):
- ✅ Next.js frontend
- ✅ Dashboard UI
- ✅ Trend charts
- ✅ Blocker heatmaps

### Week 4 (Days 22-30):
- ✅ Landing page
- ✅ Email alerts
- ✅ Beta user onboarding
- ✅ Launch 🚀

## 🐛 Troubleshooting

### Docker won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Database connection fails
Check `DATABASE_URL` in `.env` matches docker-compose settings.

### FinBERT model download slow
First request downloads ~500MB model. Subsequent requests are fast.

### API returns 401 Unauthorized
Include `X-Tenant-ID` header in request.

### API returns 429 Too Many Requests
Tenant hit usage limit. Wait for next month or upgrade plan.

## 📞 Support

For issues during Week 1 implementation:
- Check `/health` endpoint first
- Review Docker logs: `docker-compose logs -f backend`
- Check database: `docker exec -it consilo-db psql -U consilo -d consilo`
- API docs: http://localhost:8080/docs

---

## ✅ Week 1 Checklist

Copy this checklist to track progress:

- [ ] Cloned repo
- [ ] Generated encryption key
- [ ] Started Docker Compose locally
- [ ] Created first tenant
- [ ] Analyzed first issue
- [ ] Analyzed first sprint
- [ ] Created DigitalOcean managed PostgreSQL
- [ ] Deployed to DigitalOcean App Platform
- [ ] Tested production API
- [ ] Verified usage tracking works
- [ ] Documented custom Jira fields (if any)

**Week 1 Goal:** Production-ready multi-tenant backend deployed to DigitalOcean ✅

---

Built with ❤️ for Consilo SaaS | Week 1 of 30-Day Plan
