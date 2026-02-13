"""
Pydantic schemas for Consilo API
Used for request validation and response serialization
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# ============================================================================
# TENANT SCHEMAS
# ============================================================================

class TenantCreate(BaseModel):
    """Request to create a new tenant account"""
    company_name: str = Field(..., min_length=1, max_length=255)
    jira_url: str = Field(..., description="Jira instance URL (e.g., https://company.atlassian.net)")
    jira_email: EmailStr
    jira_token: str = Field(..., min_length=10, description="Jira API token")
    daily_rate_per_person: Optional[float] = 2500.0
    
    @validator('jira_url')
    def validate_jira_url(cls, v):
        if not v.startswith('http'):
            raise ValueError('jira_url must start with http:// or https://')
        return v.rstrip('/')


class TenantUpdate(BaseModel):
    """Update tenant settings"""
    company_name: Optional[str] = None
    jira_url: Optional[str] = None
    jira_email: Optional[EmailStr] = None
    jira_token: Optional[str] = None
    daily_rate_per_person: Optional[float] = None


class TenantResponse(BaseModel):
    """Public tenant information (no sensitive data)"""
    id: UUID
    company_name: str
    jira_url: str
    jira_email: str
    plan: str
    status: str
    created_at: datetime
    
    # Usage stats
    monthly_issue_limit: int
    monthly_sprint_limit: int
    monthly_portfolio_limit: int
    
    class Config:
        from_attributes = True


# ============================================================================
# ANALYSIS SCHEMAS
# ============================================================================

class IssueAnalysisRequest(BaseModel):
    """Request to analyze a single issue"""
    issue_key: str = Field(..., description="Jira issue key (e.g., ENG-123)")
    template: Optional[str] = Field("executive", description="Report template: executive, technical, pm, all")
    store_history: Optional[bool] = Field(True, description="Store analysis in history for trending")


class IssueAnalysisResponse(BaseModel):
    """Response from issue analysis"""
    issue_key: str
    template: str
    report: str  # Formatted text report
    risk_score: int
    daily_cost: float
    blocker_count: int
    timestamp: datetime


class IssueAnalysisRawResponse(BaseModel):
    """Raw analysis data (JSON)"""
    issue_key: str
    project_key: str
    risk_score: int
    sentiment: Dict[str, Any]
    blockers: List[Dict[str, Any]]
    timeline: Dict[str, Any]
    capacity: Dict[str, Any]
    predictions: Dict[str, Any]
    trends: Dict[str, Any]
    dependencies: Dict[str, Any]
    similar_issues: List[str]
    team_baseline: Dict[str, Any]


class SprintAnalysisRequest(BaseModel):
    """Request to analyze a sprint"""
    project_key: str = Field(..., description="Jira project key (e.g., ENG)")
    sprint_name: Optional[str] = Field(None, description="Sprint name (leave empty for active sprint)")
    max_issues: Optional[int] = Field(50, ge=1, le=200)


class SprintAnalysisResponse(BaseModel):
    """Sprint analysis results"""
    project_key: str
    sprint_name: str
    issue_count: int
    executive_summary: str
    rollup: Dict[str, Any]
    timestamp: datetime


class PortfolioAnalysisRequest(BaseModel):
    """Request to analyze portfolio across multiple JQL slices"""
    project_keys: List[str] = Field(..., description="List of project keys")
    slices: List[Dict[str, str]] = Field(
        ...,
        description="JQL slices with 'name' and 'jql' keys"
    )
    max_issues_per_slice: Optional[int] = Field(50, ge=1, le=200)


class PortfolioAnalysisResponse(BaseModel):
    """Portfolio analysis results"""
    slices: List[Dict[str, Any]]
    overall: Dict[str, Any]
    executive_summary: str
    timestamp: datetime


# ============================================================================
# USAGE & HISTORY SCHEMAS
# ============================================================================

class UsageStats(BaseModel):
    """Current month usage for a tenant"""
    tenant_id: UUID
    period: str  # e.g., "2025-02"
    issue_analyses: int
    sprint_analyses: int
    portfolio_analyses: int
    total_calls: int
    
    # Limits
    issue_limit: int
    sprint_limit: int
    portfolio_limit: int
    
    # Remaining
    issue_remaining: int
    sprint_remaining: int
    portfolio_remaining: int


class AnalysisHistoryItem(BaseModel):
    """Single historical analysis record"""
    id: UUID
    issue_key: str
    project_key: str
    risk_score: int
    daily_cost: float
    blocker_count: int
    analyzed_at: datetime
    
    class Config:
        from_attributes = True


class TrendData(BaseModel):
    """Trend data for an issue over time"""
    issue_key: str
    project_key: str
    data_points: List[Dict[str, Any]]  # [{timestamp, risk_score, daily_cost, ...}, ...]
    trend_direction: str  # improving, stable, degrading


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
