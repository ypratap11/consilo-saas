"""
JiraIQ Role-Based Cost Configuration

Define daily rates for different roles in your organization.
Costs are calculated based on team member roles, not a flat rate.

Instructions:
1. Customize the rates below to match your organization
2. Map Jira users to roles in USER_ROLE_MAPPING
3. Set a DEFAULT_RATE for unmapped users
"""

# ==============================================================================
# ROLE DEFINITIONS & DAILY RATES
# ==============================================================================

ROLE_RATES = {
    # Engineering roles
    'Senior Engineer': 5000,
    'Staff Engineer': 6000,
    'Principal Engineer': 7000,
    'Mid Engineer': 3000,
    'Junior Engineer': 2000,
    'Engineering Manager': 6500,
    'Tech Lead': 5500,
    
    # Product & Design
    'Senior PM': 5000,
    'PM': 4000,
    'Associate PM': 2500,
    'Senior Designer': 4500,
    'Designer': 3500,
    'Junior Designer': 2000,
    
    # QA & DevOps
    'Senior QA': 4000,
    'QA Engineer': 3000,
    'DevOps Engineer': 4500,
    'SRE': 5000,
    
    # Data & Analytics
    'Data Engineer': 4500,
    'Data Scientist': 5000,
    'Analytics Engineer': 3500,
    
    # Other
    'Contractor': 3500,
    'Intern': 1000,
    'Consultant': 5000,
}

# ==============================================================================
# USER → ROLE MAPPING
# ==============================================================================

# Option 1: Manual mapping (most accurate)
# Map Jira display names to roles
USER_ROLE_MAPPING = {
    # Example mappings - replace with your actual team
    'Pratap Yeragudipati': 'Senior PM',
    'Sarah Chen': 'Senior Engineer',
    'Mike Rodriguez': 'Mid Engineer',
    'Alex Kim': 'Junior Engineer',
    'Jordan Lee': 'Senior Designer',
    'Taylor Swift': 'QA Engineer',
    
    # Add your team members here:
    # 'John Doe': 'Staff Engineer',
    # 'Jane Smith': 'PM',
    # 'Bob Johnson': 'DevOps Engineer',
}

# Option 1b: Manual location mapping
# Map Jira display names to locations
USER_LOCATION_MAPPING = {
    # Example mappings - replace with your actual team
    'Pratap Yeragudipati': 'San Francisco',
    'Sarah Chen': 'San Francisco',
    'Mike Rodriguez': 'Austin',
    'Alex Kim': 'Remote',
    'Rajesh Kumar': 'Bangalore',
    'Anna Kowalski': 'Warsaw',
    
    # Add your team members here:
    # 'John Doe': 'New York',
    # 'Jane Smith': 'Portland',
}

# Option 2: Auto-detect from Jira custom field
# If your Jira has a "Role" or "Job Title" custom field, specify it here:
JIRA_ROLE_FIELD = None  # e.g., 'customfield_10050' or None to disable

# Option 3: Pattern matching from display names
# Auto-detect roles from naming patterns
ROLE_DETECTION_PATTERNS = {
    # Pattern in display name → Role
    '(Senior|Sr\.).*Engineer': 'Senior Engineer',
    '(Staff|Principal).*Engineer': 'Staff Engineer',
    'Engineer.*Manager': 'Engineering Manager',
    'Tech.*Lead': 'Tech Lead',
    '(Mid|Middle).*Engineer': 'Mid Engineer',
    '(Junior|Jr\.).*Engineer': 'Junior Engineer',
    
    '(Senior|Sr\.).*PM': 'Senior PM',
    'Product.*Manager': 'PM',
    '(Associate|Assoc\.).*PM': 'Associate PM',
    
    '(Senior|Sr\.).*Designer': 'Senior Designer',
    'Designer': 'Designer',
    
    'QA|Quality': 'QA Engineer',
    'DevOps': 'DevOps Engineer',
    'SRE|Reliability': 'SRE',
    
    'Data.*Scientist': 'Data Scientist',
    'Data.*Engineer': 'Data Engineer',
    
    'Contractor': 'Contractor',
    'Intern': 'Intern',
    'Consultant': 'Consultant',
}

# ==============================================================================
# FALLBACK & DEFAULTS
# ==============================================================================

# Default rate for unmapped users (fallback)
DEFAULT_RATE = 3000

# Use this if you want all unmapped users to be treated as a specific role
DEFAULT_ROLE = 'Mid Engineer'  # or None to use DEFAULT_RATE directly

# ==============================================================================
# ADVANCED OPTIONS
# ==============================================================================

# Multipliers for special circumstances
OVERTIME_MULTIPLIER = 1.5  # 1.5x for work outside business hours
WEEKEND_MULTIPLIER = 2.0   # 2x for weekend work
ONCALL_MULTIPLIER = 1.2    # 1.2x for on-call incidents

# Geographic adjustments (if you have distributed teams)
LOCATION_MULTIPLIERS = {
    'San Francisco': 1.3,
    'New York': 1.2,
    'Austin': 1.0,
    'Portland': 1.0,
    'Bangalore': 0.4,
    'Warsaw': 0.5,
    'Remote': 1.0,
}

# Seniority level override (if you want to adjust by years of experience)
SENIORITY_ADJUSTMENTS = {
    '0-2 years': 0.7,    # 70% of base rate
    '2-5 years': 1.0,    # 100% (no adjustment)
    '5-10 years': 1.3,   # 130%
    '10+ years': 1.5,    # 150%
}

# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_config():
    """Validate configuration is properly set up"""
    errors = []
    
    # Check if rates are defined
    if not ROLE_RATES:
        errors.append("ROLE_RATES is empty - define at least one role")
    
    # Check if default rate is set
    if DEFAULT_RATE <= 0:
        errors.append("DEFAULT_RATE must be positive")
    
    # Check if any users are mapped
    if not USER_ROLE_MAPPING:
        print("⚠️  Warning: USER_ROLE_MAPPING is empty - using defaults for all users")
    
    # Validate user mappings point to valid roles
    for user, role in USER_ROLE_MAPPING.items():
        if role not in ROLE_RATES:
            errors.append(f"User '{user}' mapped to unknown role '{role}'")
    
    # Validate default role exists
    if DEFAULT_ROLE and DEFAULT_ROLE not in ROLE_RATES:
        errors.append(f"DEFAULT_ROLE '{DEFAULT_ROLE}' not found in ROLE_RATES")
    
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Role configuration validated successfully")
    return True

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_user_role(display_name, jira_user_obj=None):
    """
    Get role for a user, trying multiple methods:
    1. Direct mapping from USER_ROLE_MAPPING
    2. Jira custom field (if configured)
    3. Pattern matching from display name
    4. Default role/rate
    """
    import re
    
    # Method 1: Direct mapping
    if display_name in USER_ROLE_MAPPING:
        return USER_ROLE_MAPPING[display_name]
    
    # Method 2: Jira custom field (if available and configured)
    if jira_user_obj and JIRA_ROLE_FIELD:
        try:
            custom_role = getattr(jira_user_obj, JIRA_ROLE_FIELD, None)
            if custom_role and custom_role in ROLE_RATES:
                return custom_role
        except:
            pass
    
    # Method 3: Pattern matching
    for pattern, role in ROLE_DETECTION_PATTERNS.items():
        if re.search(pattern, display_name, re.IGNORECASE):
            return role
    
    # Method 4: Default
    return DEFAULT_ROLE if DEFAULT_ROLE else None


def get_user_rate(display_name, jira_user_obj=None):
    """Get daily rate for a user"""
    role = get_user_role(display_name, jira_user_obj)
    
    if role and role in ROLE_RATES:
        return ROLE_RATES[role], role
    else:
        return DEFAULT_RATE, 'Unknown (using default)'


def get_user_location(display_name, jira_user_obj=None):
    """
    Get location for a user, trying multiple methods:
    1. Direct mapping from USER_LOCATION_MAPPING
    2. Jira custom field (if configured)
    3. Default to None
    """
    # Method 1: Direct mapping
    if display_name in USER_LOCATION_MAPPING:
        return USER_LOCATION_MAPPING[display_name]
    
    # Method 2: Jira custom field (if available)
    # Example: customfield_10051 might be "Location" or "Office"
    if jira_user_obj:
        try:
            # Try common location field names
            for field in ['location', 'timeZone', 'office']:
                location = getattr(jira_user_obj, field, None)
                if location:
                    # Try to match to known locations
                    location_str = str(location).lower()
                    for known_location in LOCATION_MULTIPLIERS.keys():
                        if known_location.lower() in location_str:
                            return known_location
        except:
            pass
    
    # Method 3: Default to None
    return None


def apply_geographic_multiplier(base_cost, location):
    """Apply geographic cost multiplier"""
    if location in LOCATION_MULTIPLIERS:
        multiplier = LOCATION_MULTIPLIERS[location]
        return base_cost * multiplier
    return base_cost


def is_overtime(timestamp):
    """
    Check if timestamp is outside normal business hours
    Business hours: 9 AM - 6 PM Monday-Friday
    """
    from datetime import datetime
    
    try:
        # Parse timestamp (handle both string and datetime objects)
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        # Check if weekend
        if dt.weekday() >= 5:  # Saturday or Sunday
            return False  # Weekend is handled separately
        
        # Check if outside 9 AM - 6 PM
        hour = dt.hour
        if hour < 9 or hour >= 18:
            return True
        
        return False
    except:
        return False


def is_weekend(timestamp):
    """Check if timestamp is on weekend"""
    from datetime import datetime
    
    try:
        # Parse timestamp
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        # Check if Saturday (5) or Sunday (6)
        return dt.weekday() >= 5
    except:
        return False


def get_rate_summary():
    """Print summary of configured rates"""
    print("\n" + "="*60)
    print("CONFIGURED ROLE RATES")
    print("="*60)
    
    # Group by category
    categories = {
        'Engineering': ['Senior Engineer', 'Staff Engineer', 'Principal Engineer', 
                       'Mid Engineer', 'Junior Engineer', 'Engineering Manager', 'Tech Lead'],
        'Product & Design': ['Senior PM', 'PM', 'Associate PM', 
                            'Senior Designer', 'Designer', 'Junior Designer'],
        'QA & DevOps': ['Senior QA', 'QA Engineer', 'DevOps Engineer', 'SRE'],
        'Data': ['Data Engineer', 'Data Scientist', 'Analytics Engineer'],
        'Other': ['Contractor', 'Intern', 'Consultant'],
    }
    
    for category, roles in categories.items():
        print(f"\n{category}:")
        for role in roles:
            if role in ROLE_RATES:
                print(f"  {role:.<40} ${ROLE_RATES[role]:>5,}/day")
    
    print(f"\nDefault rate (unmapped users): ${DEFAULT_RATE:,}/day")
    print(f"Mapped users: {len(USER_ROLE_MAPPING)}")
    
    # Show location multipliers
    if LOCATION_MULTIPLIERS:
        print("\n" + "="*60)
        print("GEOGRAPHIC MULTIPLIERS")
        print("="*60)
        for location, multiplier in sorted(LOCATION_MULTIPLIERS.items()):
            print(f"  {location:.<40} {multiplier:>5.1f}x")
        print(f"Mapped locations: {len(USER_LOCATION_MAPPING)}")
    
    # Show time-based multipliers
    print("\n" + "="*60)
    print("TIME-BASED MULTIPLIERS")
    print("="*60)
    print(f"  Overtime (after hours):........... {OVERTIME_MULTIPLIER}x")
    print(f"  Weekend work:..................... {WEEKEND_MULTIPLIER}x")
    print(f"  On-call incidents:................ {ONCALL_MULTIPLIER}x")
    
    print("="*60 + "\n")


# Run validation when imported
if __name__ == "__main__":
    validate_config()
    get_rate_summary()
