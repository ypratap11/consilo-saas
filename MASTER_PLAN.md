# 🚀 Consilo 30-Day Launch Plan - Master Reference

**Your Complete Roadmap from MVP to Revenue**

Last Updated: February 11, 2026  
Status: Week 1 ✅ Complete | Week 2 🔄 Ready to Build

---

## 📊 Executive Summary

**Goal:** Launch Consilo SaaS and acquire first paying customers in 30 days

**Milestones:**
- Week 1: ✅ Multi-tenant backend + AI engine (DONE)
- Week 2: 🔄 Authentication + Billing (READY)
- Week 3: 📅 Frontend dashboard + Charts
- Week 4: 🚀 Landing page + Beta launch

**Revenue Target:** 10 beta customers × $49/mo = $490 MRR by Day 30

---

## 🎯 Week 1: Foundation (Days 1-7) ✅ COMPLETE

### Objectives
- ✅ Build multi-tenant SaaS backend
- ✅ Integrate AI analysis engine
- ✅ Setup Docker deployment
- ✅ Test with real Jira data

### Deliverables Completed
1. **Backend API (FastAPI)**
   - Multi-tenant architecture
   - Tenant isolation via X-Tenant-ID
   - Encrypted credential storage (Fernet)
   - Health checks & monitoring

2. **AI Analysis Engine**
   - FinBERT sentiment analysis
   - 7-category blocker detection
   - Risk scoring algorithm (0-100)
   - Cost modeling with role-based rates
   - Geographic multipliers
   - Overtime/weekend detection

3. **Database (PostgreSQL)**
   - Tenants table
   - Usage logs (billing tracking)
   - Analysis history (trends)
   - Subscription plans

4. **API Endpoints**
   - POST /api/analyze/issue
   - POST /api/analyze/sprint
   - POST /api/analyze/portfolio
   - GET /api/analyze/history/{key}
   - GET /api/tenants/{id}/usage
   - CRUD /api/tenants

5. **Infrastructure**
   - Docker containerization
   - Local development setup
   - DigitalOcean deployment guide
   - Automated testing suite

6. **Advanced Features**
   - Role-based cost modeling
   - Geographic cost multipliers
   - Auto-detection from Jira names
   - Overtime detection
   - Weekend work tracking

### Time Investment
- **Planned:** 7 days
- **Actual:** 2 hours (with AI assistance)
- **Efficiency:** 28x faster than expected

### Week 1 Metrics
- ✅ 6/6 tests passing
- ✅ 1 tenant created
- ✅ 1+ issues analyzed
- ✅ 100% health check uptime
- ✅ Docker containers running
- ✅ Production-ready code

### Week 1 Lessons Learned
- Docker setup required Windows-specific commands
- email-validator dependency needed for Pydantic
- Geographic features add massive value
- Role-based costs justify enterprise pricing

---

## 🔐 Week 2: Authentication & Billing (Days 8-14) 🔄 READY

### Objectives
- Implement user authentication (Clerk.dev)
- Integrate Stripe subscriptions
- Add usage enforcement
- Setup payment webhooks
- Enable trial management

### Deliverables to Build

#### 1. Authentication Layer (Clerk.dev)
**What:** Google/Microsoft/Email login

**Files to Create:**
- `backend/app/auth/clerk.py` - Clerk JWT verification
- `backend/app/auth/middleware.py` - Protect routes
- `backend/app/routes/auth.py` - Login/logout endpoints

**Features:**
- Social login (Google, Microsoft)
- Email/password fallback
- JWT token validation
- User session management
- Multi-tenant user mapping

**Integration Points:**
- Replace X-Tenant-ID header with JWT claims
- Map Clerk user_id → tenant_id
- Automatic tenant creation on signup

#### 2. Stripe Integration
**What:** Accept payments, manage subscriptions

**Files to Create:**
- `backend/app/billing/stripe_client.py` - Stripe SDK wrapper
- `backend/app/routes/billing.py` - Subscription endpoints
- `backend/app/routes/webhooks.py` - Payment webhooks

**Features:**
- Create Stripe customer on signup
- Subscription checkout (3 plans)
- Payment method management
- Invoice generation
- Dunning management (failed payments)

**Endpoints:**
- POST /api/billing/checkout (create session)
- POST /api/billing/portal (customer portal)
- GET /api/billing/subscription (current plan)
- POST /api/billing/upgrade
- POST /api/billing/downgrade
- POST /api/webhooks/stripe (payment events)

#### 3. Usage Enforcement
**What:** Limit API calls based on subscription plan

**Updates to Existing Files:**
- `backend/app/middleware.py` - Add usage check
- `backend/app/models.py` - Track subscription status
- `backend/app/routes/analyze.py` - Enforce limits

**Logic:**
```python
if tenant.monthly_issues_used >= tenant.plan.monthly_issues_limit:
    raise HTTPException(
        status_code=403,
        detail="Monthly issue analysis limit reached. Upgrade plan."
    )
```

**Features:**
- Real-time usage tracking
- Soft limits (warnings at 80%)
- Hard limits (block at 100%)
- Usage reset on billing cycle
- Prorated upgrades

#### 4. Trial Management
**What:** 14-day free trial for new signups

**Database Updates:**
- Add `trial_ends_at` to tenants table
- Add `trial_converted` boolean
- Track trial usage separately

**Features:**
- 14-day trial period
- Full feature access during trial
- Auto-downgrade to free after trial (or require payment)
- Trial extension for qualified leads
- Convert trial → paid subscription

#### 5. Webhook Handlers
**What:** React to Stripe payment events

**Events to Handle:**
- `customer.subscription.created` → Activate subscription
- `customer.subscription.updated` → Update plan limits
- `customer.subscription.deleted` → Downgrade to free
- `invoice.payment_succeeded` → Reset usage counters
- `invoice.payment_failed` → Send dunning email

**Security:**
- Verify Stripe webhook signatures
- Idempotency keys
- Async processing (don't block webhook response)

### Week 2 Architecture

```
User Login (Clerk)
     ↓
JWT Token
     ↓
Backend validates JWT → Maps to tenant_id
     ↓
Check subscription status (Stripe)
     ↓
Check usage limits (usage_logs table)
     ↓
Allow/Deny API call
     ↓
Log usage → Update counters
     ↓
If limit approaching → Show upgrade prompt
```

### Week 2 Tech Stack
- **Clerk.dev:** $0/month (free tier: 10K MAU)
- **Stripe:** 2.9% + $0.30 per transaction
- **Python libraries:**
  - `clerk-backend-api`
  - `stripe`
  - `pyjwt`
  - `cryptography`

### Week 2 Success Criteria
- [ ] User can signup with Google
- [ ] User can login and get JWT
- [ ] JWT protects all API routes
- [ ] User can start 14-day trial
- [ ] User can subscribe via Stripe
- [ ] Subscription limits enforced
- [ ] Webhooks update subscription status
- [ ] Failed payment triggers email
- [ ] User can upgrade/downgrade plans
- [ ] Usage resets on billing cycle

### Week 2 Time Estimate
- **Setup Clerk:** 2 hours
- **Build auth middleware:** 2 hours
- **Integrate Stripe:** 3 hours
- **Webhook handlers:** 2 hours
- **Testing:** 2 hours
- **Total:** 11 hours (spread over 7 days)

### Week 2 Risks & Mitigations
**Risk:** Stripe webhook security
**Mitigation:** Use webhook signing, verify all signatures

**Risk:** Usage tracking race conditions
**Mitigation:** Use database transactions, atomic increments

**Risk:** Trial abuse
**Mitigation:** Email verification required, track by IP

---

## 🎨 Week 3: Frontend Dashboard (Days 15-21) 📅 PLANNED

### Objectives
- Build Next.js dashboard
- Create risk visualization charts
- Show historical trends
- Enable CSV exports

### Deliverables to Build

#### 1. Next.js Application
**Framework:** Next.js 14 (App Router)

**Pages:**
- `/` - Landing page
- `/login` - Clerk authentication
- `/dashboard` - Main dashboard
- `/dashboard/issues` - Issue list with risk scores
- `/dashboard/sprints` - Sprint analysis
- `/dashboard/settings` - Account settings
- `/dashboard/billing` - Subscription management

#### 2. Dashboard Components
**Charts (Recharts library):**
- Risk over time line chart
- Cost breakdown pie chart
- Blocker categories bar chart
- Sentiment trend area chart
- Usage vs limits gauge

**Tables:**
- High-risk issues table (sortable)
- Recent analyses list
- Blocked issues alert list

**Widgets:**
- Current risk score (big number + emoji)
- Daily cost exposure
- Usage this month (progress bar)
- Upgrade prompt (if near limit)

#### 3. Real-time Updates
**Technology:** Server-Sent Events (SSE) or polling

**Features:**
- Auto-refresh risk scores every 5 minutes
- Real-time usage counter updates
- New analysis notifications

#### 4. CSV Exports
**What:** Download analysis data

**Formats:**
- Issues CSV (all fields)
- Sprint summary CSV
- Cost breakdown CSV
- Historical trends CSV

**Access Control:** Growth plan and above only

### Week 3 Tech Stack
- Next.js 14
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- Recharts (charts)
- React Query (data fetching)

### Week 3 Success Criteria
- [ ] User can login via Clerk
- [ ] Dashboard shows real risk data
- [ ] Charts render correctly
- [ ] Issue list is sortable/filterable
- [ ] CSV export works
- [ ] Mobile responsive
- [ ] <3 second page load
- [ ] Works on Chrome, Firefox, Safari

### Week 3 Time Estimate
- **Next.js setup:** 1 hour
- **Dashboard layout:** 2 hours
- **Charts integration:** 3 hours
- **Tables & filters:** 2 hours
- **CSV export:** 1 hour
- **Polish & mobile:** 2 hours
- **Testing:** 2 hours
- **Total:** 13 hours

---

## 🚀 Week 4: Launch (Days 22-30) 🎯 PLANNED

### Objectives
- Create landing page
- Launch beta program
- Acquire first 10 customers
- Collect testimonials

### Deliverables to Build

#### 1. Landing Page
**Sections:**
- Hero (with animated demo)
- Problem/Solution
- Features (with screenshots)
- Pricing table
- Social proof (testimonials)
- FAQ
- CTA (Start free trial)

**Copy Focus:**
- "Prevent $100K project failures"
- "AI-powered delivery intelligence"
- "Know which issues will fail before they do"
- "CTOs use Consilo to save 20-40% on engineering costs"

#### 2. Beta Program
**Structure:**
- 50% off for first 3 months
- Weekly feedback calls
- Feature requests prioritized
- Testimonial in exchange for discount

**Target:** 10 beta customers

**Outreach:**
- LinkedIn (CTOs, VPs Engineering)
- Email (Oracle/ERP implementation teams)
- Reddit (r/projectmanagement, r/agile)
- ProductHunt launch

#### 3. Email Sequences
**Welcome Email:**
- Day 0: Welcome + setup guide
- Day 1: First analysis tutorial
- Day 3: Case study (similar company)
- Day 7: Check-in + offer help
- Day 13: Trial ending soon
- Day 14: Upgrade prompt

**Activation Email:**
- Analyze first issue
- Connect to Slack
- Invite team members
- Setup cost alerts

#### 4. Analytics & Tracking
**Tools:**
- PostHog (product analytics)
- Google Analytics (marketing)
- Stripe Dashboard (revenue)

**Metrics to Track:**
- Signups per day
- Trial → Paid conversion
- Time to first analysis
- Daily active users
- Churn rate
- MRR growth

### Week 4 Success Criteria
- [ ] Landing page live
- [ ] 50+ signups
- [ ] 10 active beta users
- [ ] 5 paying customers
- [ ] $245 MRR ($49 × 5)
- [ ] 2+ testimonials collected
- [ ] ProductHunt launch
- [ ] First blog post published

### Week 4 Time Estimate
- **Landing page:** 4 hours
- **Email sequences:** 2 hours
- **Beta outreach:** 6 hours
- **Analytics setup:** 1 hour
- **ProductHunt prep:** 2 hours
- **Customer calls:** 5 hours
- **Total:** 20 hours

---

## 💰 30-Day Financial Projections

### Costs
**Development:**
- DigitalOcean: $27/month
- Clerk.dev: $0 (free tier)
- Stripe: 2.9% + $0.30 per transaction
- Domain: $12/year
- **Total Month 1:** ~$30

**Marketing:**
- LinkedIn ads: $0 (organic only)
- Content: $0 (DIY)
- ProductHunt: $0
- **Total:** $0

**Time Investment:**
- Week 1: ✅ 2 hours (done)
- Week 2: 11 hours
- Week 3: 13 hours
- Week 4: 20 hours
- **Total:** 46 hours

### Revenue
**Conservative (50% of target):**
- 5 customers × $49/month = $245 MRR
- Annual run rate: $2,940

**Target:**
- 10 customers × $49/month = $490 MRR
- Annual run rate: $5,880

**Optimistic (200% of target):**
- 20 customers × $49/month = $980 MRR
- Annual run rate: $11,760

### ROI
**Month 1:**
- Investment: 46 hours + $30
- Revenue: $245-980 (depending on conversions)
- ROI: 8x - 33x

**Month 3 Projection:**
- 50 customers × $80/month average = $4,000 MRR
- Annual run rate: $48,000
- Profitability: Break-even at 2 customers

---

## 📊 Success Metrics by Week

### Week 1 Metrics (Actual)
- ✅ Backend deployed: Yes
- ✅ Tests passing: 6/6
- ✅ Real data analyzed: Yes
- ✅ Production ready: Yes

### Week 2 Metrics (Target)
- [ ] Auth working: Yes/No
- [ ] First subscription: Yes/No
- [ ] Webhooks tested: Yes/No
- [ ] Trial activated: Yes/No

### Week 3 Metrics (Target)
- [ ] Dashboard deployed: Yes/No
- [ ] Charts rendering: Yes/No
- [ ] Mobile responsive: Yes/No
- [ ] User feedback: Positive/Negative

### Week 4 Metrics (Target)
- [ ] Landing page live: Yes/No
- [ ] Signups: 50+ goal
- [ ] Beta customers: 10 goal
- [ ] Paying customers: 5 minimum
- [ ] MRR: $245+ goal
- [ ] ProductHunt votes: 100+ goal

---

## 🎯 90-Day Extended Plan

### Month 2 (Days 31-60)
**Focus:** Product refinement + growth

**Goals:**
- Reach 50 customers ($2,450 MRR)
- Add Slack integration
- Add email alerts
- Launch affiliate program
- First blog posts (SEO)

**Features:**
- Slack daily digest
- Risk threshold alerts
- Team collaboration
- API access (Enterprise)

### Month 3 (Days 61-90)
**Focus:** Scale + enterprise

**Goals:**
- Reach 150 customers ($7,350 MRR)
- Launch enterprise plan ($499/mo)
- Add SSO (SAML)
- White-label option
- Partner with consultancies

**Features:**
- Custom risk weights
- White-label branding
- Dedicated support
- SLA guarantees
- On-premise option

---

## 🚨 Risk Management

### Technical Risks
**Risk:** Jira API rate limits
**Mitigation:** Implement caching, batch requests

**Risk:** FinBERT model too slow
**Mitigation:** Cache sentiment results, use quantized model

**Risk:** Database scaling
**Mitigation:** Start with managed PostgreSQL, add read replicas later

### Business Risks
**Risk:** Low conversion rate
**Mitigation:** Extensive customer interviews, iterate on value prop

**Risk:** High churn
**Mitigation:** Onboarding sequence, customer success calls

**Risk:** Pricing too low
**Mitigation:** A/B test pricing, survey customers on willingness to pay

### Competitive Risks
**Risk:** Atlassian copies feature
**Mitigation:** Move fast, build moat through data + customer relationships

**Risk:** Competitor launches similar
**Mitigation:** Speed, customer intimacy, geographic features

---

## 📚 Documentation & Resources

### Technical Docs
- `START_HERE.md` - First file to read
- `README.md` - Complete setup guide
- `ARCHITECTURE.md` - System design
- `DEPLOYMENT.md` - Production deployment
- `WEEK_1_CHECKLIST.md` - Week 1 execution ✅
- `WEEK_2_CHECKLIST.md` - Week 2 execution (coming)

### Business Docs
- `ENTERPRISE_FEATURES.md` - ROI & value prop
- `PRICING_STRATEGY.md` - Pricing rationale (coming)
- `CUSTOMER_PERSONAS.md` - Target customers (coming)

### Code Organization
```
consilo-saas/
├── backend/
│   ├── app/
│   │   ├── auth/           # Week 2 - Clerk integration
│   │   ├── billing/        # Week 2 - Stripe integration
│   │   ├── core/           # Week 1 - AI engine ✅
│   │   ├── routes/         # Week 1 - API endpoints ✅
│   │   └── models.py       # Week 1 - Database ✅
│   └── requirements.txt
├── frontend/               # Week 3 - Next.js dashboard
├── docs/                   # All documentation
└── docker-compose.yml
```

---

## ✅ Decision Log

### Key Decisions Made
1. **Week 1:** Use Fernet encryption (simpler than AWS KMS)
2. **Week 1:** PostgreSQL over MongoDB (better for analytics)
3. **Week 1:** Role-based costs (massive value-add)
4. **Week 1:** Geographic multipliers (enterprise differentiator)
5. **Week 2:** Clerk over Auth0 (better DX, free tier)
6. **Week 2:** Stripe over PayPal (better subscription management)

### Decisions Pending
- [ ] Week 3: Chart library (Recharts vs Victory vs D3)
- [ ] Week 4: Email provider (SendGrid vs Resend vs Loops)
- [ ] Month 2: Analytics (PostHog vs Mixpanel)

---

## 🎯 Your Next Action Items

### Today (Day 8)
1. ✅ Review this master plan
2. 🔄 Start Week 2 code implementation
3. 📝 Create Clerk.dev account
4. 💳 Create Stripe account (test mode)

### This Week (Days 8-14)
1. Build authentication layer
2. Integrate Stripe billing
3. Test complete signup → payment flow
4. Deploy to production
5. Test with real credit card (test mode)

### By Day 30
1. Launch landing page
2. Acquire 10 beta customers
3. Collect 2+ testimonials
4. Reach $490 MRR

---

## 📞 Support & Resources

### When Stuck
1. Check documentation in `/docs`
2. Review this master plan
3. Ask for help (don't waste time)

### External Resources
- Clerk.dev docs: https://clerk.dev/docs
- Stripe docs: https://stripe.com/docs
- FastAPI docs: https://fastapi.tiangolo.com
- Next.js docs: https://nextjs.org/docs

---

## 🎉 Conclusion

**You have:**
- ✅ Clear 30-day roadmap
- ✅ Week 1 complete (2 hours invested)
- 🔄 Week 2 code ready to build
- 📅 Weeks 3-4 planned
- 💰 Financial projections
- 🎯 Success metrics

**What's possible:**
- 10 customers in 30 days
- $490 MRR by end of month
- $5,880 ARR by Month 1
- $180K+ ARR by Month 12

**Your advantage:**
- First mover (6-12 month head start)
- Enterprise features (geographic, role-based costs)
- Production ready (no MVP, actual product)
- Technical founder (can iterate fast)

---

**You're not building a side project. You're building a business.**

**Let's execute.** 🚀

---

Last Updated: February 11, 2026  
Next Update: After Week 2 completion  
Owner: Pratap Yeragudipati
