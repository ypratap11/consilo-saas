"""
Authentication Middleware

Protects API routes with JWT authentication and maps users to tenants.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.auth.clerk import clerk_auth
from app.database import get_db
from app.models import Tenant, User


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify JWT token and return current user.
    
    Creates user record if first login.
    Maps user to tenant (creates tenant if needed).
    """
    # Verify token
    token = credentials.credentials
    claims = clerk_auth.verify_token(token)
    
    # Extract user info
    clerk_user_id = clerk_auth.get_user_id(claims)
    email = clerk_auth.get_user_email(claims)
    name = clerk_auth.get_user_name(claims)
    
    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    # Get or create user
    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    
    if not user:
        # First login - create user
        user = User(
            id=uuid.uuid4(),
            clerk_user_id=clerk_user_id,
            email=email,
            full_name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


async def get_current_tenant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Get tenant for current user.
    
    Creates tenant if user doesn't have one yet (first login).
    """
    # Check if user has a tenant
    if not user.tenant_id:
        # First login - create tenant with trial
        from datetime import datetime, timedelta
        
        tenant = Tenant(
            id=uuid.uuid4(),
            company_name=user.email.split('@')[1] if user.email else "My Company",
            owner_user_id=user.id,
            plan="starter",
            status="trial",
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            # Default limits for trial (same as starter plan)
            monthly_issues_limit=200,
            monthly_sprints_limit=5,
            monthly_portfolios_limit=1,
            daily_rate_per_person=2500
        )
        db.add(tenant)
        
        # Link user to tenant
        user.tenant_id = tenant.id
        
        db.commit()
        db.refresh(tenant)
    else:
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
    
    return tenant


async def require_active_subscription(
    tenant: Tenant = Depends(get_current_tenant)
) -> Tenant:
    """
    Require tenant to have active subscription (not trial or cancelled).
    
    Use this for premium features.
    """
    from datetime import datetime
    
    # Check if trial expired
    if tenant.status == "trial":
        if tenant.trial_ends_at and tenant.trial_ends_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Trial has expired. Please upgrade to continue."
            )
    
    # Check if subscription active
    if tenant.status not in ["trial", "active"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Subscription is {tenant.status}. Please reactivate to continue."
        )
    
    return tenant


def check_usage_limit(
    tenant: Tenant,
    action_type: str,
    db: Session
) -> None:
    """
    Check if tenant has exceeded usage limits for the current billing period.
    
    Args:
        tenant: Tenant object
        action_type: Type of action (issue/sprint/portfolio)
        db: Database session
        
    Raises:
        HTTPException: If limit exceeded
    """
    from app.models import UsageLog
    from datetime import datetime
    from sqlalchemy import func, extract
    
    # Get current month usage
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    usage_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant.id,
        UsageLog.action_type == action_type,
        extract('month', UsageLog.created_at) == current_month,
        extract('year', UsageLog.created_at) == current_year
    ).scalar()
    
    # Check limits based on action type
    limits = {
        'issue': tenant.monthly_issues_limit,
        'sprint': tenant.monthly_sprints_limit,
        'portfolio': tenant.monthly_portfolios_limit
    }
    
    limit = limits.get(action_type, float('inf'))
    
    if usage_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly {action_type} analysis limit ({limit}) reached. "
                   f"Upgrade your plan for higher limits."
        )
    
    # Warn at 80% usage
    if usage_count >= limit * 0.8:
        import warnings
        warnings.warn(
            f"Approaching {action_type} limit: {usage_count}/{limit} used this month"
        )
