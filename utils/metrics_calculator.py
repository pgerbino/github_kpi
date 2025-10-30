"""
Productivity metrics calculator for GitHub Productivity Dashboard.

This module provides functions to calculate various productivity metrics
from GitHub data including commit frequency, code volume, and PR statistics.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass

from models.core import Commit, PullRequest, Issue, Review
from models.metrics import (
    CommitMetrics, PRMetrics, VelocityPoint, MetricPeriod,
    ProductivityMetrics
)


class MetricsCalculator:
    """Calculator for productivity metrics from GitHub data."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    def calculate_commit_metrics(self, commits: List[Commit]) -> CommitMetrics:
        """
        Calculate commit-related productivity metrics.
        
        Args:
            commits: List of commits to analyze
            
        Returns:
            CommitMetrics: Calculated commit metrics
        """
        if not commits:
            return CommitMetrics(
                total_commits=0,
                commit_frequency={},
                average_additions=0.0,
                average_deletions=0.0,
                average_files_changed=0.0,
                most_active_hours=[],
                commit_message_length_avg=0.0
            )
        
        total_commits = len(commits)
        
        # Calculate frequency by different periods
        commit_frequency = self._calculate_commit_frequency(commits)
        
        # Calculate averages
        total_additions = sum(commit.additions for commit in commits)
        total_deletions = sum(commit.deletions for commit in commits)
        total_files_changed = sum(commit.files_changed for commit in commits)
        total_message_length = sum(len(commit.message) for commit in commits)
        
        average_additions = total_additions / total_commits
        average_deletions = total_deletions / total_commits
        average_files_changed = total_files_changed / total_commits
        commit_message_length_avg = total_message_length / total_commits
        
        # Find most active hours
        most_active_hours = self._find_most_active_hours(commits)
        
        return CommitMetrics(
            total_commits=total_commits,
            commit_frequency=commit_frequency,
            average_additions=average_additions,
            average_deletions=average_deletions,
            average_files_changed=average_files_changed,
            most_active_hours=most_active_hours,
            commit_message_length_avg=commit_message_length_avg
        )
    
    def calculate_pr_metrics(self, pull_requests: List[PullRequest]) -> PRMetrics:
        """
        Calculate pull request related productivity metrics.
        
        Args:
            pull_requests: List of pull requests to analyze
            
        Returns:
            PRMetrics: Calculated PR metrics
        """
        if not pull_requests:
            return PRMetrics(
                total_prs=0,
                merged_prs=0,
                closed_prs=0,
                open_prs=0,
                average_time_to_merge=None,
                average_additions=0.0,
                average_deletions=0.0,
                average_commits_per_pr=0.0,
                merge_rate=0.0
            )
        
        total_prs = len(pull_requests)
        merged_prs = sum(1 for pr in pull_requests if pr.is_merged)
        closed_prs = sum(1 for pr in pull_requests if pr.state.value == 'closed' and not pr.is_merged)
        open_prs = sum(1 for pr in pull_requests if pr.state.value == 'open')
        
        # Calculate merge rate
        merge_rate = (merged_prs / total_prs) * 100 if total_prs > 0 else 0.0
        
        # Calculate average time to merge for merged PRs
        merge_times = [pr.time_to_merge for pr in pull_requests if pr.time_to_merge is not None]
        average_time_to_merge = statistics.mean(merge_times) if merge_times else None
        
        # Calculate code change averages
        total_additions = sum(pr.additions for pr in pull_requests)
        total_deletions = sum(pr.deletions for pr in pull_requests)
        total_commits = sum(pr.commits for pr in pull_requests)
        
        average_additions = total_additions / total_prs
        average_deletions = total_deletions / total_prs
        average_commits_per_pr = total_commits / total_prs
        
        return PRMetrics(
            total_prs=total_prs,
            merged_prs=merged_prs,
            closed_prs=closed_prs,
            open_prs=open_prs,
            average_time_to_merge=average_time_to_merge,
            average_additions=average_additions,
            average_deletions=average_deletions,
            average_commits_per_pr=average_commits_per_pr,
            merge_rate=merge_rate
        )
    
    def generate_time_series_data(self, commits: List[Commit], pull_requests: List[PullRequest], 
                                 issues: List[Issue], period: MetricPeriod = MetricPeriod.DAILY) -> List[VelocityPoint]:
        """
        Generate time-series data for trend analysis.
        
        Args:
            commits: List of commits
            pull_requests: List of pull requests
            issues: List of issues
            period: Time period for aggregation
            
        Returns:
            List[VelocityPoint]: Time-series velocity data
        """
        if not commits and not pull_requests and not issues:
            return []
        
        # Determine date range
        all_dates = []
        if commits:
            all_dates.extend([commit.timestamp for commit in commits])
        if pull_requests:
            all_dates.extend([pr.created_at for pr in pull_requests])
        if issues:
            all_dates.extend([issue.created_at for issue in issues])
        
        if not all_dates:
            return []
        
        start_date = min(all_dates).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = max(all_dates).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Generate time buckets based on period
        time_buckets = self._generate_time_buckets(start_date, end_date, period)
        
        # Aggregate data by time buckets
        velocity_points = []
        for bucket_start, bucket_end in time_buckets:
            # Count commits in this bucket
            bucket_commits = [c for c in commits if bucket_start <= c.timestamp <= bucket_end]
            commit_count = len(bucket_commits)
            additions = sum(c.additions for c in bucket_commits)
            deletions = sum(c.deletions for c in bucket_commits)
            
            # Count PRs created in this bucket
            pr_count = len([pr for pr in pull_requests if bucket_start <= pr.created_at <= bucket_end])
            
            # Count issues closed in this bucket
            issues_closed = len([
                issue for issue in issues 
                if issue.closed_at and bucket_start <= issue.closed_at <= bucket_end
            ])
            
            velocity_point = VelocityPoint(
                timestamp=bucket_start,
                commits=commit_count,
                additions=additions,
                deletions=deletions,
                pull_requests=pr_count,
                issues_closed=issues_closed
            )
            velocity_points.append(velocity_point)
        
        return velocity_points
    
    def calculate_productivity_metrics(self, commits: List[Commit], pull_requests: List[PullRequest], 
                                     issues: List[Issue], period_start: datetime, 
                                     period_end: datetime) -> ProductivityMetrics:
        """
        Calculate comprehensive productivity metrics for a given period.
        
        Args:
            commits: List of commits
            pull_requests: List of pull requests
            issues: List of issues
            period_start: Start of analysis period
            period_end: End of analysis period
            
        Returns:
            ProductivityMetrics: Comprehensive productivity metrics
        """
        # Calculate individual metric components
        commit_metrics = self.calculate_commit_metrics(commits)
        pr_metrics = self.calculate_pr_metrics(pull_requests)
        
        # Generate velocity trends
        velocity_trends = self.generate_time_series_data(commits, pull_requests, issues)
        
        # Calculate time distribution (placeholder - would need more detailed data)
        time_distribution = self._calculate_time_distribution(commits, pull_requests)
        
        # Calculate review and issue metrics using the review metrics processor
        from utils.review_metrics_processor import ReviewMetricsProcessor
        processor = ReviewMetricsProcessor()
        
        review_metrics = processor.calculate_review_metrics(pull_requests)
        issue_metrics = processor.calculate_issue_metrics(issues)
        
        return ProductivityMetrics(
            period_start=period_start,
            period_end=period_end,
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=velocity_trends,
            time_distribution=time_distribution
        )
    
    def _calculate_commit_frequency(self, commits: List[Commit]) -> Dict[str, int]:
        """Calculate commit frequency by different time periods."""
        frequency = {
            'daily': defaultdict(int),
            'weekly': defaultdict(int),
            'monthly': defaultdict(int),
            'hourly': defaultdict(int)
        }
        
        for commit in commits:
            # Daily frequency
            day_key = commit.timestamp.strftime('%Y-%m-%d')
            frequency['daily'][day_key] += 1
            
            # Weekly frequency (ISO week)
            week_key = f"{commit.timestamp.year}-W{commit.timestamp.isocalendar()[1]:02d}"
            frequency['weekly'][week_key] += 1
            
            # Monthly frequency
            month_key = commit.timestamp.strftime('%Y-%m')
            frequency['monthly'][month_key] += 1
            
            # Hourly frequency
            hour_key = str(commit.timestamp.hour)
            frequency['hourly'][hour_key] += 1
        
        # Convert defaultdicts to regular dicts
        return {
            period: dict(freq_dict) for period, freq_dict in frequency.items()
        }
    
    def _find_most_active_hours(self, commits: List[Commit], top_n: int = 3) -> List[int]:
        """Find the most active hours of the day for commits."""
        hour_counts = Counter(commit.timestamp.hour for commit in commits)
        most_common = hour_counts.most_common(top_n)
        return [hour for hour, count in most_common]
    
    def _generate_time_buckets(self, start_date: datetime, end_date: datetime, 
                              period: MetricPeriod) -> List[Tuple[datetime, datetime]]:
        """Generate time buckets for the given period."""
        buckets = []
        current = start_date
        
        if period == MetricPeriod.DAILY:
            delta = timedelta(days=1)
        elif period == MetricPeriod.WEEKLY:
            delta = timedelta(weeks=1)
        elif period == MetricPeriod.MONTHLY:
            delta = timedelta(days=30)  # Approximate
        elif period == MetricPeriod.QUARTERLY:
            delta = timedelta(days=90)  # Approximate
        else:
            delta = timedelta(days=1)  # Default to daily
        
        while current <= end_date:
            bucket_end = min(current + delta - timedelta(microseconds=1), end_date)
            buckets.append((current, bucket_end))
            current += delta
        
        return buckets
    
    def _calculate_time_distribution(self, commits: List[Commit], 
                                   pull_requests: List[PullRequest]) -> Dict[str, float]:
        """Calculate time distribution across different activities."""
        # This is a simplified calculation - in reality would need more detailed timing data
        total_commits = len(commits)
        total_prs = len(pull_requests)
        
        # Estimate time spent based on activity counts (placeholder logic)
        commit_time = total_commits * 0.5  # Assume 30 minutes per commit
        pr_time = total_prs * 2.0  # Assume 2 hours per PR
        
        total_time = commit_time + pr_time
        
        if total_time == 0:
            return {}
        
        return {
            'coding': (commit_time / total_time) * 100,
            'code_review': (pr_time / total_time) * 100,
            'other': 0.0
        }