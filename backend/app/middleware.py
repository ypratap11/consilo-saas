"""
Consilo Middleware

- Tenant isolation via X-Tenant-ID header
- Credential encryption/decryption
- Usage tracking
"""

import os
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from typing import Optional
import time

from .database import get_db
from .models import Tenant, UsageLog

# Encryption key for Jira tokens (store in environment variable)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development (NEVER do this in production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"⚠️  WARNING: Using generated encryption key. Set ENCRYPTION_KEY in production!")
    print(f"Generated key: {ENCRYPTION_KEY}")

fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    """Encrypt Jira API token for storage"""
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt Jira API token for use"""
    return fernet.decrypt(encrypted_token.encode()).decode()


async def get_current_tenant(
    request: Request,
    db: Session = Depends(get_db)
) -> Tenant:
    """
    FastAPI dependency to get current tenant from X-Tenant-ID header.
    
    Usage in routes:
        @app.get("/protected")
        def route(tenant: Tenant = Depends(get_current_tenant)):
            ...
    """
    tenant_id = request.headers.get("X-Tenant-ID")
    
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Tenant-ID header"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant {tenant_id} not found"
        )
    
    if tenant.status not in ["trial", "active"]:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant account is {tenant.status}"
        )
    
    return tenant


async def check_usage_limit(
    tenant: Tenant,
    action_type: str,  # "issue", "sprint", "portfolio"
    db: Session
) -> bool:
    """
    Check if tenant has exceeded their usage limits for the current month.
    Returns True if within limits, raises HTTPException if exceeded.
    """
    from sqlalchemy import func, extract
    from datetime import datetime
    
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    
    # Count usage this month
    usage_count = db.query(func.count(UsageLog.id)).filter(
        UsageLog.tenant_id == tenant.id,
        UsageLog.action_type == action_type,
        extract('month', UsageLog.created_at) == current_month,
        extract('year', UsageLog.created_at) == current_year
    ).scalar()
    
    # Check against limits
    limits = {
        "issue": tenant.monthly_issue_limit,
        "sprint": tenant.monthly_sprint_limit,
        "portfolio": tenant.monthly_portfolio_limit
    }
    
    limit = limits.get(action_type, 0)
    
    if usage_count >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly {action_type} analysis limit ({limit}) exceeded. Upgrade your plan or wait for next billing cycle."
        )
    
    return True


async def log_usage(
    tenant_id: str,
    action_type: str,
    resource_key: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    db: Session = None
):
    """
    Log API usage for billing and analytics.
    """
    if not db:
        from .database import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        log = UsageLog(
            tenant_id=tenant_id,
            action_type=action_type,
            resource_key=resource_key,
            processing_time_ms=processing_time_ms
        )
        db.add(log)
        db.commit()
    finally:
        if should_close:
            db.close()


class UsageTrackingMiddleware:
    """
    Middleware to automatically track processing time and log usage.
    """
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        processing_time = int((time.time() - start_time) * 1000)  # ms
        
        # Add processing time to response headers
        response.headers["X-Processing-Time-Ms"] = str(processing_time)
        
        return response
