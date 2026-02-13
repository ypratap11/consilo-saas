"""
Stripe Webhook Handlers

Process Stripe payment events and update tenant subscriptions.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import Tenant
from app.billing.stripe_client import stripe_client


router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


# Plan limits configuration
PLAN_LIMITS = {
    "starter": {
        "monthly_issue_limit": 200,
        "monthly_sprint_limit": 5,
        "monthly_portfolio_limit": 1,
    },
    "growth": {
        "monthly_issue_limit": 99999,  # Unlimited
        "monthly_sprint_limit": 20,
        "monthly_portfolio_limit": 5,
    },
    "enterprise": {
        "monthly_issue_limit": 99999,  # Unlimited
        "monthly_sprint_limit": 99999,  # Unlimited
        "monthly_portfolio_limit": 99999,  # Unlimited
    }
}


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Events processed:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Verify webhook signature
    try:
        event = stripe_client.verify_webhook_signature(payload, signature)
    except HTTPException:
        raise
    
    # Process event
    event_type = event["type"]
    logger.info(f"Processing Stripe webhook: {event_type}")
    
    try:
        if event_type == "customer.subscription.created":
            await handle_subscription_created(event.data.object, db)
        
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event.data.object, db)
        
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(event.data.object, db)
        
        elif event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(event.data.object, db)
        
        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(event.data.object, db)
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
    return {"status": "success"}


async def handle_subscription_created(subscription, db: Session):
    """
    Handle new subscription creation.
    
    Activates tenant subscription and sets limits.
    """
    customer_id = subscription.customer
    subscription_id = subscription.id
    
    # Find tenant by Stripe customer ID
    tenant = db.query(Tenant).filter(
        Tenant.stripe_customer_id == customer_id
    ).first()
    
    if not tenant:
        logger.error(f"Tenant not found for customer: {customer_id}")
        return
    
    # Get plan from subscription metadata or price
    metadata = subscription.metadata
    plan = metadata.get("plan", "starter")
    
    # Update tenant
    tenant.stripe_subscription_id = subscription_id
    tenant.plan = plan
    tenant.status = "active"
    tenant.trial_ends_at = None  # Clear trial
    
    # Set plan limits
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
    tenant.monthly_issue_limit = limits["monthly_issue_limit"]
    tenant.monthly_sprint_limit = limits["monthly_sprint_limit"]
    tenant.monthly_portfolio_limit = limits["monthly_portfolio_limit"]
    
    db.commit()
    
    logger.info(f"Subscription created for tenant {tenant.id}: {plan}")


async def handle_subscription_updated(subscription, db: Session):
    """
    Handle subscription updates (plan changes, status changes).
    """
    subscription_id = subscription.id
    
    # Find tenant
    tenant = db.query(Tenant).filter(
        Tenant.stripe_subscription_id == subscription_id
    ).first()
    
    if not tenant:
        logger.error(f"Tenant not found for subscription: {subscription_id}")
        return
    
    # Update status
    stripe_status = subscription.status
    status_mapping = {
        "active": "active",
        "past_due": "past_due",
        "canceled": "cancelled",
        "unpaid": "past_due",
        "incomplete": "trial",
        "trialing": "trial"
    }
    tenant.status = status_mapping.get(stripe_status, "active")
    
    # If plan changed, update limits
    if subscription.items and subscription.items.data:
        price_id = subscription.items.data[0].price.id
        
        # Map price ID to plan name
        plan = None
        for plan_name, pid in stripe_client.price_ids.items():
            if pid == price_id:
                plan = plan_name
                break
        
        if plan and plan != tenant.plan:
            tenant.plan = plan
            limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
            tenant.monthly_issue_limit = limits["monthly_issue_limit"]
            tenant.monthly_sprint_limit = limits["monthly_sprint_limit"]
            tenant.monthly_portfolio_limit = limits["monthly_portfolio_limit"]
            logger.info(f"Tenant {tenant.id} plan changed to {plan}")
    
    db.commit()


async def handle_subscription_deleted(subscription, db: Session):
    """
    Handle subscription cancellation.
    
    Downgrades tenant to free plan with limited access.
    """
    subscription_id = subscription.id
    
    # Find tenant
    tenant = db.query(Tenant).filter(
        Tenant.stripe_subscription_id == subscription_id
    ).first()
    
    if not tenant:
        logger.error(f"Tenant not found for subscription: {subscription_id}")
        return
    
    # Downgrade to free/cancelled
    tenant.status = "cancelled"
    tenant.plan = "free"
    tenant.stripe_subscription_id = None
    
    # Set very limited free tier
    tenant.monthly_issue_limit = 10  # Very limited free tier
    tenant.monthly_sprint_limit = 0
    tenant.monthly_portfolio_limit = 0
    
    db.commit()
    
    logger.info(f"Subscription cancelled for tenant {tenant.id}")


async def handle_payment_succeeded(invoice, db: Session):
    """
    Handle successful payment.
    
    Resets usage counters at start of new billing period.
    """
    customer_id = invoice.customer
    
    # Find tenant
    tenant = db.query(Tenant).filter(
        Tenant.stripe_customer_id == customer_id
    ).first()
    
    if not tenant:
        logger.error(f"Tenant not found for customer: {customer_id}")
        return
    
    # If status was past_due, reactivate
    if tenant.status == "past_due":
        tenant.status = "active"
        db.commit()
        logger.info(f"Tenant {tenant.id} reactivated after successful payment")
    
    # Note: Usage counter reset happens automatically via monthly billing cycle check
    # in the usage tracking middleware


async def handle_payment_failed(invoice, db: Session):
    """
    Handle failed payment.
    
    Marks tenant as past_due, sends dunning email (TODO).
    """
    customer_id = invoice.customer
    
    # Find tenant
    tenant = db.query(Tenant).filter(
        Tenant.stripe_customer_id == customer_id
    ).first()
    
    if not tenant:
        logger.error(f"Tenant not found for customer: {customer_id}")
        return
    
    # Mark as past due
    tenant.status = "past_due"
    db.commit()
    
    logger.warning(f"Payment failed for tenant {tenant.id}")
    
    # TODO: Send dunning email to tenant owner
    # This would integrate with email service (SendGrid, Resend, etc.)
