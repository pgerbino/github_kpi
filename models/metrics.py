"""
Productivity metrics data models for GitHub Productivity Dashboard.

This module contains data structures for representing calculated
productivity metrics and analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class MetricPeriod(Enum):
    """Enumeration for metric calculation periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass
class VelocityPoint:
    """Represents a single velocity measurement point."""
    timestamp: datetime
    commits: int
    additions: int
    deletions: int
    pull_requests: int
    issues_closed: int
    
    def __post_init__(self):
        """Validate velocity point data."""
        if any(val < 0 for val in [self.commits, self.additions, self.deletions, 
                                   self.pull_requests, self.issues_closed]):
            raise ValueError("All velocity metrics must be non-negative")
    
    @property
    def total_changes(self) -> int:
        """Calculate total code changes."""
        return self.additions + self.deletions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert velocity point to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'commits': self.commits,
            'additions': self.additions,
            'deletions': self.deletions,
            'pull_requests': self.pull_requests,
            'issues_closed': self.issues_closed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VelocityPoint':
        """Create velocity point from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            commits=data['commits'],
            additions=data['additions'],
            deletions=data['deletions'],
            pull_requests=data['pull_requests'],
            issues_closed=data['issues_closed']
        )


@dataclass
class CommitMetrics:
    """Metrics related to commit activity."""
    total_commits: int
    commit_frequency: Dict[str, int]  # period -> count
    average_additions: float
    average_deletions: float
    average_files_changed: float
    most_active_hours: List[int]  # hours of day with most commits
    commit_message_length_avg: float
    
    def __post_init__(self):
        """Validate commit metrics."""
        if self.total_commits < 0:
            raise ValueError("Total commits must be non-negative")
        if any(val < 0 for val in [self.average_additions, self.average_deletions, 
                                   self.average_files_changed, self.commit_message_length_avg]):
            raise ValueError("Average metrics must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert commit metrics to dictionary."""
        return {
            'total_commits': self.total_commits,
            'commit_frequency': self.commit_frequency,
            'average_additions': self.average_additions,
            'average_deletions': self.average_deletions,
            'average_files_changed': self.average_files_changed,
            'most_active_hours': self.most_active_hours,
            'commit_message_length_avg': self.commit_message_length_avg
        }


@dataclass
class PRMetrics:
    """Metrics related to pull request activity."""
    total_prs: int
    merged_prs: int
    closed_prs: int
    open_prs: int
    average_time_to_merge: Optional[float]  # hours
    average_additions: float
    average_deletions: float
    average_commits_per_pr: float
    merge_rate: float  # percentage
    
    def __post_init__(self):
        """Validate PR metrics."""
        if any(val < 0 for val in [self.total_prs, self.merged_prs, self.closed_prs, self.open_prs]):
            raise ValueError("PR counts must be non-negative")
        if self.total_prs != (self.merged_prs + self.closed_prs + self.open_prs):
            raise ValueError("PR counts must sum to total")
        if not 0 <= self.merge_rate <= 100:
            raise ValueError("Merge rate must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PR metrics to dictionary."""
        return {
            'total_prs': self.total_prs,
            'merged_prs': self.merged_prs,
            'closed_prs': self.closed_prs,
            'open_prs': self.open_prs,
            'average_time_to_merge': self.average_time_to_merge,
            'average_additions': self.average_additions,
            'average_deletions': self.average_deletions,
            'average_commits_per_pr': self.average_commits_per_pr,
            'merge_rate': self.merge_rate
        }


@dataclass
class ReviewMetrics:
    """Metrics related to code review activity."""
    total_reviews_given: int
    total_reviews_received: int
    average_review_time: Optional[float]  # hours
    approval_rate: float  # percentage
    change_request_rate: float  # percentage
    review_participation_rate: float  # percentage
    
    def __post_init__(self):
        """Validate review metrics."""
        if any(val < 0 for val in [self.total_reviews_given, self.total_reviews_received]):
            raise ValueError("Review counts must be non-negative")
        if not all(0 <= rate <= 100 for rate in [self.approval_rate, self.change_request_rate, 
                                                  self.review_participation_rate]):
            raise ValueError("All rates must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review metrics to dictionary."""
        return {
            'total_reviews_given': self.total_reviews_given,
            'total_reviews_received': self.total_reviews_received,
            'average_review_time': self.average_review_time,
            'approval_rate': self.approval_rate,
            'change_request_rate': self.change_request_rate,
            'review_participation_rate': self.review_participation_rate
        }


@dataclass
class IssueMetrics:
    """Metrics related to issue activity."""
    total_issues: int
    closed_issues: int
    open_issues: int
    average_time_to_close: Optional[float]  # hours
    resolution_rate: float  # percentage
    issues_created: int
    issues_assigned: int
    
    def __post_init__(self):
        """Validate issue metrics."""
        if any(val < 0 for val in [self.total_issues, self.closed_issues, self.open_issues,
                                   self.issues_created, self.issues_assigned]):
            raise ValueError("Issue counts must be non-negative")
        if self.total_issues != (self.closed_issues + self.open_issues):
            raise ValueError("Issue counts must sum to total")
        if not 0 <= self.resolution_rate <= 100:
            raise ValueError("Resolution rate must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue metrics to dictionary."""
        return {
            'total_issues': self.total_issues,
            'closed_issues': self.closed_issues,
            'open_issues': self.open_issues,
            'average_time_to_close': self.average_time_to_close,
            'resolution_rate': self.resolution_rate,
            'issues_created': self.issues_created,
            'issues_assigned': self.issues_assigned
        }


@dataclass
class ProductivityMetrics:
    """Comprehensive productivity metrics for a developer or team."""
    period_start: datetime
    period_end: datetime
    commit_metrics: CommitMetrics
    pr_metrics: PRMetrics
    review_metrics: ReviewMetrics
    issue_metrics: IssueMetrics
    velocity_trends: List[VelocityPoint] = field(default_factory=list)
    time_distribution: Dict[str, float] = field(default_factory=dict)  # activity type -> hours
    
    def __post_init__(self):
        """Validate productivity metrics."""
        if self.period_end <= self.period_start:
            raise ValueError("Period end must be after period start")
    
    @property
    def period_days(self) -> int:
        """Calculate number of days in the period."""
        return (self.period_end - self.period_start).days
    
    @property
    def daily_commit_average(self) -> float:
        """Calculate average commits per day."""
        if self.period_days == 0:
            return 0.0
        return self.commit_metrics.total_commits / self.period_days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert productivity metrics to dictionary."""
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'commit_metrics': self.commit_metrics.to_dict(),
            'pr_metrics': self.pr_metrics.to_dict(),
            'review_metrics': self.review_metrics.to_dict(),
            'issue_metrics': self.issue_metrics.to_dict(),
            'velocity_trends': [vp.to_dict() for vp in self.velocity_trends],
            'time_distribution': self.time_distribution
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductivityMetrics':
        """Create productivity metrics from dictionary."""
        return cls(
            period_start=datetime.fromisoformat(data['period_start']),
            period_end=datetime.fromisoformat(data['period_end']),
            commit_metrics=CommitMetrics(**data['commit_metrics']),
            pr_metrics=PRMetrics(**data['pr_metrics']),
            review_metrics=ReviewMetrics(**data['review_metrics']),
            issue_metrics=IssueMetrics(**data['issue_metrics']),
            velocity_trends=[VelocityPoint.from_dict(vp) for vp in data.get('velocity_trends', [])],
            time_distribution=data.get('time_distribution', {})
        )


@dataclass
class Anomaly:
    """Represents an anomaly detected in productivity data."""
    metric_name: str
    timestamp: datetime
    expected_value: float
    actual_value: float
    severity: str  # LOW, MEDIUM, HIGH
    description: str
    
    def __post_init__(self):
        """Validate anomaly data."""
        if not self.metric_name:
            raise ValueError("Metric name cannot be empty")
        if self.severity not in ['LOW', 'MEDIUM', 'HIGH']:
            raise ValueError("Severity must be LOW, MEDIUM, or HIGH")
    
    @property
    def deviation_percentage(self) -> float:
        """Calculate percentage deviation from expected value."""
        if self.expected_value == 0:
            return 0.0
        return abs((self.actual_value - self.expected_value) / self.expected_value) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert anomaly to dictionary."""
        return {
            'metric_name': self.metric_name,
            'timestamp': self.timestamp.isoformat(),
            'expected_value': self.expected_value,
            'actual_value': self.actual_value,
            'severity': self.severity,
            'description': self.description
        }


@dataclass
class AnalysisReport:
    """AI-generated analysis report for productivity data."""
    generated_at: datetime
    summary: str
    key_insights: List[str]
    recommendations: List[str]
    anomalies: List[Anomaly]
    confidence_score: float
    
    def __post_init__(self):
        """Validate analysis report."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        if not self.summary:
            raise ValueError("Summary cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis report to dictionary."""
        return {
            'generated_at': self.generated_at.isoformat(),
            'summary': self.summary,
            'key_insights': self.key_insights,
            'recommendations': self.recommendations,
            'anomalies': [anomaly.to_dict() for anomaly in self.anomalies],
            'confidence_score': self.confidence_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisReport':
        """Create analysis report from dictionary."""
        return cls(
            generated_at=datetime.fromisoformat(data['generated_at']),
            summary=data['summary'],
            key_insights=data['key_insights'],
            recommendations=data['recommendations'],
            anomalies=[Anomaly(**anomaly) for anomaly in data.get('anomalies', [])],
            confidence_score=data['confidence_score']
        )