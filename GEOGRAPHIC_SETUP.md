# 🌍 Geographic & Auto-Detection Setup Guide

**Transform Consilo into a global cost intelligence platform**

---

## 🎯 What These Features Do

### 1. Geographic Cost Multipliers
**Automatically adjust costs based on location:**
```
Senior Engineer (Base: $5,000/day)
• San Francisco: $6,500/day (1.3x)
• Bangalore: $2,000/day (0.4x)
• Austin: $5,000/day (1.0x)
```

### 2. Auto-Detection from Names
**No manual mapping needed:**
```
"Sarah Chen - Senior Engineer" → Auto-detects "Senior Engineer"
"Mike Rodriguez (Jr. Dev)" → Auto-detects "Junior Engineer"
"PM - Alex Kim" → Auto-detects "PM"
```

### 3. Overtime/Weekend Detection
**Higher costs for after-hours work:**
```
Comment at 10 PM → 1.5x multiplier
Comment on Saturday → 2.0x multiplier
On-call incident → 1.2x multiplier
```

---

## 📦 Setup (10 Minutes)

### Step 1: Configure Geographic Multipliers

Open `backend/app/core/role_costs.py`:

```python
# Geographic adjustments (if you have distributed teams)
LOCATION_MULTIPLIERS = {
    # US Cities
    'San Francisco': 1.3,    # 30% higher (high cost of living)
    'New York': 1.2,         # 20% higher
    'Seattle': 1.15,         # 15% higher
    'Austin': 1.0,           # Baseline
    'Portland': 1.0,         # Baseline
    
    # International
    'London': 1.1,           # 10% higher
    'Bangalore': 0.4,        # 60% lower (purchasing power parity)
    'Warsaw': 0.5,           # 50% lower
    'Mexico City': 0.5,      # 50% lower
    
    # Remote/Other
    'Remote': 1.0,           # Baseline
}
```

**How to choose multipliers:**
1. Pick a baseline location (usually US average)
2. Adjust based on:
   - Cost of living
   - Market rates
   - Your actual salary bands

**Pro tip:** Use purchasing power parity (PPP) data from sites like Numbeo.com

### Step 2: Map Team Members to Locations

```python
USER_LOCATION_MAPPING = {
    # US Team
    'Pratap Yeragudipati': 'San Francisco',
    'Sarah Chen': 'San Francisco',
    'Mike Rodriguez': 'Austin',
    
    # International Team
    'Rajesh Kumar': 'Bangalore',
    'Anna Kowalski': 'Warsaw',
    'Carlos Martinez': 'Mexico City',
    
    # Remote Workers
    'Alex Kim': 'Remote',
}
```

**To find team locations:**
1. Check Jira user profiles
2. Ask your HR/admin
3. Or let auto-detection handle it (see Step 3)

### Step 3: Enable Auto-Detection

Consilo can auto-detect roles from Jira display names using patterns:

```python
ROLE_DETECTION_PATTERNS = {
    # Engineering
    r'(Senior|Sr\.?).*Engineer': 'Senior Engineer',
    r'(Staff|Principal).*Engineer': 'Staff Engineer',
    r'(Mid|Middle).*Engineer': 'Mid Engineer',
    r'(Junior|Jr\.?).*Engineer': 'Junior Engineer',
    r'Tech.*Lead': 'Tech Lead',
    
    # Product
    r'(Senior|Sr\.?).*PM': 'Senior PM',
    r'Product.*Manager': 'PM',
    r'(Associate|Assoc\.).*PM': 'Associate PM',
    
    # Design
    r'(Senior|Sr\.?).*Designer': 'Senior Designer',
    r'Designer': 'Designer',
    
    # QA & DevOps
    r'QA|Quality': 'QA Engineer',
    r'DevOps': 'DevOps Engineer',
    r'SRE|Reliability': 'SRE',
    
    # Data
    r'Data.*Scientist': 'Data Scientist',
    r'Data.*Engineer': 'Data Engineer',
    
    # Other
    r'Contractor': 'Contractor',
    r'Intern': 'Intern',
}
```

**How it works:**
1. Consilo checks `USER_ROLE_MAPPING` first (manual)
2. If not found, tries pattern matching
3. If no match, uses `DEFAULT_ROLE`

**Example detections:**
```
"Sarah Chen - Senior Engineer" → Senior Engineer
"Mike (Jr. Dev)" → Junior Engineer
"Alex Kim, PM" → PM
"QA Lead - Jordan" → QA Engineer
```

### Step 4: Configure Time-Based Multipliers

```python
# Multipliers for special circumstances
OVERTIME_MULTIPLIER = 1.5  # 1.5x for work outside business hours
WEEKEND_MULTIPLIER = 2.0   # 2x for weekend work
ONCALL_MULTIPLIER = 1.2    # 1.2x for on-call incidents
```

**Business hours definition:**
- Monday-Friday, 9 AM - 6 PM
- Comments/work outside these hours → overtime
- Saturday/Sunday → weekend

### Step 5: Rebuild & Test

```powershell
# Rebuild backend
docker-compose up -d --build backend

# Wait 30 seconds
docker-compose ps

# Should show healthy
```

**Test it:**
```powershell
python test_local.py
```

Pick an issue with:
- Assignee in a mapped location
- Comments posted after hours or on weekends

---

## 📊 Example Outputs

### Before (Flat Rate)
```
Assignee: Sarah Chen
Daily cost: $2,500
Total estimated cost: $7,500
```

### After (With Geographic Multipliers)
```
Assignee: Sarah Chen (Senior Engineer, San Francisco)
Daily cost: $6,500 (base: $5,000)
  Multipliers: San Francisco: 1.3x
Total estimated cost: $19,500
```

### With Overtime Detection
```
Assignee: Mike Rodriguez (Mid Engineer, Austin)
Daily cost: $4,500 (base: $3,000)
  Multipliers: Overtime: 1.5x
Total estimated cost: $13,500
⚠️ After-hours work detected
```

### With Weekend Work
```
Assignee: Rajesh Kumar (Senior Engineer, Bangalore)
Daily cost: $4,000 (base: $2,000)
  Multipliers: Bangalore: 0.4x, Weekend: 2.0x
Total estimated cost: $12,000
⚠️ Weekend work detected
```

---

## 💡 Real-World Use Cases

### Use Case 1: Global Team Cost Optimization

**Scenario:** Your team is distributed globally

**Consilo shows:**
```
Sprint Cost Breakdown by Location:
• San Francisco (3 engineers): $58,500/day
• Bangalore (5 engineers): $12,000/day
• Warsaw (2 engineers): $6,000/day

Recommendation: Move low-priority work to Bangalore team
Potential savings: $15,000/day
```

### Use Case 2: Overtime Alert

**Scenario:** Team working excessive after-hours

**Consilo shows:**
```
⚠️ ALERT: 47% of work happening after hours
Overtime cost impact: +$42,000 this sprint
Affected issues: ENG-45, ENG-67, ENG-89

Recommendation: Review workload distribution
```

### Use Case 3: Weekend Incident Response

**Scenario:** Production incident on Saturday

**Consilo shows:**
```
Incident Cost Analysis:
• 3 Senior Engineers (weekend): $30,000/day (2x multiplier)
• On-call multiplier: +20%
Total incident cost: $36,000/day

This could have been prevented with better monitoring
Recommendation: Invest in observability
```

---

## 🔧 Advanced Configuration

### Custom Business Hours by Location

```python
BUSINESS_HOURS_BY_LOCATION = {
    'San Francisco': {'start': 9, 'end': 18, 'timezone': 'America/Los_Angeles'},
    'Bangalore': {'start': 9, 'end': 18, 'timezone': 'Asia/Kolkata'},
    'Warsaw': {'start': 9, 'end': 18, 'timezone': 'Europe/Warsaw'},
}
```

### Seniority-Based Adjustments

```python
SENIORITY_ADJUSTMENTS = {
    '0-2 years': 0.7,    # 70% of base rate
    '2-5 years': 1.0,    # 100% (baseline)
    '5-10 years': 1.3,   # 130%
    '10+ years': 1.5,    # 150%
}
```

### Holiday Multipliers

```python
HOLIDAY_MULTIPLIER = 2.5  # 2.5x for work on holidays

HOLIDAYS = [
    '2026-01-01',  # New Year
    '2026-12-25',  # Christmas
    # Add your company holidays
]
```

---

## 🎯 Validation & Testing

### Test Auto-Detection

```powershell
# Run validation
docker-compose exec backend python -c "from app.core.role_costs import get_user_role, get_rate_summary; get_rate_summary()"
```

Should show:
```
CONFIGURED ROLE RATES
=====================================
Engineering:
  Senior Engineer................. $5,000/day
  ...

GEOGRAPHIC MULTIPLIERS
=====================================
  San Francisco................... 1.3x
  Bangalore....................... 0.4x
  ...

TIME-BASED MULTIPLIERS
=====================================
  Overtime (after hours):......... 1.5x
  Weekend work:................... 2.0x
```

### Test Specific User

```python
from app.core.role_costs import get_user_rate, get_user_location, apply_geographic_multiplier

# Test role detection
rate, role = get_user_rate("Sarah Chen - Senior Engineer")
print(f"Role: {role}, Rate: ${rate}/day")

# Test location
location = get_user_location("Sarah Chen")
final_rate = apply_geographic_multiplier(rate, location)
print(f"Location: {location}, Final rate: ${final_rate}/day")
```

---

## 📈 Business Impact

### Without Geographic/Auto-Detection
```
"Our team costs $50,000/day"
Generic, not actionable
```

### With Geographic/Auto-Detection
```
"Our team costs breakdown:
• US team (30%): $35,000/day
• India team (50%): $8,000/day
• Poland team (20%): $7,000/day

Optimization opportunity:
Shift 20% of work to India → Save $180,000/quarter
```

**This is CFO-level strategic intelligence.**

---

## 💰 Pricing Impact

**Consilo without geographic intelligence:**
- "Jira analytics tool" = $49-149/month

**Consilo with geographic intelligence:**
- "Global workforce cost optimization platform" = $499-999/month
- Enterprise feature = Enterprise pricing

**Companies with distributed teams will pay premium for this.**

---

## ✅ Setup Checklist

- [ ] Configured `LOCATION_MULTIPLIERS` for your team's locations
- [ ] Mapped team members in `USER_LOCATION_MAPPING`
- [ ] Customized `ROLE_DETECTION_PATTERNS` for your naming conventions
- [ ] Set `OVERTIME_MULTIPLIER` and `WEEKEND_MULTIPLIER`
- [ ] Rebuilt backend container
- [ ] Tested with real issues
- [ ] Verified location showing in output
- [ ] Verified multipliers being applied
- [ ] Checked overtime/weekend detection working

---

## 🚀 Next Steps

1. **Today:** Configure locations and patterns
2. **This Week:** Analyze your team's work patterns
3. **Next Week:** Present cost optimization opportunities to leadership
4. **Month 1:** Show ROI from geographic optimization

---

## 🎉 What You Now Have

**Consilo is now a:**
- Global workforce intelligence platform
- Cost optimization tool
- Work pattern analyzer
- Resource allocation advisor

**This is enterprise SaaS at its finest.**

---

Built with ❤️ for Consilo Geographic Intelligence
