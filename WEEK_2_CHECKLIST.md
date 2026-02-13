# 🔐 Week 2 Execution Checklist - Authentication & Billing

**Goal:** Add user authentication and subscription billing to Consilo

**Time Estimate:** 11 hours spread over 7 days  
**Outcome:** Users can signup, login, and subscribe to paid plans

---

## 📋 Pre-Week Checklist

Before starting Week 2:

- [ ] Week 1 fully complete (backend running, tests passing)
- [ ] DigitalOcean account created (if deploying)
- [ ] Credit card ready for Stripe/Clerk accounts
- [ ] Email domain ready (for transactional emails)

---

## 📅 Day 8 (Monday): Setup External Services

**Time:** 2 hours

### Morning: Create Accounts

- [ ] **Create Clerk.dev Account**
  - Go to https://clerk.dev
  - Sign up (free for <10K users)
  - Create new application "Consilo"
  - Choose providers: Google, Microsoft, Email
  - Copy API keys (Publishable + Secret)

- [ ] **Create Stripe Account**
  - Go to https://stripe.com
  - Sign up
  - Activate test mode
  - Copy API keys (Publishable + Secret)
  
### Afternoon: Configure Products in Stripe

- [ ] **Create Products in Stripe Dashboard**
  - Product 1: "Consilo Starter"
    - Price: $49/month
    - Recurring
    - Save price ID
  
  - Product 2: "Consilo Growth"
    - Price: $149/month
    - Recurring
    - Save price ID
  
  - Product 3: "Consilo Enterprise"
    - Price: $499/month
    - Recurring
    - Save price ID

- [ ] **Setup Webhook in Stripe**
  - Add endpoint: `https://your-domain.com/api/webhooks/stripe`
  - Select events:
    - `customer.subscription.created`
    - `customer.subscription.updated`
    - `customer.subscription.deleted`
    - `invoice.payment_succeeded`
    - `invoice.payment_failed`
  - Copy webhook signing secret

### Evening: Update Environment Variables

- [ ] **Update `.env` file:**
```bash
# Existing variables
DATABASE_URL=...
ENCRYPTION_KEY=...

# Week 2: Clerk Authentication
CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx
CLERK_JWKS_URL=https://api.clerk.dev/v1/jwks

# Week 2: Stripe Billing
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_STARTER=price_xxx
STRIPE_PRICE_GROWTH=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
```

**Day 8 Checkpoint:**
- ✅ Clerk account created
- ✅ Stripe account created
- ✅ Products configured
- ✅ Webhook configured
- ✅ Environment variables updated

---

## 📅 Day 9 (Tuesday): Database Migration

**Time:** 1 hour

### Morning: Create Migration

- [ ] **Add User table**
```powershell
docker-compose exec postgres psql -U consilo -d consilo
```

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tenant_id UUID REFERENCES tenants(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- Add owner_user_id to tenants
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES users(id);
CREATE INDEX IF NOT EXISTS idx_tenants_owner ON tenants(owner_user_id);

-- Verify
\dt
\d users
\d tenants
\q
```

### Afternoon: Rebuild Backend

- [ ] **Extract Week 2 code package**
```powershell
# Extract consilo-saas-week2.tar.gz
tar -xzf consilo-saas-week2.tar.gz
cd consilo-saas
```

- [ ] **Rebuild with new dependencies**
```powershell
docker-compose up -d --build backend
```

- [ ] **Verify health**
```powershell
docker-compose ps
curl http://localhost:8080/health
```

**Day 9 Checkpoint:**
- ✅ Database migrated
- ✅ Backend rebuilt
- ✅ Health check passing

---

## 📅 Day 10 (Wednesday): Test Authentication

**Time:** 2 hours

### Morning: Test Signup Flow

- [ ] **Create test user in Clerk Dashboard**
  - Go to Clerk dashboard
  - Users → Create user
  - Email: test@example.com
  - Copy user ID

- [ ] **Get JWT token**
  - Use Clerk's testing tools OR
  - Build simple login page (see `WEEK_2_SETUP.md`)

- [ ] **Test protected endpoint**
```powershell
# Get JWT from Clerk dashboard (Testing → JWT Template)
$TOKEN = "eyJ..."

# Test authentication
curl http://localhost:8080/api/tenants `
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** Should create tenant automatically on first request

### Afternoon: Test Tenant Creation

- [ ] **Verify tenant created**
```powershell
docker-compose exec postgres psql -U consilo -d consilo -c "SELECT * FROM users;"
docker-compose exec postgres psql -U consilo -d consilo -c "SELECT * FROM tenants WHERE status='trial';"
```

- [ ] **Verify 14-day trial**
  - Check `trial_ends_at` is 14 days from now
  - Check `status = 'trial'`
  - Check limits match starter plan

**Day 10 Checkpoint:**
- ✅ User authentication working
- ✅ Tenant auto-creation working
- ✅ Trial period set correctly

---

## 📅 Day 11 (Thursday): Test Stripe Integration

**Time:** 3 hours

### Morning: Test Checkout Flow

- [ ] **Create checkout session**
```powershell
# Using your JWT token
curl -X POST http://localhost:8080/api/billing/checkout `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d "{
    \"plan\": \"starter\",
    \"success_url\": \"http://localhost:3000/success\",
    \"cancel_url\": \"http://localhost:3000/cancel\"
  }"
```

**Expected:** Returns checkout URL

- [ ] **Complete test payment**
  - Open checkout URL in browser
  - Use Stripe test card: `4242 4242 4242 4242`
  - Expiry: Any future date
  - CVC: Any 3 digits
  - Complete payment

### Afternoon: Test Webhooks

- [ ] **Verify subscription created**
```powershell
# Check backend logs
docker-compose logs backend | grep -i subscription

# Check database
docker-compose exec postgres psql -U consilo -d consilo -c "
SELECT id, company_name, plan, status, stripe_customer_id, stripe_subscription_id
FROM tenants WHERE stripe_subscription_id IS NOT NULL;
"
```

- [ ] **Test webhook manually**
  - Go to Stripe Dashboard → Webhooks
  - Find webhook endpoint
  - Send test event: `customer.subscription.created`
  - Check backend logs

### Evening: Test Billing Portal

- [ ] **Access billing portal**
```powershell
curl -X POST http://localhost:8080/api/billing/portal `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d "{
    \"return_url\": \"http://localhost:3000/dashboard\"
  }"
```

- [ ] **Test portal features**
  - Update payment method
  - View invoices
  - Change plan
  - Cancel subscription

**Day 11 Checkpoint:**
- ✅ Checkout working
- ✅ Payments processing
- ✅ Webhooks firing
- ✅ Billing portal accessible

---

## 📅 Day 12 (Friday): Test Usage Limits

**Time:** 2 hours

### Morning: Test Limit Enforcement

- [ ] **Analyze issues until limit**
```powershell
# Analyze 200+ issues (starter plan limit)
for i in {1..205}
do
  curl -X POST http://localhost:8080/api/analyze/issue `
    -H "Authorization: Bearer $TOKEN" `
    -H "Content-Type: application/json" `
    -d "{\"issue_key\": \"ENG-$i\"}"
done
```

**Expected:** First 200 succeed, 201+ fail with 429 error

- [ ] **Verify error message**
  - Should say "Monthly issue analysis limit reached"
  - Should suggest upgrading plan

### Afternoon: Test Plan Upgrade

- [ ] **Upgrade to growth plan**
```powershell
curl -X POST "http://localhost:8080/api/billing/upgrade?plan=growth" `
  -H "Authorization: Bearer $TOKEN"
```

- [ ] **Verify limits increased**
```powershell
curl http://localhost:8080/api/billing/subscription `
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** `monthly_issues_limit: 99999` (unlimited)

- [ ] **Test analysis works again**
```powershell
curl -X POST http://localhost:8080/api/analyze/issue `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"issue_key\": \"ENG-250\"}"
```

**Day 12 Checkpoint:**
- ✅ Usage limits enforced
- ✅ Upgrade working
- ✅ Limits updated correctly

---

## 📅 Day 13 (Saturday): Production Deployment

**Time:** 1 hour (if deploying)

- [ ] **Update production environment variables**
  - Add all Clerk/Stripe keys to DigitalOcean
  - Use production Stripe keys (not test)
  - Use production Clerk keys

- [ ] **Deploy to DigitalOcean**
```powershell
# Push to GitHub
git add .
git commit -m "Add authentication and billing (Week 2)"
git push origin main
```

- [ ] **Run database migration on production**
  - Connect to production database
  - Run users table creation script
  - Verify schema

- [ ] **Update Stripe webhook URL**
  - Change to production URL
  - Test webhook delivery

**Day 13 Checkpoint:**
- ✅ Production deployed
- ✅ Environment variables configured
- ✅ Webhooks pointing to production

---

## 📅 Day 14 (Sunday): End-to-End Testing

**Time:** 2 hours

### Full User Journey Test

- [ ] **Signup Flow**
  1. User signs up with Google/Email
  2. Tenant created with 14-day trial
  3. User redirected to dashboard
  4. Usage limits show trial plan

- [ ] **Trial Usage**
  1. User analyzes 10 issues
  2. Usage counter increases
  3. Approaching limit warning at 160/200
  4. Limit hit at 200/200

- [ ] **Upgrade Flow**
  1. User clicks "Upgrade"
  2. Redirected to Stripe checkout
  3. Completes payment
  4. Redirected back to dashboard
  5. Plan updated to "Starter"
  6. Usage limits increased
  7. Can analyze more issues

- [ ] **Billing Management**
  1. User accesses billing portal
  2. Updates payment method
  3. Views past invoices
  4. Sees next invoice preview

- [ ] **Cancellation Flow**
  1. User cancels subscription
  2. Subscription marked to cancel at period end
  3. Usage still allowed until period end
  4. After period end, downgraded to free

### Documentation

- [ ] **Document any issues found**
- [ ] **Update README with learnings**
- [ ] **Create user onboarding guide**

**Day 14 Checkpoint:**
- ✅ End-to-end flow tested
- ✅ All edge cases covered
- ✅ Documentation updated

---

## 🎯 Week 2 Success Criteria

By end of Week 2, you should have:

**Technical:**
- [  ] Users can signup with Google/Microsoft/Email
- [  ] JWT authentication protects all API routes
- [  ] Tenants created automatically on first login
- [  ] 14-day trial period works
- [  ] Stripe checkout processes payments
- [  ] Webhooks update subscription status
- [  ] Usage limits enforced by plan
- [  ] Plan upgrades/downgrades work
- [  ] Billing portal accessible

**Business:**
- [  ] Test payment completed successfully
- [  ] Webhook events processing correctly
- [  ] Trial → Paid conversion flow works
- [  ] Cancellation flow works
- [  ] Ready for real customers

**Deployment:**
- [  ] Production environment configured
- [  ] All secrets in environment variables
- [  ] Database migrations applied
- [  ] Stripe webhooks configured for production

---

## 🐛 Common Issues & Solutions

### Issue: JWT verification fails
**Solution:** Check CLERK_JWKS_URL is correct, verify token not expired

### Issue: Stripe webhook not firing
**Solution:** Check webhook URL is accessible, verify signing secret matches

### Issue: Trial not creating correctly
**Solution:** Check `trial_ends_at` calculation, verify timezone handling

### Issue: Usage limits not enforcing
**Solution:** Check middleware is applied to routes, verify database transaction handling

### Issue: Database migration fails
**Solution:** Check UUID extension installed, verify no circular foreign key references

---

## 📊 Week 2 Metrics

Track these metrics:

- [ ] **Test Completions:**
  - Authentication tests: ___/5 passed
  - Billing tests: ___/5 passed
  - Integration tests: ___/3 passed

- [ ] **Performance:**
  - Checkout session creation: <500ms
  - JWT verification: <100ms
  - Webhook processing: <1000ms

- [ ] **Coverage:**
  - All happy paths tested
  - 5+ edge cases tested
  - Error handling verified

---

## 🎉 Week 2 Complete!

When all checkboxes are marked:

1. ✅ Celebrate! You built a complete authentication & billing system
2. 📸 Take screenshots of working flow
3. 💾 Backup database
4. 📝 Document any customizations made
5. 🚀 Ready for Week 3: Frontend Dashboard

---

**Next:** `WEEK_3_CHECKLIST.md` - Build the frontend dashboard

**Questions?** Check `WEEK_2_SETUP.md` for detailed troubleshooting
