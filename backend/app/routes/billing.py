"""
Billing Routes

Handle subscription checkout, upgrades, downgrades, and billing portal access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Tenant, User
from app.auth.middleware import get_current_user, get_current_tenant
from app.billing.stripe_client import stripe_client


router = APIRouter(prefix="/api/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    """Request to create checkout session"""
    plan: str  # starter, growth, enterprise
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Response with checkout URL"""
    checkout_url: str
    session_id: str


class PortalRequest(BaseModel):
    """Request to create billing portal session"""
    return_url: str


class PortalResponse(BaseModel):
    """Response with portal URL"""
    portal_url: str


class SubscriptionInfo(BaseModel):
    """Current subscription information"""
    plan: str
    status: str
    trial_ends_at: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    monthly_issues_used: int
    monthly_issues_limit: int
    monthly_sprints_used: int
    monthly_sprints_limit: int
    monthly_portfolios_used: int
    monthly_portfolios_limit: int


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create Stripe checkout session for subscription.
    
    User will be redirected to Stripe to complete payment.
    """
    # Validate plan
    valid_plans = ["starter", "growth", "enterprise"]
    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}"
        )
    
    # Get price ID for plan
    price_id = stripe_client.price_ids.get(request.plan)
    if not price_id:
        raise HTTPException(
            status_code=500,
            detail=f"Price ID not configured for plan: {request.plan}"
        )
    
    # Create or get Stripe customer
    if not tenant.stripe_customer_id:
        customer = stripe_client.create_customer(
            email=user.email,
            name=user.full_name or user.email,
            metadata={
                "tenant_id": str(tenant.id),
                "user_id": str(user.id)
            }
        )
        tenant.stripe_customer_id = customer.id
        db.commit()
    
    # Create checkout session
    session = stripe_client.create_checkout_session(
        customer_id=tenant.stripe_customer_id,
        price_id=price_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        metadata={
            "tenant_id": str(tenant.id),
            "plan": request.plan
        },
        trial_days=0  # Trial already handled separately
    )
    
    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.id
    )


@router.post("/portal", response_model=PortalResponse)
async def create_billing_portal_session(
    request: PortalRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Create Stripe billing portal session.
    
    Allows customer to manage subscription, payment methods, invoices.
    """
    if not tenant.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer found. Please subscribe first."
        )
    
    session = stripe_client.create_billing_portal_session(
        customer_id=tenant.stripe_customer_id,
        return_url=request.return_url
    )
    
    return PortalResponse(portal_url=session.url)


@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription_info(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get current subscription information and usage stats.
    """
    from datetime import datetime
    from sqlalchemy import func, extract
    from app.models import UsageLog
    
    # Get current month usage
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    issues_used = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant.id,
        UsageLog.action_type == "issue",
        extract('month', UsageLog.created_at) == current_month,
        extract('year', UsageLog.created_at) == current_year
    ).scalar() or 0
    
    sprints_used = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant.id,
        UsageLog.action_type == "sprint",
        extract('month', UsageLog.created_at) == current_month,
        extract('year', UsageLog.created_at) == current_year
    ).scalar() or 0
    
    portfolios_used = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant.id,
        UsageLog.action_type == "portfolio",
        extract('month', UsageLog.created_at) == current_month,
        extract('year', UsageLog.created_at) == current_year
    ).scalar() or 0
    
    # Get Stripe subscription info if active
    current_period_end = None
    cancel_at_period_end = False
    
    if tenant.stripe_subscription_id:
        try:
            subscription = stripe_client.get_subscription(tenant.stripe_subscription_id)
            current_period_end = datetime.fromtimestamp(
                subscription.current_period_end
            ).isoformat()
            cancel_at_period_end = subscription.cancel_at_period_end
        except:
            pass
    
    return SubscriptionInfo(
        plan=tenant.plan,
        status=tenant.status,
        trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        monthly_issues_used=issues_used,
        monthly_issues_limit=tenant.monthly_issue_limit,
        monthly_sprints_used=sprints_used,
        monthly_sprints_limit=tenant.monthly_sprint_limit,
        monthly_portfolios_used=portfolios_used,
        monthly_portfolios_limit=tenant.monthly_portfolio_limit
    )


@router.post("/upgrade")
async def upgrade_subscription(
    plan: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Upgrade subscription to higher plan.
    
    Prorated automatically by Stripe.
    """
    valid_plans = ["starter", "growth", "enterprise"]
    if plan not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}"
        )
    
    if not tenant.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription. Please subscribe first."
        )
    
    # Get price ID for new plan
    price_id = stripe_client.price_ids.get(plan)
    if not price_id:
        raise HTTPException(
            status_code=500,
            detail=f"Price ID not configured for plan: {plan}"
        )
    
    # Update subscription in Stripe
    subscription = stripe_client.update_subscription(
        subscription_id=tenant.stripe_subscription_id,
        new_price_id=price_id,
        proration_behavior="create_prorations"  # Prorate the difference
    )
    
    # Update tenant plan (limits updated via webhook)
    return {
        "message": f"Upgraded to {plan}",
        "subscription_id": subscription.id,
        "status": subscription.status
    }


@router.post("/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Cancel subscription.
    
    If at_period_end=True, subscription stays active until end of billing period.
    If at_period_end=False, cancels immediately.
    """
    if not tenant.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription to cancel."
        )
    
    subscription = stripe_client.cancel_subscription(
        subscription_id=tenant.stripe_subscription_id,
        at_period_end=at_period_end
    )
    
    return {
        "message": "Subscription cancelled" + (" at period end" if at_period_end else " immediately"),
        "subscription_id": subscription.id,
        "cancel_at": subscription.cancel_at if at_period_end else None
    }
