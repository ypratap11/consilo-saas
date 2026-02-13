"""
Analysis endpoints - core Consilo business logic
- Analyze single issue
- Analyze sprint
- Analyze portfolio
- Get analysis history / trends
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import time

from ..database import get_db
from ..models import Tenant, AnalysisHistory
from ..schemas import (
    IssueAnalysisRequest,
    IssueAnalysisResponse,
    IssueAnalysisRawResponse,
    SprintAnalysisRequest,
    SprintAnalysisResponse,
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    TrendData,
    AnalysisHistoryItem
)
from ..middleware import get_current_tenant, check_usage_limit, log_usage, decrypt_token
from ..core.consilo_engine import ConsiloEngine
from ..core.sprint import analyze_sprint, format_sprint_executive
from ..core.portfolio import analyze_portfolio, format_portfolio_executive

router = APIRouter()


def _get_engine(tenant: Tenant) -> ConsiloEngine:
    """
    Helper to instantiate ConsiloEngine with tenant's Jira credentials.
    """
    jira_token = decrypt_token(tenant.jira_token_encrypted)
    
    engine = ConsiloEngine(
        jira_url=tenant.jira_url,
        jira_email=tenant.jira_email,
        jira_token=jira_token,
        daily_rate=tenant.daily_rate_per_person
    )
    
    return engine


@router.post("/issue", response_model=IssueAnalysisResponse)
async def analyze_issue(
    request: IssueAnalysisRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Analyze a single Jira issue.
    
    Returns formatted report based on template (executive, technical, pm, all).
    """
    # Check usage limits
    await check_usage_limit(tenant, "issue", db)
    
    # Initialize engine
    engine = _get_engine(tenant)
    
    # Run analysis
    start_time = time.time()
    
    try:
        # Get raw analysis
        analysis = engine.build_analysis(request.issue_key)
        
        if analysis.get("error"):
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        # Get formatted report
        report = engine.analyze_issue(request.issue_key, template=request.template)
        
        # Store in history if requested
        if request.store_history:
            history_record = AnalysisHistory(
                tenant_id=tenant.id,
                issue_key=analysis['issue_key'],
                project_key=analysis['project_key'],
                risk_score=analysis['risk_score'],
                daily_cost=analysis['capacity']['daily_cost'],
                blocker_count=len(analysis['blockers']),
                sentiment_negative_pct=analysis['sentiment'].get('negative_pct'),
                age_days=analysis['timeline'].get('age_days'),
                assignee=analysis['capacity'].get('assignee'),
                assignee_role=analysis['capacity'].get('assignee_role'),
                total_estimated_cost=analysis['capacity'].get('total_estimated_cost'),
                # Store full analysis as JSON (excluding non-serializable Jira objects)
                analysis_json={
                    'risk_score': analysis['risk_score'],
                    'sentiment': analysis['sentiment'],
                    'capacity': analysis['capacity'],
                    'timeline': analysis['timeline'],
                    'blocker_count': len(analysis['blockers']),
                    'predictions': analysis['predictions']
                }
            )
            db.add(history_record)
            db.commit()
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Log usage
        await log_usage(
            tenant_id=str(tenant.id),
            action_type="issue",
            resource_key=request.issue_key,
            processing_time_ms=processing_time,
            db=db
        )
        
        return IssueAnalysisResponse(
            issue_key=analysis['issue_key'],
            template=request.template,
            report=report,
            risk_score=analysis['risk_score'],
            daily_cost=analysis['capacity']['daily_cost'],
            blocker_count=len(analysis['blockers']),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/issue/{issue_key}/raw", response_model=IssueAnalysisRawResponse)
async def get_issue_raw(
    issue_key: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get raw analysis data for an issue (JSON format).
    
    This endpoint is useful for:
    - Programmatic access
    - Dashboard widgets
    - Custom integrations
    """
    # Check usage limits
    await check_usage_limit(tenant, "issue", db)
    
    engine = _get_engine(tenant)
    
    analysis = engine.build_analysis(issue_key)
    
    if analysis.get("error"):
        raise HTTPException(status_code=400, detail=analysis["error"])
    
    # Log usage
    await log_usage(
        tenant_id=str(tenant.id),
        action_type="issue",
        resource_key=issue_key,
        db=db
    )
    
    # Return JSON-safe projection
    return IssueAnalysisRawResponse(
        issue_key=analysis['issue_key'],
        project_key=analysis['project_key'],
        risk_score=analysis['risk_score'],
        sentiment=analysis['sentiment'],
        blockers=[
            {
                'author': b['author'],
                'date': b['date'],
                'snippet': b['snippet'],
                'categories': b['categories']
            }
            for b in analysis['blockers']
        ],
        timeline=analysis['timeline'],
        capacity=analysis['capacity'],
        predictions=analysis['predictions'],
        trends=analysis['trends'],
        dependencies=analysis['dependencies'],
        similar_issues=analysis['similar_issues'],
        team_baseline=analysis['team_baseline']
    )


@router.post("/sprint", response_model=SprintAnalysisResponse)
async def analyze_sprint_endpoint(
    request: SprintAnalysisRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Analyze all issues in a sprint.
    
    Returns rollup metrics and executive summary.
    """
    # Check usage limits
    await check_usage_limit(tenant, "sprint", db)
    
    engine = _get_engine(tenant)
    
    try:
        # Run sprint analysis
        sprint_data = analyze_sprint(
            analyzer=engine,
            project_key=request.project_key,
            sprint_name=request.sprint_name,
            max_results=request.max_issues
        )
        
        # Format executive summary
        executive_summary = format_sprint_executive(sprint_data)
        
        # Log usage
        await log_usage(
            tenant_id=str(tenant.id),
            action_type="sprint",
            resource_key=f"{request.project_key}/{request.sprint_name or 'active'}",
            db=db
        )
        
        return SprintAnalysisResponse(
            project_key=sprint_data['project_key'],
            sprint_name=sprint_data['sprint_name'],
            issue_count=len(sprint_data['issues']),
            executive_summary=executive_summary,
            rollup=sprint_data['rollup'],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sprint analysis failed: {str(e)}")


@router.post("/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio_endpoint(
    request: PortfolioAnalysisRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Analyze portfolio across multiple projects/JQL slices.
    
    Returns aggregated metrics across all slices.
    """
    # Check usage limits
    await check_usage_limit(tenant, "portfolio", db)
    
    engine = _get_engine(tenant)
    
    try:
        # Convert slices to JQL list
        jql_list = [s['jql'] for s in request.slices]
        labels = [s['name'] for s in request.slices]
        
        # Run portfolio analysis
        portfolio_data = analyze_portfolio(
            analyzer=engine,
            jql_list=jql_list,
            labels=labels,
            max_results_each=request.max_issues_per_slice
        )
        
        # Format executive summary
        executive_summary = format_portfolio_executive(portfolio_data)
        
        # Log usage
        await log_usage(
            tenant_id=str(tenant.id),
            action_type="portfolio",
            resource_key=','.join(request.project_keys),
            db=db
        )
        
        return PortfolioAnalysisResponse(
            slices=portfolio_data['slices'],
            overall=portfolio_data['overall'],
            executive_summary=executive_summary,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio analysis failed: {str(e)}")


@router.get("/history/{issue_key}", response_model=list[AnalysisHistoryItem])
async def get_issue_history(
    issue_key: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get historical analysis data for an issue.
    
    This enables "risk over time" charts and trend analysis.
    """
    history = db.query(AnalysisHistory).filter(
        AnalysisHistory.tenant_id == tenant.id,
        AnalysisHistory.issue_key == issue_key
    ).order_by(AnalysisHistory.analyzed_at.desc()).limit(30).all()
    
    return history


@router.get("/trends/{issue_key}", response_model=TrendData)
async def get_issue_trends(
    issue_key: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get trend analysis for an issue based on historical data.
    
    Returns:
    - Historical data points
    - Trend direction (improving, stable, degrading)
    """
    history = db.query(AnalysisHistory).filter(
        AnalysisHistory.tenant_id == tenant.id,
        AnalysisHistory.issue_key == issue_key
    ).order_by(AnalysisHistory.analyzed_at).all()
    
    if not history:
        raise HTTPException(status_code=404, detail="No historical data found for this issue")
    
    # Convert to data points
    data_points = [
        {
            'timestamp': str(h.analyzed_at),
            'risk_score': h.risk_score,
            'daily_cost': h.daily_cost,
            'blocker_count': h.blocker_count,
            'sentiment_negative_pct': h.sentiment_negative_pct
        }
        for h in history
    ]
    
    # Determine trend direction
    if len(history) >= 2:
        recent_risk = history[-1].risk_score
        older_risk = history[0].risk_score
        
        if recent_risk < older_risk - 10:
            trend_direction = "improving"
        elif recent_risk > older_risk + 10:
            trend_direction = "degrading"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "insufficient_data"
    
    return TrendData(
        issue_key=issue_key,
        project_key=history[0].project_key,
        data_points=data_points,
        trend_direction=trend_direction
    )
