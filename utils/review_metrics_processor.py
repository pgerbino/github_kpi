"""
Code review and issue metrics processor for GitHub Productivity Dashboard.

This module provides functions to analyze PR review participation, issue resolution,
and calculate review response times and quality metrics.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter
import statistics

from models.core import PullRequest, Issue, Review
from models.metrics import ReviewMetrics, IssueMetrics


class ReviewMetricsProcessor:
    """Processor for code review and issue metrics."""
    
    def __init__(self):
        """Initialize review metrics processor."""
        pass
    
    def calculate_review_metrics(self, pull_requests: List[PullRequest], 
                               target_author: Optional[str] = None) -> ReviewMetrics:
        """
        Calculate code review participation and quality metrics.
        
        Args:
            pull_requests: List of pull requests to analyze
            target_author: Optional specific author to calculate metrics for
            
        Returns:
            ReviewMetrics: Calculated review metrics
        """
        if not pull_requests:
            return ReviewMetrics(
                total_reviews_given=0,
                total_reviews_received=0,
                average_review_time=None,
                approval_rate=0.0,
                change_request_rate=0.0,
                review_participation_rate=0.0
            )
        
        # Collect all reviews
        all_reviews = []
        reviews_given = []
        reviews_received = []
        
        for pr in pull_requests:
            all_reviews.extend(pr.reviews)
            
            if target_author:
                # Reviews given by target author
                reviews_given.extend([r for r in pr.reviews if r.reviewer == target_author])
                
                # Reviews received by target author (on their PRs)
                if pr.author == target_author:
                    reviews_received.extend(pr.reviews)
            else:
                # All reviews for general metrics
                reviews_given = all_reviews
                reviews_received = all_reviews
        
        total_reviews_given = len(reviews_given)
        total_reviews_received = len(reviews_received)
        
        # Calculate review response times
        review_times = self._calculate_review_response_times(pull_requests)
        average_review_time = statistics.mean(review_times) if review_times else None
        
        # Calculate approval and change request rates
        approval_rate = self._calculate_approval_rate(reviews_given)
        change_request_rate = self._calculate_change_request_rate(reviews_given)
        
        # Calculate review participation rate
        review_participation_rate = self._calculate_participation_rate(pull_requests, target_author)
        
        return ReviewMetrics(
            total_reviews_given=total_reviews_given,
            total_reviews_received=total_reviews_received,
            average_review_time=average_review_time,
            approval_rate=approval_rate,
            change_request_rate=change_request_rate,
            review_participation_rate=review_participation_rate
        )
    
    def calculate_issue_metrics(self, issues: List[Issue], 
                              target_author: Optional[str] = None) -> IssueMetrics:
        """
        Calculate issue resolution and management metrics.
        
        Args:
            issues: List of issues to analyze
            target_author: Optional specific author to calculate metrics for
            
        Returns:
            IssueMetrics: Calculated issue metrics
        """
        if not issues:
            return IssueMetrics(
                total_issues=0,
                closed_issues=0,
                open_issues=0,
                average_time_to_close=None,
                resolution_rate=0.0,
                issues_created=0,
                issues_assigned=0
            )
        
        # Filter issues by target author if specified
        if target_author:
            author_issues = [issue for issue in issues if issue.author == target_author]
            assigned_issues = [issue for issue in issues if issue.assignee == target_author]
        else:
            author_issues = issues
            assigned_issues = [issue for issue in issues if issue.assignee]
        
        total_issues = len(issues)
        closed_issues = len([issue for issue in issues if issue.is_closed])
        open_issues = total_issues - closed_issues
        
        # Calculate average time to close
        close_times = [issue.time_to_close for issue in issues if issue.time_to_close is not None]
        average_time_to_close = statistics.mean(close_times) if close_times else None
        
        # Calculate resolution rate
        resolution_rate = (closed_issues / total_issues) * 100 if total_issues > 0 else 0.0
        
        issues_created = len(author_issues)
        issues_assigned = len(assigned_issues)
        
        return IssueMetrics(
            total_issues=total_issues,
            closed_issues=closed_issues,
            open_issues=open_issues,
            average_time_to_close=average_time_to_close,
            resolution_rate=resolution_rate,
            issues_created=issues_created,
            issues_assigned=issues_assigned
        )
    
    def analyze_review_patterns(self, pull_requests: List[PullRequest]) -> Dict[str, any]:
        """
        Analyze detailed review patterns and behaviors.
        
        Args:
            pull_requests: List of pull requests to analyze
            
        Returns:
            Dict containing detailed review pattern analysis
        """
        if not pull_requests:
            return {}
        
        # Collect reviewer statistics
        reviewer_stats = defaultdict(lambda: {
            'reviews_count': 0,
            'approvals': 0,
            'change_requests': 0,
            'comments': 0,
            'response_times': []
        })
        
        # Analyze each PR and its reviews
        for pr in pull_requests:
            pr_created = pr.created_at
            
            for review in pr.reviews:
                reviewer = review.reviewer
                reviewer_stats[reviewer]['reviews_count'] += 1
                
                # Count review types
                if review.state == 'APPROVED':
                    reviewer_stats[reviewer]['approvals'] += 1
                elif review.state == 'CHANGES_REQUESTED':
                    reviewer_stats[reviewer]['change_requests'] += 1
                elif review.state == 'COMMENTED':
                    reviewer_stats[reviewer]['comments'] += 1
                
                # Calculate response time
                response_time = (review.submitted_at - pr_created).total_seconds() / 3600  # hours
                reviewer_stats[reviewer]['response_times'].append(response_time)
        
        # Calculate summary statistics for each reviewer
        reviewer_analysis = {}
        for reviewer, stats in reviewer_stats.items():
            total_reviews = stats['reviews_count']
            if total_reviews > 0:
                reviewer_analysis[reviewer] = {
                    'total_reviews': total_reviews,
                    'approval_rate': (stats['approvals'] / total_reviews) * 100,
                    'change_request_rate': (stats['change_requests'] / total_reviews) * 100,
                    'comment_rate': (stats['comments'] / total_reviews) * 100,
                    'average_response_time': statistics.mean(stats['response_times']) if stats['response_times'] else None,
                    'median_response_time': statistics.median(stats['response_times']) if stats['response_times'] else None
                }
        
        return {
            'reviewer_analysis': reviewer_analysis,
            'total_reviewers': len(reviewer_stats),
            'most_active_reviewers': self._get_most_active_reviewers(reviewer_stats),
            'fastest_reviewers': self._get_fastest_reviewers(reviewer_stats)
        }
    
    def analyze_issue_resolution_patterns(self, issues: List[Issue]) -> Dict[str, any]:
        """
        Analyze issue resolution patterns and trends.
        
        Args:
            issues: List of issues to analyze
            
        Returns:
            Dict containing issue resolution pattern analysis
        """
        if not issues:
            return {}
        
        # Analyze by labels
        label_stats = defaultdict(lambda: {
            'total': 0,
            'closed': 0,
            'resolution_times': []
        })
        
        # Analyze by assignee
        assignee_stats = defaultdict(lambda: {
            'total': 0,
            'closed': 0,
            'resolution_times': []
        })
        
        for issue in issues:
            # Label analysis
            for label in issue.labels:
                label_stats[label]['total'] += 1
                if issue.is_closed:
                    label_stats[label]['closed'] += 1
                    if issue.time_to_close:
                        label_stats[label]['resolution_times'].append(issue.time_to_close)
            
            # Assignee analysis
            if issue.assignee:
                assignee = issue.assignee
                assignee_stats[assignee]['total'] += 1
                if issue.is_closed:
                    assignee_stats[assignee]['closed'] += 1
                    if issue.time_to_close:
                        assignee_stats[assignee]['resolution_times'].append(issue.time_to_close)
        
        # Calculate summary statistics
        label_analysis = {}
        for label, stats in label_stats.items():
            if stats['total'] > 0:
                label_analysis[label] = {
                    'total_issues': stats['total'],
                    'closed_issues': stats['closed'],
                    'resolution_rate': (stats['closed'] / stats['total']) * 100,
                    'average_resolution_time': statistics.mean(stats['resolution_times']) if stats['resolution_times'] else None
                }
        
        assignee_analysis = {}
        for assignee, stats in assignee_stats.items():
            if stats['total'] > 0:
                assignee_analysis[assignee] = {
                    'total_issues': stats['total'],
                    'closed_issues': stats['closed'],
                    'resolution_rate': (stats['closed'] / stats['total']) * 100,
                    'average_resolution_time': statistics.mean(stats['resolution_times']) if stats['resolution_times'] else None
                }
        
        return {
            'label_analysis': label_analysis,
            'assignee_analysis': assignee_analysis,
            'total_labels': len(label_stats),
            'total_assignees': len(assignee_stats)
        }
    
    def _calculate_review_response_times(self, pull_requests: List[PullRequest]) -> List[float]:
        """Calculate review response times in hours."""
        response_times = []
        
        for pr in pull_requests:
            pr_created = pr.created_at
            
            for review in pr.reviews:
                response_time = (review.submitted_at - pr_created).total_seconds() / 3600  # hours
                response_times.append(response_time)
        
        return response_times
    
    def _calculate_approval_rate(self, reviews: List[Review]) -> float:
        """Calculate the percentage of reviews that were approvals."""
        if not reviews:
            return 0.0
        
        approvals = len([r for r in reviews if r.state == 'APPROVED'])
        return (approvals / len(reviews)) * 100
    
    def _calculate_change_request_rate(self, reviews: List[Review]) -> float:
        """Calculate the percentage of reviews that requested changes."""
        if not reviews:
            return 0.0
        
        change_requests = len([r for r in reviews if r.state == 'CHANGES_REQUESTED'])
        return (change_requests / len(reviews)) * 100
    
    def _calculate_participation_rate(self, pull_requests: List[PullRequest], 
                                    target_author: Optional[str] = None) -> float:
        """Calculate review participation rate."""
        if not pull_requests:
            return 0.0
        
        if target_author:
            # Calculate participation rate for specific author
            # PRs where they could have reviewed (not their own)
            reviewable_prs = [pr for pr in pull_requests if pr.author != target_author]
            if not reviewable_prs:
                return 0.0
            
            # PRs where they actually reviewed
            participated_prs = len([
                pr for pr in reviewable_prs 
                if any(review.reviewer == target_author for review in pr.reviews)
            ])
            
            return (participated_prs / len(reviewable_prs)) * 100
        else:
            # General participation rate - PRs that received at least one review
            reviewed_prs = len([pr for pr in pull_requests if pr.reviews])
            return (reviewed_prs / len(pull_requests)) * 100
    
    def _get_most_active_reviewers(self, reviewer_stats: Dict, top_n: int = 5) -> List[Dict]:
        """Get the most active reviewers by review count."""
        sorted_reviewers = sorted(
            reviewer_stats.items(),
            key=lambda x: x[1]['reviews_count'],
            reverse=True
        )
        
        return [
            {
                'reviewer': reviewer,
                'review_count': stats['reviews_count']
            }
            for reviewer, stats in sorted_reviewers[:top_n]
        ]
    
    def _get_fastest_reviewers(self, reviewer_stats: Dict, top_n: int = 5) -> List[Dict]:
        """Get the fastest reviewers by average response time."""
        reviewers_with_times = [
            (reviewer, stats) for reviewer, stats in reviewer_stats.items()
            if stats['response_times']
        ]
        
        sorted_reviewers = sorted(
            reviewers_with_times,
            key=lambda x: statistics.mean(x[1]['response_times'])
        )
        
        return [
            {
                'reviewer': reviewer,
                'average_response_time': statistics.mean(stats['response_times'])
            }
            for reviewer, stats in sorted_reviewers[:top_n]
        ]