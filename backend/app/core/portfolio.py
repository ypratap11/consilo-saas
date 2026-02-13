
"""
Portfolio analysis module:
- Analyze multiple projects or multiple JQL slices
- Aggregate across issues using the same analysis dict structure
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .consilo_engine import ConsiloEngine


def analyze_portfolio(
    analyzer: ConsiloEngine,
    jql_list: List[str],
    labels: Optional[List[str]] = None,
    max_results_each: int = 50,
) -> Dict[str, Any]:
    """
    Run multiple JQL queries (portfolio slices) and return per-slice + overall rollups.

    Example slices:
      - "project = ENG AND statusCategory != Done"
      - "project = FIN AND statusCategory != Done AND priority in (High, Highest)"
    """
    labels = labels or [f"slice_{i+1}" for i in range(len(jql_list))]
    if len(labels) != len(jql_list):
        raise ValueError("labels length must match jql_list length")

    slices: List[Dict[str, Any]] = []
    overall_analyses: List[Dict[str, Any]] = []
    overall_errors: List[Tuple[str, str]] = []

    for label, jql in zip(labels, jql_list):
        jira_issues = analyzer.jira.search_issues(jql, maxResults=max_results_each)
        keys = [i.key for i in jira_issues]

        errors: List[Tuple[str, str]] = []
        analyses: List[Dict[str, Any]] = []
        for k in keys:
            a = analyzer.build_analysis(k)
            if isinstance(a, dict) and a.get("error"):
                errors.append((k, a["error"]))
                continue
            analyses.append(a)

        rollup = _rollup(analyses)

        slices.append({
            "label": label,
            "jql": jql,
            "issue_keys": keys,
            "issues": analyses,
            "errors": errors,
            "rollup": rollup,
        })

        overall_analyses.extend(analyses)
        overall_errors.extend(errors)

    overall_rollup = _rollup(overall_analyses)

    return {"slices": slices, "overall": {"issues": overall_analyses, "errors": overall_errors, "rollup": overall_rollup}}


def _rollup(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    risks = [a["risk_score"] for a in analyses]
    avg_risk = round(sum(risks) / len(risks), 1) if risks else 0.0
    max_risk = max(risks) if risks else 0

    total_daily_cost = sum(a["capacity"]["daily_cost"] for a in analyses)
    total_person_days_lost_per_day = sum(a["capacity"]["days_lost_per_day_blocked"] for a in analyses)

    blockers_total = sum(len(a["blockers"]) for a in analyses)
    blockers_by_cat = defaultdict(int)
    for a in analyses:
        for b in a["blockers"]:
            for c in b["categories"]:
                blockers_by_cat[c] += 1

    by_project = defaultdict(int)
    for a in analyses:
        by_project[a["project_key"]] += 1

    high_risk = [a for a in analyses if a["risk_score"] >= 70]
    return {
        "counts": {
            "issues": len(analyses),
            "projects": len(by_project),
            "blockers": blockers_total,
            "high_risk": len(high_risk),
        },
        "risk": {"avg": avg_risk, "max": max_risk},
        "capacity": {
            "total_daily_cost": total_daily_cost,
            "total_person_days_lost_per_day": total_person_days_lost_per_day,
        },
        "blockers_by_category": dict(sorted(blockers_by_cat.items(), key=lambda kv: kv[1], reverse=True)),
        "issues_by_project": dict(sorted(by_project.items(), key=lambda kv: kv[1], reverse=True)),
        "top_high_risk": [
            {
                "key": a["issue_key"],
                "risk": a["risk_score"],
                "status": a["timeline"]["current_status"],
                "assignee": (a["issue"].fields.assignee.displayName if a["issue"].fields.assignee else "Unassigned"),
                "summary": a["issue"].fields.summary[:80],
            }
            for a in sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)[:20]
        ],
    }


def format_portfolio_executive(report: Dict[str, Any]) -> str:
    o = report["overall"]["rollup"]
    top_blockers = ", ".join([f"{k}:{v}" for k, v in list(o["blockers_by_category"].items())[:5]]) or "None"
    return f"""
{'='*80}
PORTFOLIO EXECUTIVE SUMMARY
{'='*80}
Projects covered: {o['counts']['projects']}
Issues analyzed: {o['counts']['issues']} (errors: {len(report['overall']['errors'])})

RISK
• Avg risk: {o['risk']['avg']}/100
• Max risk: {o['risk']['max']}/100
• High risk issues: {o['counts']['high_risk']}

BLOCKERS
• Total blockers detected: {o['counts']['blockers']}
• Top categories: {top_blockers}

CAPACITY / COST
• Total daily cost exposure: ${o['capacity']['total_daily_cost']:,.0f}
• Total person-days lost per day (if blocked): {o['capacity']['total_person_days_lost_per_day']:.1f}

TOP HIGH-RISK ISSUES
{chr(10).join([f"• {x['key']} ({x['risk']}/100) - {x['status']} - {x['assignee']}: {x['summary']}" for x in o['top_high_risk'][:10]])}
""".strip()
