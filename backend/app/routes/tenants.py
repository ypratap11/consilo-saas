"""
Tenant management endpoints
- Create tenant
- Get tenant info
- Update tenant
- Delete tenant
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Tenant, UsageLog
from ..schemas import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    UsageStats
)
from ..middleware import encrypt_token, decrypt_token

router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=201)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant account.
    
    This is typically called during signup/onboarding.
    In production, this would be protected by admin auth or webhook from Clerk/Auth0.
    """
    
    # Check if tenant with same Jira URL already exists
    existing = db.query(Tenant).filter(
        Tenant.jira_url == tenant_data.jira_url
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant with Jira URL {tenant_data.jira_url} already exists"
        )
    
    # Encrypt Jira token
    encrypted_token = encrypt_token(tenant_data.jira_token)
    
    # Create tenant
    tenant = Tenant(
        company_name=tenant_data.company_name,
        jira_url=tenant_data.jira_url,
        jira_email=tenant_data.jira_email,
        jira_token_encrypted=encrypted_token,
        daily_rate_per_person=tenant_data.daily_rate_per_person,
        plan="starter",
        status="trial"
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get tenant information"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    updates: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update tenant settings"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Update fields if provided
    if updates.company_name is not None:
        tenant.company_name = updates.company_name
    if updates.jira_url is not None:
        tenant.jira_url = updates.jira_url
    if updates.jira_email is not None:
        tenant.jira_email = updates.jira_email
    if updates.jira_token is not None:
        tenant.jira_token_encrypted = encrypt_token(updates.jira_token)
    if updates.daily_rate_per_person is not None:
        tenant.daily_rate_per_person = updates.daily_rate_per_person
    
    db.commit()
    db.refresh(tenant)
    
    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Delete tenant account"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    db.delete(tenant)
    db.commit()
    
    return {"message": f"Tenant {tenant_id} deleted successfully"}


@router.get("/{tenant_id}/usage", response_model=UsageStats)
def get_usage_stats(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current month usage statistics for a tenant.
    Used to display usage limits in dashboard.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Count usage by type for current month
    now = datetime.utcnow()
    
    issue_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant_id,
        UsageLog.action_type == "issue",
        extract('month', UsageLog.created_at) == now.month,
        extract('year', UsageLog.created_at) == now.year
    ).scalar()
    
    sprint_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant_id,
        UsageLog.action_type == "sprint",
        extract('month', UsageLog.created_at) == now.month,
        extract('year', UsageLog.created_at) == now.year
    ).scalar()
    
    portfolio_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant_id,
        UsageLog.action_type == "portfolio",
        extract('month', UsageLog.created_at) == now.month,
        extract('year', UsageLog.created_at) == now.year
    ).scalar()
    
    total_count = issue_count + sprint_count + portfolio_count
    
    return UsageStats(
        tenant_id=tenant_id,
        period=now.strftime("%Y-%m"),
        issue_analyses=issue_count,
        sprint_analyses=sprint_count,
        portfolio_analyses=portfolio_count,
        total_calls=total_count,
        issue_limit=tenant.monthly_issue_limit,
        sprint_limit=tenant.monthly_sprint_limit,
        portfolio_limit=tenant.monthly_portfolio_limit,
        issue_remaining=max(0, tenant.monthly_issue_limit - issue_count),
        sprint_remaining=max(0, tenant.monthly_sprint_limit - sprint_count),
        portfolio_remaining=max(0, tenant.monthly_portfolio_limit - portfolio_count)
    )
