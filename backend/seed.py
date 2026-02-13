"""
Database seeder - populate initial data
Run once after first deployment to create subscription plans
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import SubscriptionPlan

def seed_plans():
    """Create subscription plan records"""
    db = SessionLocal()
    
    # Check if plans already exist
    existing = db.query(SubscriptionPlan).count()
    if existing > 0:
        print(f"✅ Plans already seeded ({existing} plans found)")
        return
    
    plans = [
        SubscriptionPlan(
            id="starter",
            name="Starter",
            price_monthly=49.0,
            issue_analyses_monthly=200,
            sprint_analyses_monthly=5,
            portfolio_analyses_monthly=1,
            csv_export=False,
            api_access=False,
            custom_risk_weights=False,
            slack_integration=False
        ),
        SubscriptionPlan(
            id="growth",
            name="Growth",
            price_monthly=149.0,
            issue_analyses_monthly=9999999,  # "Unlimited"
            sprint_analyses_monthly=20,
            portfolio_analyses_monthly=5,
            csv_export=True,
            api_access=False,
            custom_risk_weights=False,
            slack_integration=True
        ),
        SubscriptionPlan(
            id="enterprise",
            name="Enterprise",
            price_monthly=499.0,
            issue_analyses_monthly=9999999,
            sprint_analyses_monthly=9999999,
            portfolio_analyses_monthly=9999999,
            csv_export=True,
            api_access=True,
            custom_risk_weights=True,
            slack_integration=True
        )
    ]
    
    for plan in plans:
        db.add(plan)
        print(f"Created plan: {plan.name} (${plan.price_monthly}/mo)")
    
    db.commit()
    db.close()
    print("\n✅ Subscription plans seeded successfully!")

if __name__ == "__main__":
    print("🌱 Seeding database with initial data...\n")
    seed_plans()
