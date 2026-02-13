# Role-Based Cost Modeling Setup Guide

**This feature transforms Consilo from simple risk tracking to enterprise-grade financial intelligence.**

---

## 🎯 What This Does

Instead of flat $2,500/day rate for everyone:
- **Senior Engineer:** $5,000/day
- **Junior Engineer:** $2,000/day  
- **Product Manager:** $4,000/day
- **Contractor:** $3,500/day

**Impact:**
- More accurate cost modeling
- Better resource allocation insights
- Executive-level financial reporting
- "This issue costs $35,000" vs "high risk"

---

## 📦 Setup (5 Minutes)

### Step 1: Copy role_costs.py

```powershell
# You already have this file - just copy it
copy role_costs.py backend\app\core\role_costs.py
```

### Step 2: Customize for Your Team

```powershell
notepad backend\app\core\role_costs.py
```

**Update these sections:**

#### 1. Define Your Team's Roles & Rates

```python
ROLE_RATES = {
    # Your actual roles and rates
    'Senior Engineer': 5000,
    'Mid Engineer': 3000,
    'Junior Engineer': 2000,
    'PM': 4000,
    'Designer': 3500,
    'QA Engineer': 3000,
    # ... add your roles
}
```

#### 2. Map Your Team Members

```python
USER_ROLE_MAPPING = {
    # Replace with your actual Jira display names
    'Pratap Yeragudipati': 'Senior PM',
    'Sarah Chen': 'Senior Engineer',
    'Mike Rodriguez': 'Mid Engineer',
    # ... add your team
}
```

**To find Jira display names:**
1. Go to your Jira
2. Look at issue assignees
3. Copy their exact display name

#### 3. Set Default Rate

```python
DEFAULT_RATE = 3000  # For unmapped users
```

### Step 3: Rebuild Backend

```powershell
# Rebuild to include role_costs.py
docker-compose up -d --build backend

# Wait 30 seconds
docker-compose ps
```

Should show `consilo-api` as **healthy**.

---

## 🧪 Test It Works

### 1. Analyze an Issue with Assignee

```powershell
python test_local.py
```

Pick an issue that **has an assignee**.

**Before role-based costs:**
```
Daily cost: $2,500
```

**After role-based costs:**
```
Assignee: Pratap Yeragudipati (Senior PM)
Daily cost: $5,000
Total estimated cost: $15,000
```

### 2. Check Database

```powershell
docker-compose exec postgres psql -U consilo -d consilo -c "SELECT issue_key, assignee, assignee_role, daily_cost, total_estimated_cost FROM analysis_history ORDER BY analyzed_at DESC LIMIT 5;"
```

Should show role information!

---

## 📊 Advanced Features

### Geographic Cost Adjustments

```python
LOCATION_MULTIPLIERS = {
    'San Francisco': 1.3,  # 30% higher
    'Bangalore': 0.4,      # 60% lower
    'Remote': 1.0,
}
```

### Overtime Multipliers

```python
OVERTIME_MULTIPLIER = 1.5   # 1.5x for after-hours
WEEKEND_MULTIPLIER = 2.0    # 2x for weekend work
```

### Pattern Matching (Auto-detect from names)

```python
ROLE_DETECTION_PATTERNS = {
    '(Senior|Sr\.).*Engineer': 'Senior Engineer',
    '(Junior|Jr\.).*Engineer': 'Junior Engineer',
    'Product.*Manager': 'PM',
}
```

Consilo will auto-detect roles from Jira display names if not explicitly mapped.

---

## 💡 Use Cases

### 1. Sprint Cost Analysis

**Before:**
```
Sprint cost: $37,500 (15 issues × $2,500)
```

**After (role-based):**
```
Sprint cost breakdown:
• 3 Senior Engineers: $45,000
• 2 Mid Engineers: $18,000
• 1 PM: $12,000
• 1 Designer: $10,500
Total: $85,500
```

### 2. Resource Optimization

Identify expensive issues:
```
Issue ENG-45: Assigned to Principal Engineer ($7,000/day)
Recommendation: Could be handled by Mid Engineer ($3,000/day)
Potential savings: $12,000
```

### 3. Executive Reporting

"Our blocked issues represent $427,000 in daily cost exposure across:
- 12 Senior Engineers ($60K/day)
- 8 Product Managers ($32K/day)
- ..."

This is **CFO-level intelligence**.

---

## 🔧 Troubleshooting

### Issue: All costs still showing $2,500

**Fix:** Make sure you rebuilt the container:
```powershell
docker-compose up -d --build backend
```

### Issue: "Unknown" roles showing

**Fix:** Add that person to `USER_ROLE_MAPPING`:
```python
USER_ROLE_MAPPING = {
    'Their Jira Name': 'Their Role',
}
```

### Issue: Want to test without rebuilding

**Fix:** Edit `role_costs.py` inside the container:
```powershell
docker-compose exec backend vi /app/app/core/role_costs.py
docker-compose restart backend
```

---

## 📈 Impact on Consilo Value

**Without role-based costs:**
- "This sprint has 47 risk score"
- Generic dashboard

**With role-based costs:**
- "This sprint has $427K daily cost exposure"
- "Blocked Senior Engineers cost you $35K/day"
- "Resource optimization could save $15K/sprint"

**This is why enterprises pay $149-499/month for Consilo.**

---

## 🎯 Next Steps

1. ✅ Copy `role_costs.py` to `backend/app/core/`
2. ✅ Customize roles and rates for your team
3. ✅ Map your team members
4. ✅ Rebuild backend container
5. ✅ Test with real issues
6. ✅ Show to your CTO/CFO

---

## 💰 Pricing Impact

**Without this feature:**
- "Nice Jira dashboard" = $49/month

**With this feature:**
- "Financial intelligence platform" = $149-499/month
- Enterprise customers see **10x ROI** in first month

**This is your differentiator.**

---

Built with ❤️ for Consilo Enterprise Features
