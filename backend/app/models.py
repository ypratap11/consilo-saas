"""
SQLAlchemy models for Consilo SaaS

Tables:
- tenants: Company/team accounts with encrypted Jira credentials
- usage_logs: Track API usage for billing
- analysis_history: Store analysis results for trends
- subscription_plans: Pricing tiers and limits
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base

class User(Base):
    """
    User accounts - maps Clerk users to tenants.
    
    A user can belong to one tenant (for now).
    Future: support multiple tenants per user for team collaboration.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Tenant relationship (one user = one tenant for MVP)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.email}>"

class Tenant(Base):
    """
    Tenant represents a customer account (company/team).
    Each tenant has isolated Jira credentials and usage limits.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    
    # Owner (the user who created this tenant)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Jira credentials (encrypted in application layer)
    jira_url = Column(String(500), nullable=False)
    jira_email = Column(String(255), nullable=False)
    jira_token_encrypted = Column(Text, nullable=False)  # Encrypted with Fernet
    
    # Subscription
    plan = Column(String(50), default="starter")  # starter, growth, enterprise
    status = Column(String(50), default="trial")  # trial, active, suspended, cancelled
    
    # Usage limits (based on plan)
    monthly_issue_limit = Column(Integer, default=200)
    monthly_sprint_limit = Column(Integer, default=5)
    monthly_portfolio_limit = Column(Integer, default=1)
    
    # Cost modeling
    daily_rate_per_person = Column(Float, default=2500.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Stripe integration (Week 2)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Tenant {self.company_name} ({self.plan})>"


class UsageLog(Base):
    """
    Track every API call for billing and analytics.
    """
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # What was analyzed
    action_type = Column(String(50), nullable=False)  # issue, sprint, portfolio
    resource_key = Column(String(255), nullable=True)  # Issue key, project key, etc.
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<UsageLog {self.action_type} at {self.created_at}>"


class AnalysisHistory(Base):
    """
    Store analysis results for historical trending and comparison.
    This enables "Risk over time" charts and trend detection.
    """
    __tablename__ = "analysis_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # What was analyzed
    issue_key = Column(String(50), nullable=False, index=True)
    project_key = Column(String(50), nullable=False, index=True)
    
    # Core metrics (for trending)
    risk_score = Column(Integer, nullable=False)
    daily_cost = Column(Float, nullable=False)
    blocker_count = Column(Integer, default=0)
    sentiment_negative_pct = Column(Float, nullable=True)
    age_days = Column(Integer, nullable=True)
    
    # Role-based cost tracking
    assignee = Column(String(255), nullable=True)
    assignee_role = Column(String(100), nullable=True)
    total_estimated_cost = Column(Float, nullable=True)
    
    # Full analysis (JSON blob for detailed retrieval)
    analysis_json = Column(JSON, nullable=True)
    
    # Timestamp
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AnalysisHistory {self.issue_key} risk={self.risk_score}>"


class SubscriptionPlan(Base):
    """
    Pricing tier definitions.
    Loaded from config, not user-editable.
    """
    __tablename__ = "subscription_plans"

    id = Column(String(50), primary_key=True)  # starter, growth, enterprise
    name = Column(String(100), nullable=False)
    price_monthly = Column(Float, nullable=False)
    
    # Limits
    issue_analyses_monthly = Column(Integer, nullable=False)
    sprint_analyses_monthly = Column(Integer, nullable=False)
    portfolio_analyses_monthly = Column(Integer, nullable=False)
    
    # Features
    csv_export = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    custom_risk_weights = Column(Boolean, default=False)
    slack_integration = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Plan {self.name} - ${self.price_monthly}/mo>"
