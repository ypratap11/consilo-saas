# Consilo SaaS - Complete Project Overview

## 🎯 What Is Consilo?

**Consilo is an AI-powered delivery risk intelligence platform for engineering teams.**

Instead of just showing Jira data, Consilo:
- Quantifies risk (0-100 score)
- Calculates cost exposure ($/day)
- Detects blockers automatically
- Analyzes team sentiment
- Predicts delivery issues
- Tracks trends over time

**Target customers:** CTOs, Engineering Managers, PMOs at companies with 50-500 engineers

**Pricing:** $49-$499/month per team

**Competitive advantage:** First to combine AI sentiment analysis + cost modeling + predictive analytics for Jira

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Week 3)                       │
│                   Next.js + Tailwind                        │
│              Auth: Clerk.dev | Billing: Stripe              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Consilo API (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes Layer                                        │  │
│  │  • /api/tenants  - Tenant management                 │  │
│  │  • /api/analyze  - Analysis endpoints                │  │
│  │  • /health       - Health check                      │  │
│  └────────┬────────────────────────────────────┬────────┘  │
│           │                                     │           │
│  ┌────────▼────────┐                  ┌────────▼────────┐  │
│  │   Middleware    │                  │  Consilo Engine  │  │
│  │  • Tenant auth  │                  │  • Sentiment AI │  │
│  │  • Encryption   │                  │  • Risk calc    │  │
│  │  • Usage limits │                  │  • Predictions  │  │
│  └────────┬────────┘                  └────────┬────────┘  │
│           │                                     │           │
│  ┌────────▼─────────────────────────────────────▼────────┐  │
│  │              Database Layer (SQLAlchemy)             │  │
│  │  • tenants                                           │  │
│  │  • usage_logs                                        │  │
│  │  • analysis_history                                  │  │
│  │  • subscription_plans                                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         ▼                        ▼
┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL     │    │    Jira API      │
│  (DigitalOcean)  │    │   + FinBERT AI   │
└──────────────────┘    └──────────────────┘
```

---

## 🗂️ Project Structure

```
consilo-saas/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy connection
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── middleware.py        # Tenant isolation, encryption
│   │   ├── core/
│   │   │   ├── consilo_engine.py # AI analysis engine
│   │   │   ├── sprint.py        # Sprint aggregation
│   │   │   └── portfolio.py     # Portfolio aggregation
│   │   └── routes/
│   │       ├── analyze.py       # Analysis endpoints
│   │       ├── tenants.py       # Tenant management
│   │       └── health.py        # Health check
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                  # Database seeding
├── docker-compose.yml           # Local dev environment
├── .env.example                 # Environment template
├── .gitignore
├── Makefile                     # Common commands
├── test_local.py               # Test suite
├── README.md                    # Full documentation
├── QUICKSTART.md               # 30-minute setup
├── DEPLOYMENT.md               # Production deployment
├── WEEK_1_CHECKLIST.md         # Daily tasks
└── ARCHITECTURE.md             # This file
```

---

## 🔐 Security Architecture

### Multi-Tenant Isolation

Every API request requires `X-Tenant-ID` header:

1. Middleware validates tenant exists
2. Checks tenant status (trial/active/suspended)
3. Loads tenant-specific Jira credentials
4. Decrypts Jira token using Fernet encryption
5. Enforces usage limits based on plan

### Credential Encryption

Jira API tokens are encrypted using `cryptography.fernet`:

```python
# Encryption
encrypted = fernet.encrypt(token.encode()).decode()

# Decryption (at runtime only)
token = fernet.decrypt(encrypted.encode()).decode()
```

Encryption key stored in environment variable, **never in code**.

### Database Security

- SSL/TLS encryption in transit (`sslmode=require`)
- Managed by DigitalOcean (automatic backups, patching)
- No direct public access (App Platform only)
- Row-level tenant_id isolation

---

## 💾 Database Schema

### Tenants Table
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    jira_url VARCHAR(500) NOT NULL,
    jira_email VARCHAR(255) NOT NULL,
    jira_token_encrypted TEXT NOT NULL,
    
    plan VARCHAR(50) DEFAULT 'starter',
    status VARCHAR(50) DEFAULT 'trial',
    
    monthly_issue_limit INT DEFAULT 200,
    monthly_sprint_limit INT DEFAULT 5,
    monthly_portfolio_limit INT DEFAULT 1,
    
    daily_rate_per_person FLOAT DEFAULT 2500.0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    trial_ends_at TIMESTAMP,
    
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255)
);
```

### Usage Logs Table
```sql
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    
    action_type VARCHAR(50) NOT NULL,  -- issue, sprint, portfolio
    resource_key VARCHAR(255),
    processing_time_ms INT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_tenant_date ON usage_logs(tenant_id, created_at);
CREATE INDEX idx_usage_action ON usage_logs(action_type);
```

### Analysis History Table
```sql
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    
    issue_key VARCHAR(50) NOT NULL,
    project_key VARCHAR(50) NOT NULL,
    
    risk_score INT NOT NULL,
    daily_cost FLOAT NOT NULL,
    blocker_count INT DEFAULT 0,
    sentiment_negative_pct FLOAT,
    age_days INT,
    
    analysis_json JSONB,
    analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_history_tenant ON analysis_history(tenant_id);
CREATE INDEX idx_history_issue ON analysis_history(issue_key);
CREATE INDEX idx_history_date ON analysis_history(analyzed_at);
```

---

## 🧠 AI Analysis Engine

### ConsiloEngine Flow

```
Input: Issue Key (e.g., ENG-123)
    ↓
1. Fetch issue + comments from Jira
    ↓
2. Sentiment Analysis (FinBERT)
   • Process all comments
   • Calculate positive/negative %
   • Identify sentiment trend
    ↓
3. Blocker Detection (NLP patterns)
   • Category: technical_debt
   • Category: dependency
   • Category: resource
   • Category: external
   • Category: requirements
   • Category: testing
   • Category: deployment
    ↓
4. Timeline Analysis
   • Age (days since created)
   • Last update (days)
   • Status change history
    ↓
5. Capacity Modeling
   • Estimated person-days
   • Daily cost exposure
   • Days lost if blocked
    ↓
6. Risk Scoring (0-100)
   • Sentiment: 0-30 points
   • Blockers: 0-30 points
   • Age: 0-20 points
   • Staleness: 0-20 points
    ↓
7. Predictions
   • Completion likelihood
   • Recommended action
   • Escalation needed?
    ↓
Output: Complete Analysis Dict
```

### Risk Score Calculation

```python
risk = 0

# Sentiment (max 30)
risk += negative_pct * 0.3

# Blockers (max 30)
risk += min(blocker_count * 10, 30)

# Age (max 20)
if age > 30 days: risk += 20
elif age > 14 days: risk += 10
elif age > 7 days: risk += 5

# Staleness (max 20)
if last_update > 10 days: risk += 20
elif last_update > 5 days: risk += 10
elif last_update > 3 days: risk += 5

total_risk = min(risk, 100)
```

---

## 📊 API Endpoints

### Tenant Management
```
POST   /api/tenants                    Create tenant
GET    /api/tenants/{id}               Get tenant info
PUT    /api/tenants/{id}               Update tenant
DELETE /api/tenants/{id}               Delete tenant
GET    /api/tenants/{id}/usage         Get usage stats
```

### Analysis
```
POST   /api/analyze/issue              Analyze single issue
GET    /api/analyze/issue/{key}/raw    Raw analysis (JSON)
POST   /api/analyze/sprint             Analyze sprint
POST   /api/analyze/portfolio          Analyze portfolio
GET    /api/analyze/history/{key}      Historical analyses
GET    /api/analyze/trends/{key}       Trend analysis
```

### Health
```
GET    /health                         Health check
```

---

## 💰 Business Model

### Pricing Tiers

| Feature | Starter | Growth | Enterprise |
|---------|---------|--------|------------|
| **Price** | $49/mo | $149/mo | $499/mo |
| Issue Analyses | 200/mo | Unlimited | Unlimited |
| Sprint Analyses | 5/mo | 20/mo | Unlimited |
| Portfolio Analyses | 1/mo | 5/mo | Unlimited |
| CSV Export | ❌ | ✅ | ✅ |
| API Access | ❌ | ❌ | ✅ |
| Custom Risk Weights | ❌ | ❌ | ✅ |
| Slack Integration | ❌ | ✅ | ✅ |
| Support | Email | Priority | Dedicated |

### Revenue Projections

| Month | Customers | MRR | ARR |
|-------|-----------|-----|-----|
| 1 (Beta) | 10 | $490 | $5,880 |
| 3 | 50 | $2,450 | $29,400 |
| 6 | 150 | $7,350 | $88,200 |
| 12 | 300 | $14,700 | $176,400 |

**Assumptions:**
- 70% Starter, 25% Growth, 5% Enterprise
- 5% monthly churn
- 30% month-over-month growth

### Unit Economics

**Customer Acquisition Cost (CAC):**
- Week 4 beta: $0 (organic outreach)
- Month 2-3: ~$50 (LinkedIn ads, content marketing)
- Month 4+: ~$100 (paid channels)

**Lifetime Value (LTV):**
- Average plan: $80/month
- Average lifetime: 18 months
- LTV: $1,440

**LTV:CAC Ratio:** 14:1 (excellent)

**Gross Margin:** ~90% (SaaS product)

**Infrastructure Cost:**
- DigitalOcean: $27/month (fixed)
- Clerk.dev: $25/month (up to 1,000 users)
- Stripe: 2.9% + $0.30/transaction
- **Total at 50 customers:** ~$200/month
- **Margin:** $2,250/month (~92%)

---

## 🚀 Launch Strategy

### Week 1: Infrastructure ✅
- Multi-tenant backend
- AI engine
- DigitalOcean deployment

### Week 2: Authentication & Billing
- Clerk.dev integration
- Stripe subscriptions
- Usage enforcement

### Week 3: Frontend
- Next.js dashboard
- Risk visualization
- Trend charts

### Week 4: Launch
- Landing page
- Beta outreach (50 prospects)
- Email alerts
- Onboarding flow

### Month 2-3: Growth
- Content marketing (blog posts)
- LinkedIn presence
- Testimonials
- Feature requests implementation

---

## 🎯 Success Metrics

### Product Metrics
- Daily Active Tenants
- Analyses per tenant/day
- Average risk score
- API response time
- Error rate

### Business Metrics
- MRR (Monthly Recurring Revenue)
- Customer count
- Churn rate
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)

### Health Indicators
- API uptime (target: 99.9%)
- P95 response time (target: <3s)
- Database query time (target: <100ms)

---

## 🔮 Future Roadmap

### Phase 2 (Months 2-3)
- Slack alerts ("Issue X risk increased to 85")
- CSV export
- Email digests
- Custom risk weight tuning

### Phase 3 (Months 4-6)
- Jira Marketplace app
- Microsoft Teams integration
- Velocity tracking
- Burndown predictions

### Phase 4 (Months 7-12)
- Public API
- Zapier integration
- Advanced ML models
- Competitive analysis

---

## 💡 Why Consilo Wins

### Differentiation

**vs. Jira Native Dashboards:**
- ❌ Jira: Manual risk assessment
- ✅ Consilo: Automated AI risk scoring

**vs. Linear/ClickUp:**
- ❌ Competitors: Focus on task management
- ✅ Consilo: Focus on delivery intelligence

**vs. Consultants:**
- ❌ Consultants: $200/hour, manual analysis
- ✅ Consilo: $49/month, instant analysis

### Market Opportunity

**TAM (Total Addressable Market):**
- 500K+ companies use Jira
- Target: Engineering teams 50-500 people
- 50K potential customers

**SAM (Serviceable Addressable Market):**
- Companies willing to pay for AI tooling
- ~10K customers

**SOM (Serviceable Obtainable Market):**
- Year 1 realistic capture: 300 customers
- Revenue: ~$180K ARR

---

## 📞 Support & Documentation

### For Development
- `README.md` - Complete setup guide
- `QUICKSTART.md` - 30-minute setup
- `http://localhost:8080/docs` - Interactive API docs

### For Deployment
- `DEPLOYMENT.md` - DigitalOcean guide
- `WEEK_1_CHECKLIST.md` - Daily tasks

### For Usage
- `Makefile` - Common commands (`make help`)
- `test_local.py` - Test suite

---

## 🏁 Current Status

**Week 1 Complete:** ✅
- Backend API deployed
- Multi-tenant isolation
- AI analysis engine
- Usage tracking
- Production-ready on DigitalOcean

**Next: Week 2**
- Clerk.dev auth
- Stripe billing
- Subscription enforcement

**Goal:** Paid beta launch in 30 days

---

Built with ❤️ for Consilo SaaS
