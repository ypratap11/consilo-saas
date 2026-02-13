"""
Consilo Engine - Core Analysis Logic
Adapted from original JiraIQ Enhanced for multi-tenant SaaS

Changes from original:
- Accepts Jira credentials as parameters (not from environment)
- Works with Tenant model for multi-tenancy
- Designed for API use (not CLI)
"""

from jira import JIRA
from transformers import pipeline
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
import re

class ConsiloEngine:
    """
    Core analysis engine for Consilo.
    
    Usage:
        engine = ConsiloEngine(jira_url, jira_email, jira_token, daily_rate)
        analysis = engine.build_analysis(issue_key)
        report = engine.analyze_issue(issue_key, template="executive")
    """
    
    def __init__(
        self,
        jira_url: str,
        jira_email: str,
        jira_token: str,
        daily_rate: float = 2500.0
    ):
        """Initialize engine with Jira credentials"""
        self.jira = JIRA(server=jira_url, basic_auth=(jira_email, jira_token))
        self.daily_rate = daily_rate
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=-1
        )
        self.team_baseline = {}
    
    def build_analysis(self, issue_key: str) -> Dict[str, Any]:
        """
        Build complete analysis dict for an issue.
        This is the core pipeline - no formatting.
        
        Returns dict with all analysis data, or dict with 'error' key if failed.
        """
        try:
            issue = self.jira.issue(issue_key, expand='changelog')
        except Exception as e:
            return {"error": f"Failed to fetch issue: {str(e)}", "issue_key": issue_key}
        
        try:
            comments = self.jira.comments(issue.key)
            project_key = issue.key.split('-')[0]
            
            # Calculate team baseline if not cached
            if project_key not in self.team_baseline:
                self.team_baseline[project_key] = self._calculate_team_baseline(project_key)
            
            # Core analysis
            sentiment_data = self._analyze_sentiment(comments)
            blockers = self._categorize_blockers(comments)
            timeline_data = self._analyze_timeline(issue)
            capacity_data = self._calculate_capacity_impact(issue, comments)
            risk_score = self._calculate_risk_score(
                sentiment_data, blockers, timeline_data, capacity_data
            )
            trends = self._analyze_trends(issue, comments, sentiment_data)
            similar_issues = self._find_similar_issues(issue, project_key)
            dependencies = self._map_dependencies(issue, comments)
            predictions = self._generate_predictions(
                issue, blockers, sentiment_data, similar_issues
            )
            
            analysis = {
                'issue': issue,
                'issue_key': issue.key,
                'project_key': project_key,
                'comments': comments,
                'sentiment': sentiment_data,
                'blockers': blockers,
                'timeline': timeline_data,
                'capacity': capacity_data,
                'risk_score': risk_score,
                'trends': trends,
                'similar_issues': similar_issues,
                'dependencies': dependencies,
                'predictions': predictions,
                'team_baseline': self.team_baseline[project_key]
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}", "issue_key": issue_key}
    
    def analyze_issue(self, issue_key: str, template: str = "executive") -> str:
        """
        Public API: build analysis dict, then format based on template.
        Returns formatted string report.
        """
        analysis = self.build_analysis(issue_key)
        
        if isinstance(analysis, dict) and analysis.get("error"):
            return analysis["error"]
        
        if template == "executive":
            return self._format_executive(analysis)
        elif template == "technical":
            return self._format_technical(analysis)
        elif template == "pm":
            return self._format_pm(analysis)
        elif template == "all":
            return f"""{'='*80}
EXECUTIVE SUMMARY
{'='*80}
{self._format_executive(analysis)}

{'='*80}
TECHNICAL ANALYSIS
{'='*80}
{self._format_technical(analysis)}

{'='*80}
PM REPORT
{'='*80}
{self._format_pm(analysis)}"""
        
        return "Invalid template"
    
    # ========================================================================
    # ANALYSIS METHODS (from original core.py)
    # ========================================================================
    
    def _analyze_sentiment(self, comments) -> Dict[str, Any]:
        """Analyze sentiment of all comments using FinBERT"""
        if not comments:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_pct': 0.0,
                'negative_pct': 0.0,
                'trend': []
            }
        
        sentiments = []
        trend = []
        
        for comment in comments:
            text = comment.body[:512]  # FinBERT max length
            try:
                result = self.sentiment_analyzer(text)[0]
                label = result['label'].lower()
                score = result['score']
                
                sentiments.append(label)
                trend.append({
                    'date': str(comment.created),
                    'sentiment': label,
                    'score': score
                })
            except:
                sentiments.append('neutral')
        
        total = len(sentiments)
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        neutral = sentiments.count('neutral')
        
        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_pct': (positive / total * 100) if total > 0 else 0.0,
            'negative_pct': (negative / total * 100) if total > 0 else 0.0,
            'trend': trend
        }
    
    def _categorize_blockers(self, comments) -> List[Dict[str, Any]]:
        """Categorize blockers from comments"""
        blocker_keywords = {
            'technical_debt': ['refactor', 'technical debt', 'legacy code', 'deprecated'],
            'dependency': ['waiting on', 'blocked by', 'depends on', 'dependency'],
            'resource': ['need help', 'need resource', 'understaffed', 'capacity'],
            'external': ['vendor', 'third party', 'external team', 'partner'],
            'requirements': ['unclear requirements', 'missing spec', 'need clarification'],
            'testing': ['test failure', 'qa blocker', 'test environment'],
            'deployment': ['deploy', 'release', 'environment issue', 'infrastructure']
        }
        
        blockers = []
        
        for comment in comments:
            text = comment.body.lower()
            categories = []
            
            for category, keywords in blocker_keywords.items():
                if any(kw in text for kw in keywords):
                    categories.append(category)
            
            if categories or 'blocked' in text or 'blocker' in text:
                blockers.append({
                    'author': comment.author.displayName if hasattr(comment, 'author') else 'Unknown',
                    'date': str(comment.created),
                    'snippet': comment.body[:200],
                    'categories': categories if categories else ['uncategorized']
                })
        
        return blockers
    
    def _analyze_timeline(self, issue) -> Dict[str, Any]:
        """Analyze issue timeline and status changes"""
        created = datetime.strptime(str(issue.fields.created)[:19], '%Y-%m-%dT%H:%M:%S')
        updated = datetime.strptime(str(issue.fields.updated)[:19], '%Y-%m-%dT%H:%M:%S')
        now = datetime.utcnow()
        
        age_days = (now - created).days
        last_update_days = (now - updated).days
        
        # Analyze changelog for status changes
        status_changes = []
        if hasattr(issue, 'changelog'):
            for history in issue.changelog.histories:
                for item in history.items:
                    if item.field == 'status':
                        status_changes.append({
                            'from': item.fromString,
                            'to': item.toString,
                            'date': str(history.created),
                            'author': history.author.displayName if hasattr(history, 'author') else 'Unknown'
                        })
        
        return {
            'created': str(created),
            'updated': str(updated),
            'age_days': age_days,
            'last_update_days': last_update_days,
            'current_status': issue.fields.status.name,
            'status_changes': status_changes,
            'time_in_current_status': last_update_days
        }
    
    def _calculate_capacity_impact(self, issue, comments) -> Dict[str, Any]:
        """Calculate capacity and cost impact with role-based costs, geographic multipliers, and auto-detection"""
        # Estimate person-days based on story points or default
        story_points = getattr(issue.fields, 'customfield_10016', None)  # Common story points field
        if story_points and isinstance(story_points, (int, float)):
            estimated_days = float(story_points)
        else:
            # Default estimate based on priority
            priority = issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else 'Medium'
            estimate_map = {'Highest': 5, 'High': 3, 'Medium': 2, 'Low': 1, 'Lowest': 0.5}
            estimated_days = estimate_map.get(priority, 2)
        
        # Role-based cost calculation with geographic multipliers
        assignee_name = None
        assignee_role = None
        assignee_location = None
        base_daily_cost = self.daily_rate  # Fallback to default
        daily_cost = self.daily_rate
        cost_multipliers = []
        
        if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
            assignee_name = issue.fields.assignee.displayName
            
            # Try to get role-based cost with geographic adjustment
            try:
                from .role_costs import (
                    get_user_rate, 
                    get_user_location,
                    apply_geographic_multiplier,
                    LOCATION_MULTIPLIERS
                )
                
                # Get base role and rate
                base_daily_cost, assignee_role = get_user_rate(assignee_name, issue.fields.assignee)
                daily_cost = base_daily_cost
                
                # Apply geographic multiplier if available
                assignee_location = get_user_location(assignee_name, issue.fields.assignee)
                if assignee_location and assignee_location in LOCATION_MULTIPLIERS:
                    multiplier = LOCATION_MULTIPLIERS[assignee_location]
                    daily_cost = apply_geographic_multiplier(daily_cost, assignee_location)
                    cost_multipliers.append(f"{assignee_location}: {multiplier}x")
                    
            except ImportError:
                # role_costs.py not available, use default
                pass
            except Exception as e:
                # Gracefully handle any errors in role detection
                pass
        
        # Detect overtime/weekend work from comment timestamps
        overtime_detected = False
        weekend_detected = False
        
        try:
            from .role_costs import is_overtime, is_weekend, OVERTIME_MULTIPLIER, WEEKEND_MULTIPLIER
            
            for comment in comments:
                comment_time = comment.created
                if is_overtime(comment_time):
                    overtime_detected = True
                if is_weekend(comment_time):
                    weekend_detected = True
            
            if overtime_detected:
                daily_cost *= OVERTIME_MULTIPLIER
                cost_multipliers.append(f"Overtime: {OVERTIME_MULTIPLIER}x")
            if weekend_detected:
                daily_cost *= WEEKEND_MULTIPLIER
                cost_multipliers.append(f"Weekend: {WEEKEND_MULTIPLIER}x")
        except:
            pass
        
        # If blocked, calculate days lost
        blockers_count = len(self._categorize_blockers(comments))
        days_lost_per_day = 1.0 if blockers_count > 0 else 0.0
        
        return {
            'estimated_days': estimated_days,
            'daily_cost': daily_cost,
            'base_daily_cost': base_daily_cost,
            'cost_multipliers': cost_multipliers,
            'assignee': assignee_name or 'Unassigned',
            'assignee_role': assignee_role or 'Unknown',
            'assignee_location': assignee_location,
            'days_lost_per_day_blocked': days_lost_per_day,
            'total_cost_if_blocked': daily_cost * estimated_days if blockers_count > 0 else 0,
            'total_estimated_cost': daily_cost * estimated_days,
            'overtime_detected': overtime_detected,
            'weekend_detected': weekend_detected
        }
    
    def _calculate_risk_score(
        self,
        sentiment_data: Dict,
        blockers: List,
        timeline_data: Dict,
        capacity_data: Dict
    ) -> int:
        """Calculate risk score 0-100"""
        risk = 0
        
        # Sentiment risk (0-30)
        if sentiment_data['total'] > 0:
            risk += int(sentiment_data['negative_pct'] * 0.3)
        
        # Blocker risk (0-30)
        blocker_count = len(blockers)
        if blocker_count > 0:
            risk += min(10 * blocker_count, 30)
        
        # Age risk (0-20)
        age_days = timeline_data['age_days']
        if age_days > 30:
            risk += 20
        elif age_days > 14:
            risk += 10
        elif age_days > 7:
            risk += 5
        
        # Staleness risk (0-20)
        last_update = timeline_data['last_update_days']
        if last_update > 10:
            risk += 20
        elif last_update > 5:
            risk += 10
        elif last_update > 3:
            risk += 5
        
        return min(risk, 100)
    
    def _analyze_trends(self, issue, comments, sentiment_data) -> Dict[str, Any]:
        """Analyze trends over time"""
        return {
            'sentiment_trend': 'degrading' if sentiment_data.get('negative_pct', 0) > 40 else 'stable',
            'activity_trend': 'decreasing' if len(comments) < 2 else 'active',
            'risk_trend': 'increasing'  # Simplified for now
        }
    
    def _calculate_team_baseline(self, project_key: str) -> Dict[str, Any]:
        """Calculate team baseline metrics"""
        try:
            jql = f"project = {project_key} AND statusCategory != Done ORDER BY created DESC"
            issues = self.jira.search_issues(jql, maxResults=50)
            
            if not issues:
                return {'avg_age_days': 0, 'avg_comments': 0}
            
            total_age = 0
            total_comments = 0
            
            for iss in issues:
                created = datetime.strptime(str(iss.fields.created)[:19], '%Y-%m-%dT%H:%M:%S')
                age = (datetime.utcnow() - created).days
                total_age += age
                total_comments += len(self.jira.comments(iss.key))
            
            return {
                'avg_age_days': total_age / len(issues),
                'avg_comments': total_comments / len(issues)
            }
        except:
            return {'avg_age_days': 0, 'avg_comments': 0}
    
    def _find_similar_issues(self, issue, project_key: str) -> List[str]:
        """Find similar issues in the project"""
        try:
            summary = issue.fields.summary
            # Simple keyword search (can be enhanced with embedding similarity)
            keywords = ' '.join([w for w in summary.split() if len(w) > 3])[:100]
            jql = f'project = {project_key} AND text ~ "{keywords}" AND key != {issue.key}'
            similar = self.jira.search_issues(jql, maxResults=5)
            return [s.key for s in similar]
        except:
            return []
    
    def _map_dependencies(self, issue, comments) -> Dict[str, Any]:
        """Map issue dependencies"""
        dependencies = {
            'blocks': [],
            'blocked_by': [],
            'relates_to': []
        }
        
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                if hasattr(link, 'outwardIssue'):
                    dependencies['blocks'].append(link.outwardIssue.key)
                if hasattr(link, 'inwardIssue'):
                    dependencies['blocked_by'].append(link.inwardIssue.key)
        
        return dependencies
    
    def _generate_predictions(
        self,
        issue,
        blockers: List,
        sentiment_data: Dict,
        similar_issues: List
    ) -> Dict[str, Any]:
        """Generate predictions about issue resolution"""
        # Simplified prediction logic
        has_blockers = len(blockers) > 0
        negative_sentiment = sentiment_data.get('negative_pct', 0) > 30
        
        if has_blockers and negative_sentiment:
            completion_likelihood = 'low'
            recommended_action = 'Escalate to leadership'
        elif has_blockers or negative_sentiment:
            completion_likelihood = 'medium'
            recommended_action = 'Monitor closely'
        else:
            completion_likelihood = 'high'
            recommended_action = 'Continue as planned'
        
        return {
            'completion_likelihood': completion_likelihood,
            'recommended_action': recommended_action,
            'escalation_needed': has_blockers and negative_sentiment
        }
    
    # ========================================================================
    # FORMATTERS (from original core.py)
    # ========================================================================
    
    def _format_executive(self, analysis: Dict) -> str:
        """Executive summary format"""
        issue = analysis['issue']
        risk = analysis['risk_score']
        capacity = analysis['capacity']
        blockers = analysis['blockers']
        predictions = analysis['predictions']
        
        status_emoji = '🔴' if risk >= 70 else '🟡' if risk >= 40 else '🟢'
        
        # Role-based cost information with location
        assignee_info = f"{capacity.get('assignee', 'Unassigned')}"
        role_info = capacity.get('assignee_role')
        location_info = capacity.get('assignee_location')
        
        if role_info and role_info != 'Unknown':
            assignee_info += f" ({role_info}"
            if location_info:
                assignee_info += f", {location_info}"
            assignee_info += ")"
        elif location_info:
            assignee_info += f" ({location_info})"
        
        # Cost breakdown
        cost_details = f"• Daily cost: ${capacity['daily_cost']:,.0f}"
        
        # Show base cost if multipliers applied
        if capacity.get('cost_multipliers'):
            base_cost = capacity.get('base_daily_cost', capacity['daily_cost'])
            if base_cost != capacity['daily_cost']:
                cost_details += f" (base: ${base_cost:,.0f})"
                cost_details += f"\n  Multipliers: {', '.join(capacity['cost_multipliers'])}"
        
        # Overtime/weekend detection
        work_pattern = []
        if capacity.get('overtime_detected'):
            work_pattern.append('⚠️ After-hours work detected')
        if capacity.get('weekend_detected'):
            work_pattern.append('⚠️ Weekend work detected')
        
        work_pattern_str = '\n'.join([f"• {p}" for p in work_pattern])
        if work_pattern_str:
            work_pattern_str = '\n' + work_pattern_str
        
        return f"""
{status_emoji} RISK SCORE: {risk}/100

ISSUE: {issue.key} - {issue.fields.summary}
Status: {issue.fields.status.name}
Priority: {issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else 'N/A'}
Assignee: {assignee_info}

CAPACITY IMPACT:
{cost_details}
• Estimated effort: {capacity['estimated_days']} days
• Total estimated cost: ${capacity.get('total_estimated_cost', 0):,.0f}
• Days lost per day if blocked: {capacity['days_lost_per_day_blocked']}{work_pattern_str}

BLOCKERS: {len(blockers)}
{chr(10).join([f"• {b['categories'][0].upper()}: {b['snippet'][:80]}" for b in blockers[:3]])}

RECOMMENDATION: {predictions['recommended_action']}
Escalation needed: {'Yes' if predictions['escalation_needed'] else 'No'}
""".strip()
    
    def _format_technical(self, analysis: Dict) -> str:
        """Technical analysis format"""
        sentiment = analysis['sentiment']
        timeline = analysis['timeline']
        dependencies = analysis['dependencies']
        
        return f"""
SENTIMENT ANALYSIS:
• Total comments: {sentiment['total']}
• Positive: {sentiment['positive']} ({sentiment['positive_pct']:.1f}%)
• Negative: {sentiment['negative']} ({sentiment['negative_pct']:.1f}%)
• Neutral: {sentiment['neutral']}

TIMELINE:
• Age: {timeline['age_days']} days
• Last updated: {timeline['last_update_days']} days ago
• Status changes: {len(timeline['status_changes'])}

DEPENDENCIES:
• Blocks: {len(dependencies['blocks'])} issues
• Blocked by: {len(dependencies['blocked_by'])} issues
""".strip()
    
    def _format_pm(self, analysis: Dict) -> str:
        """PM report format"""
        return self._format_executive(analysis) + "\n\n" + self._format_technical(analysis)
