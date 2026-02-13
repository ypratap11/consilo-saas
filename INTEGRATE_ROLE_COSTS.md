# ⚡ Quick Integration: Role-Based Cost Modeling

**Time:** 5 minutes  
**Impact:** Transform Consilo into enterprise financial intelligence platform

---

## What You're Adding

**Current:** Flat $2,500/day cost for all users  
**New:** Role-specific costs (Senior Engineer: $5K, Junior: $2K, PM: $4K, etc.)

**Why it matters:**
- More accurate cost modeling
- Executive-level financial reporting  
- Differentiation from competitors
- Justify $149-499/month pricing

---

## Step-by-Step Integration

### 1. Add role_costs.py (30 seconds)

```powershell
# Copy the file
copy role_costs.py backend\app\core\role_costs.py

# Verify it's there
ls backend\app\core\role_costs.py
```

### 2. Customize for Your Team (2 minutes)

```powershell
notepad backend\app\core\role_costs.py
```

**Update this section:**

```python
USER_ROLE_MAPPING = {
    # Replace with your actual Jira display names → roles
    'Pratap Yeragudipati': 'Senior PM',
    # Add your team members here
}
```

**How to find Jira display names:**
1. Open any Jira issue
2. Look at the "Assignee" field
3. Copy the exact name shown

**Save and close.**

### 3. Apply Database Migration (1 minute)

```powershell
# Add role tracking columns to database
docker-compose exec postgres psql -U consilo -d consilo -f /app/migrations/001_add_role_tracking.sql
```

Or manually:
```powershell
docker-compose exec postgres psql -U consilo -d consilo
```

Then paste:
```sql
ALTER TABLE analysis_history 
ADD COLUMN IF NOT EXISTS assignee VARCHAR(255),
ADD COLUMN IF NOT EXISTS assignee_role VARCHAR(100),
ADD COLUMN IF NOT EXISTS total_estimated_cost FLOAT;
\q
```

### 4. Rebuild Backend (1 minute)

```powershell
docker-compose up -d --build backend
```

Wait 30 seconds, then verify:
```powershell
docker-compose ps
```

Should show `consilo-api` as **healthy**.

### 5. Test It Works (1 minute)

```powershell
python test_local.py
```

Analyze an issue that **has an assignee**.

**Look for:**
```
Assignee: Pratap Yeragudipati (Senior PM)
Daily cost: $5,000
Total estimated cost: $15,000
```

---

## ✅ Success Criteria

After integration, you should see:

**Before:**
```
CAPACITY IMPACT:
• Daily cost: $2,500
• Estimated effort: 3 days
```

**After:**
```
CAPACITY IMPACT:
• Daily cost: $5,000
• Estimated effort: 3 days  
• Total estimated cost: $15,000

Assignee: Pratap Yeragudipati (Senior PM)
```

---

## 🎯 What This Unlocks

### Sprint Cost Breakdown
```
Sprint ENG-15 Cost Analysis:
• 3 Senior Engineers: $45,000/day
• 2 Mid Engineers: $18,000/day
• 1 PM: $12,000/day
Total daily exposure: $75,000
```

### Resource Optimization
```
High-Cost Issues:
• ENG-45 (Principal Eng): $7,000/day
  → Could reassign to Mid Eng: $3,000/day
  → Potential savings: $12,000
```

### Executive Dashboard
```
Blocked Issues Financial Impact:
• 12 Senior Engineers: $60,000/day
• 8 PMs: $32,000/day
• 5 Designers: $17,500/day
Total at-risk capital: $109,500/day
```

**This is CFO-level intelligence.**

---

## 🔧 Customization Options

### 1. Geographic Multipliers

```python
LOCATION_MULTIPLIERS = {
    'San Francisco': 1.3,
    'Bangalore': 0.4,
}
```

### 2. Overtime Rates

```python
OVERTIME_MULTIPLIER = 1.5  # After hours
WEEKEND_MULTIPLIER = 2.0   # Weekend work
```

### 3. Auto-Detection from Names

```python
ROLE_DETECTION_PATTERNS = {
    '(Senior|Sr\.).*Engineer': 'Senior Engineer',
    '(Junior|Jr\.).*Engineer': 'Junior Engineer',
}
```

---

## 💡 Pro Tips

1. **Start Simple:** Map 5-10 key people first
2. **Use Defaults:** Set `DEFAULT_RATE = 3000` for unmapped users
3. **Iterate:** Add more mappings as you analyze more issues
4. **Validate:** Run `python backend/app/core/role_costs.py` to check config

---

## 🐛 Troubleshooting

### Still showing $2,500?

1. Verify `role_costs.py` is in `backend/app/core/`
2. Rebuild: `docker-compose up -d --build backend`
3. Check logs: `docker-compose logs backend | grep -i role`

### "Unknown" role?

1. Check Jira display name matches exactly
2. Add to `USER_ROLE_MAPPING`
3. Or add pattern to `ROLE_DETECTION_PATTERNS`

### Need to update rates?

1. Edit `backend/app/core/role_costs.py`
2. Restart: `docker-compose restart backend`
3. No rebuild needed for rate changes

---

## 📊 Business Impact

**Consilo without role costs:**
- Generic risk dashboard
- $49/month pricing
- Competes with free Jira plugins

**Consilo with role costs:**
- **Financial intelligence platform**
- $149-499/month pricing
- Competes with enterprise BI tools
- **10x higher value perception**

**This feature justifies enterprise pricing.**

---

## ✅ Quick Checklist

- [ ] Copied `role_costs.py` to `backend/app/core/`
- [ ] Customized `USER_ROLE_MAPPING` with your team
- [ ] Set `DEFAULT_RATE` for unmapped users
- [ ] Applied database migration
- [ ] Rebuilt backend container
- [ ] Tested with real issue
- [ ] Verified role showing in output

**All done?** You now have enterprise-grade cost intelligence! 🎉

---

**Questions?** See `ROLE_COSTS_SETUP.md` for detailed guide.
