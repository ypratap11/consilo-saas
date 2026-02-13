
"""
Sprint analysis module that reuses JiraIQEnhanced.build_analysis().
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .consilo_engine import ConsiloEngine


def analyze_sprint(
    analyzer: ConsiloEngine,
    project_key: str,
    sprint_name: Optional[str] = None,
    max_results: int = 50,
) -> Dict[str, Any]:
    """
    Analyze all non-Done issues in a sprint and return aggregated metrics + per-issue analyses.

    Returns:
      {
        "project_key": ...,
        "sprint_name": ...,
        "issue_keys": [...],
        "issues": [analysis_dict, ...],
        "errors": [(issue_key, error_str), ...],
        "rollup": {...},
      }
    """
    if sprint_name:
        jql = f'project = {project_key} AND sprint = "{sprint_name}" AND status != Done'
    else:
        jql = f"project = {project_key} AND sprint in openSprints() AND status != Done"

    jira_issues = analyzer.jira.search_issues(jql, maxResults=max_results)
    issue_keys = [i.key for i in jira_issues]

    errors: List[Tuple[str, str]] = []
    analyses: List[Dict[str, Any]] = []
    for key in issue_keys:
        a = analyzer.build_analysis(key)
        if isinstance(a, dict) and a.get("error"):
            errors.append((key, a["error"]))
            continue
        analyses.append(a)

    rollup = _rollup_sprint(analyses)

    return {
        "project_key": project_key,
        "sprint_name": sprint_name or "ACTIVE",
        "issue_keys": issue_keys,
        "issues": analyses,
        "errors": errors,
        "rollup": rollup,
    }


def _rollup_sprint(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Risk
    risks = [a["risk_score"] for a in analyses]
    avg_risk = round(sum(risks) / len(risks), 1) if risks else 0.0
    max_risk = max(risks) if risks else 0

    # Cost / capacity
    total_daily_cost = sum(a["capacity"]["daily_cost"] for a in analyses)
    total_person_days_lost_per_day = sum(a["capacity"]["days_lost_per_day_blocked"] for a in analyses)

    # Blockers
    blocker_count = sum(len(a["blockers"]) for a in analyses)
    blocker_by_cat = defaultdict(int)
    for a in analyses:
        for b in a["blockers"]:
            for c in b["categories"]:
                blocker_by_cat[c] += 1

    # Staleness
    stale = [a for a in analyses if a["timeline"]["last_update_days"] > 5]
    very_stale = [a for a in analyses if a["timeline"]["last_update_days"] > 10]

    # Health bands
    high_risk = [a["issue_key"] for a in analyses if a["risk_score"] >= 70]
    med_risk = [a["issue_key"] for a in analyses if 40 <= a["risk_score"] < 70]
    low_risk = [a["issue_key"] for a in analyses if a["risk_score"] < 40]

    return {
        "counts": {
            "issues": len(analyses),
            "blockers": blocker_count,
            "high_risk": len(high_risk),
            "medium_risk": len(med_risk),
            "low_risk": len(low_risk),
            "stale_updates_gt_5d": len(stale),
            "stale_updates_gt_10d": len(very_stale),
        },
        "risk": {"avg": avg_risk, "max": max_risk, "high_risk_keys": high_risk},
        "capacity": {
            "total_daily_cost": total_daily_cost,
            "total_person_days_lost_per_day": total_person_days_lost_per_day,
        },
        "blockers_by_category": dict(sorted(blocker_by_cat.items(), key=lambda kv: kv[1], reverse=True)),
    }


def format_sprint_executive(sprint_report: Dict[str, Any]) -> str:
    r = sprint_report["rollup"]
    counts = r["counts"]
    risk = r["risk"]
    cap = r["capacity"]
    blocker_by_cat = r["blockers_by_category"]

    top_blockers = ", ".join([f"{k}:{v}" for k, v in list(blocker_by_cat.items())[:5]]) or "None"

    return f"""
{'='*80}
SPRINT EXECUTIVE SUMMARY
{'='*80}
Project: {sprint_report['project_key']}
Sprint: {sprint_report['sprint_name']}
Issues analyzed: {counts['issues']} (errors: {len(sprint_report['errors'])})

RISK
• Avg risk: {risk['avg']}/100
• Max risk: {risk['max']}/100
• High risk issues: {counts['high_risk']} ({', '.join(risk['high_risk_keys'][:10])}{'...' if len(risk['high_risk_keys'])>10 else ''})

BLOCKERS
• Total blockers detected: {counts['blockers']}
• Top categories: {top_blockers}

CAPACITY / COST
• Total daily cost exposure: ${cap['total_daily_cost']:,.0f}
• Total person-days lost per day (if blocked): {cap['total_person_days_lost_per_day']:.1f}

STALE ISSUES
• Last update > 5d: {counts['stale_updates_gt_5d']}
• Last update > 10d: {counts['stale_updates_gt_10d']}
""".strip()
