# ⚡ Quick Setup: Geographic & Auto-Detection

**Enable all advanced cost modeling features in 5 minutes**

---

## What You're Enabling

✅ **Role-based costs** (Senior Eng: $5K, Junior: $2K)  
✅ **Geographic multipliers** (SF: 1.3x, Bangalore: 0.4x)  
✅ **Auto-detection** (detect roles from names)  
✅ **Overtime detection** (after-hours: 1.5x)  
✅ **Weekend detection** (weekend work: 2.0x)

---

## Step 1: Edit role_costs.py (3 minutes)

```powershell
notepad backend\app\core\role_costs.py
```

### A. Add Your Team Locations

Find this section and customize:

```python
USER_LOCATION_MAPPING = {
    # Your team - update these!
    'Pratap Yeragudipati': 'San Francisco',
    'Sarah Chen': 'San Francisco',
    'Mike Rodriguez': 'Austin',
    'Rajesh Kumar': 'Bangalore',
    
    # Add your team here:
    # 'Your Name': 'Your Location',
}
```

### B. Configure Location Multipliers

Already configured with sensible defaults:

```python
LOCATION_MULTIPLIERS = {
    'San Francisco': 1.3,   # Keep or adjust
    'New York': 1.2,
    'Austin': 1.0,
    'Bangalore': 0.4,       # Keep or adjust
    'Warsaw': 0.5,
    'Remote': 1.0,
}
```

### C. Time-Based Multipliers

Already configured:

```python
OVERTIME_MULTIPLIER = 1.5   # After hours (9 PM - 9 AM)
WEEKEND_MULTIPLIER = 2.0    # Saturday/Sunday
ONCALL_MULTIPLIER = 1.2     # On-call incidents
```

**Save and close.**

---

## Step 2: Rebuild Backend (1 minute)

```powershell
docker-compose up -d --build backend
```

Wait 30 seconds:

```powershell
docker-compose ps
```

Should show `consilo-api` as **healthy**.

---

## Step 3: Test It (1 minute)

```powershell
python test_local.py
```

Analyze an issue. You should now see:

```
Assignee: Pratap Yeragudipati (Senior PM, San Francisco)
Daily cost: $6,500 (base: $5,000)
  Multipliers: San Francisco: 1.3x
Total estimated cost: $19,500
```

---

## ✅ Success Criteria

**You know it's working when you see:**

1. **Location in output:**
   ```
   Assignee: Name (Role, Location)
   ```

2. **Multipliers applied:**
   ```
   Daily cost: $6,500 (base: $5,000)
     Multipliers: San Francisco: 1.3x
   ```

3. **Overtime/weekend warnings:**
   ```
   ⚠️ After-hours work detected
   ⚠️ Weekend work detected
   ```

---

## 🎯 What This Unlocks

### Before
```
Team cost: $50,000/day
```

### After
```
Team cost breakdown:
• US team (3 people, SF): $35,000/day
• India team (5 people, Bangalore): $10,000/day  
• Poland team (2 people, Warsaw): $5,000/day

Overtime impact: +$8,000/day
Weekend work: +$4,000/day

Optimization: Shift work to India → Save $180K/quarter
```

**This is strategic intelligence.**

---

## 🔧 Troubleshooting

### Location not showing?

1. Check spelling in `USER_LOCATION_MAPPING`
2. Must match Jira display name exactly
3. Or add to pattern matching

### Multipliers not applied?

1. Verify location is in `LOCATION_MULTIPLIERS`
2. Check backend logs: `docker-compose logs backend | grep -i multi`
3. Rebuild: `docker-compose up -d --build backend`

### Still showing flat rate?

1. Make sure you saved `role_costs.py`
2. Rebuild container (Step 2)
3. Check file is in container:
   ```powershell
   docker-compose exec backend ls -la /app/app/core/role_costs.py
   ```

---

## 🎨 Customization Examples

### Example 1: Your Company Has 4 Offices

```python
LOCATION_MULTIPLIERS = {
    'San Francisco HQ': 1.3,
    'NYC Office': 1.2,
    'Austin Office': 1.0,
    'Bangalore Office': 0.35,
}

USER_LOCATION_MAPPING = {
    'Person 1': 'San Francisco HQ',
    'Person 2': 'NYC Office',
    'Person 3': 'Austin Office',
    'Person 4': 'Bangalore Office',
}
```

### Example 2: Different Business Hours

```python
# In role_costs.py, update is_overtime() function
def is_overtime(timestamp):
    hour = dt.hour
    # Your business hours: 8 AM - 5 PM
    if hour < 8 or hour >= 17:
        return True
    return False
```

### Example 3: Higher Weekend Multiplier

```python
WEEKEND_MULTIPLIER = 3.0  # 3x for weekend work (discourage it)
```

---

## 📊 Validation

Run this to verify configuration:

```powershell
docker-compose exec backend python /app/app/core/role_costs.py
```

Should show:

```
CONFIGURED ROLE RATES
=====================
Engineering:
  Senior Engineer.... $5,000/day
  Mid Engineer....... $3,000/day
  ...

GEOGRAPHIC MULTIPLIERS
=====================
  San Francisco...... 1.3x
  Bangalore.......... 0.4x
  ...

TIME-BASED MULTIPLIERS
=====================
  Overtime........... 1.5x
  Weekend............ 2.0x
```

---

## 💰 Business Value

**This feature set:**
- Justifies $149-499/month pricing ✅
- Differentiates from all competitors ✅
- Provides strategic intelligence ✅
- Shows clear ROI in cost savings ✅

**Companies with global teams will pay premium for this.**

---

## 🎉 You're Done!

**Consilo now has:**
- ✅ Role-based costs
- ✅ Geographic adjustments
- ✅ Auto-detection
- ✅ Overtime tracking
- ✅ Weekend work detection

**This is enterprise-grade workforce intelligence.**

---

**Next:** Read `GEOGRAPHIC_SETUP.md` for advanced configuration options.
