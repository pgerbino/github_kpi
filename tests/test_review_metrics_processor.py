"""
Unit tests for review metrics processor.

Tests review participation analysis, issue resolution metrics, and quality calculations.
"""

import unittest
from datetime import datetime, timedelta
from typing import List

from models.core import PullRequest, Issue, Review, PullRequestState, IssueState
from models.metrics import ReviewMetrics, IssueMetrics
from utils.review_metrics_processor import ReviewMetricsProcessor


class TestReviewMetricsProcessor(unittest.TestCase):
    """Test cases for ReviewMetricsProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = ReviewMetricsProcessor()
        self.base_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # Create test reviews
        self.test_reviews = [
            Review(
                reviewer='reviewer1',
                state='APPROVED',
                submitted_at=self.base_time + timedelta(hours=2),
                body='Looks good!'
            ),
            Review(
                reviewer='reviewer2',
                state='CHANGES_REQUESTED',
                submitted_at=self.base_time + timedelta(hours=4),
                body='Please fix the bug'
            ),
            Review(
                reviewer='reviewer3',
                state='COMMENTED',
                submitted_at=self.base_time + timedelta(hours=6),
                body='Just a comment'
            )
        ]
        
        # Create test pull requests
        self.test_pull_requests = [
            PullRequest(
                number=1,
                title='Test PR 1',
                author='author1',
                created_at=self.base_time,
                state=PullRequestState.MERGED,
                merged_at=self.base_time + timedelta(hours=24),
                additions=30,
                deletions=15,
                commits=2,
                reviews=self.test_reviews
            ),
            PullRequest(
                number=2,
                title='Test PR 2',
                author='author2',
                created_at=self.base_time + timedelta(days=1),
                state=PullRequestState.OPEN,
                additions=25,
                deletions=12,
                commits=3,
                reviews=[
                    Review(
                        reviewer='reviewer1',
                        state='APPROVED',
                        submitted_at=self.base_time + timedelta(days=1, hours=1)
                    )
                ]
            ),
            PullRequest(
                number=3,
                title='Test PR 3',
                author='author1',
                created_at=self.base_time + timedelta(days=2),
                state=PullRequestState.CLOSED,
                closed_at=self.base_time + timedelta(days=3),
                additions=10,
                deletions=5,
                commits=1,
                reviews=[]  # No reviews
            )
        ]
        
        # Create test issues
        self.test_issues = [
            Issue(
                number=1,
                title='Bug Issue',
                author='author1',
                created_at=self.base_time,
                state=IssueState.CLOSED,
                closed_at=self.base_time + timedelta(hours=48),
                assignee='assignee1',
                labels=['bug', 'high-priority'],
                body='Critical bug description'
            ),
            Issue(
                number=2,
                title='Feature Request',
                author='author2',
                created_at=self.base_time + timedelta(days=1),
                state=IssueState.OPEN,
                assignee='assignee2',
                labels=['feature', 'enhancement'],
                body='New feature request'
            ),
            Issue(
                number=3,
                title='Documentation',
                author='author1',
                created_at=self.base_time + timedelta(days=2),
                state=IssueState.CLOSED,
                closed_at=self.base_time + timedelta(days=2, hours=12),
                assignee='assignee1',
                labels=['documentation'],
                body='Update documentation'
            )
        ]
    
    def test_calculate_review_metrics_empty_list(self):
        """Test review metrics calculation with empty PR list."""
        metrics = self.processor.calculate_review_metrics([])
        
        self.assertEqual(metrics.total_reviews_given, 0)
        self.assertEqual(metrics.total_reviews_received, 0)
        self.assertIsNone(metrics.average_review_time)
        self.assertEqual(metrics.approval_rate, 0.0)
        self.assertEqual(metrics.change_request_rate, 0.0)
        self.assertEqual(metrics.review_participation_rate, 0.0)
    
    def test_calculate_review_metrics_general(self):
        """Test general review metrics calculation."""
        metrics = self.processor.calculate_review_metrics(self.test_pull_requests)
        
        # Total reviews across all PRs: 3 + 1 + 0 = 4
        self.assertEqual(metrics.total_reviews_given, 4)
        self.assertEqual(metrics.total_reviews_received, 4)
        
        # Approval rate: 2 approvals out of 4 reviews = 50%
        self.assertEqual(metrics.approval_rate, 50.0)
        
        # Change request rate: 1 change request out of 4 reviews = 25%
        self.assertEqual(metrics.change_request_rate, 25.0)
        
        # Participation rate: 2 PRs with reviews out of 3 total = 66.67%
        self.assertAlmostEqual(metrics.review_participation_rate, 66.67, places=1)
        
        # Average review time should be calculated
        self.assertIsNotNone(metrics.average_review_time)
        self.assertGreater(metrics.average_review_time, 0)
    
    def test_calculate_review_metrics_specific_author(self):
        """Test review metrics for specific author."""
        # Test metrics for reviewer1
        metrics = self.processor.calculate_review_metrics(
            self.test_pull_requests, 
            target_author='reviewer1'
        )
        
        # reviewer1 gave 2 reviews
        self.assertEqual(metrics.total_reviews_given, 2)
        
        # reviewer1 received 0 reviews (no PRs by reviewer1)
        self.assertEqual(metrics.total_reviews_received, 0)
        
        # Both of reviewer1's reviews were approvals = 100%
        self.assertEqual(metrics.approval_rate, 100.0)
        self.assertEqual(metrics.change_request_rate, 0.0)
        
        # Participation rate: reviewer1 reviewed 2 out of 3 PRs they could review = 66.67%
        self.assertAlmostEqual(metrics.review_participation_rate, 66.67, places=1)
    
    def test_calculate_review_metrics_author_with_prs(self):
        """Test review metrics for author who also has PRs."""
        # Test metrics for author1 (has 2 PRs)
        metrics = self.processor.calculate_review_metrics(
            self.test_pull_requests, 
            target_author='author1'
        )
        
        # author1 gave 0 reviews
        self.assertEqual(metrics.total_reviews_given, 0)
        
        # author1 received 3 reviews on their PRs (PR #1 has 3 reviews, PR #3 has 0)
        self.assertEqual(metrics.total_reviews_received, 3)
        
        # No reviews given, so rates should be 0
        self.assertEqual(metrics.approval_rate, 0.0)
        self.assertEqual(metrics.change_request_rate, 0.0)
        
        # Participation rate: author1 could review 1 PR (not their own), reviewed 0 = 0%
        self.assertEqual(metrics.review_participation_rate, 0.0)
    
    def test_calculate_issue_metrics_empty_list(self):
        """Test issue metrics calculation with empty issue list."""
        metrics = self.processor.calculate_issue_metrics([])
        
        self.assertEqual(metrics.total_issues, 0)
        self.assertEqual(metrics.closed_issues, 0)
        self.assertEqual(metrics.open_issues, 0)
        self.assertIsNone(metrics.average_time_to_close)
        self.assertEqual(metrics.resolution_rate, 0.0)
        self.assertEqual(metrics.issues_created, 0)
        self.assertEqual(metrics.issues_assigned, 0)
    
    def test_calculate_issue_metrics_general(self):
        """Test general issue metrics calculation."""
        metrics = self.processor.calculate_issue_metrics(self.test_issues)
        
        self.assertEqual(metrics.total_issues, 3)
        self.assertEqual(metrics.closed_issues, 2)  # Issues 1 and 3 are closed
        self.assertEqual(metrics.open_issues, 1)    # Issue 2 is open
        
        # Resolution rate: 2 closed out of 3 total = 66.67%
        self.assertAlmostEqual(metrics.resolution_rate, 66.67, places=1)
        
        # All issues were created in general calculation
        self.assertEqual(metrics.issues_created, 3)
        
        # All issues have assignees
        self.assertEqual(metrics.issues_assigned, 3)
        
        # Average time to close should be calculated from closed issues
        self.assertIsNotNone(metrics.average_time_to_close)
        self.assertGreater(metrics.average_time_to_close, 0)
    
    def test_calculate_issue_metrics_specific_author(self):
        """Test issue metrics for specific author."""
        # Test metrics for author1
        metrics = self.processor.calculate_issue_metrics(
            self.test_issues, 
            target_author='author1'
        )
        
        # Still shows total issues in system
        self.assertEqual(metrics.total_issues, 3)
        self.assertEqual(metrics.closed_issues, 2)
        self.assertEqual(metrics.open_issues, 1)
        
        # author1 created 2 issues (issues 1 and 3)
        self.assertEqual(metrics.issues_created, 2)
        
        # author1 is assigned to 1 issue (issue 1 is assigned to assignee1, issue 3 to assignee1)
        # Actually, let's check the test data - assignee1 is assigned to issues 1 and 3
        # But we're filtering by author1, so we need to check assignments to author1
        author1_assigned = len([i for i in self.test_issues if i.assignee == 'author1'])
        self.assertEqual(metrics.issues_assigned, author1_assigned)
    
    def test_analyze_review_patterns(self):
        """Test detailed review pattern analysis."""
        analysis = self.processor.analyze_review_patterns(self.test_pull_requests)
        
        # Check structure
        self.assertIn('reviewer_analysis', analysis)
        self.assertIn('total_reviewers', analysis)
        self.assertIn('most_active_reviewers', analysis)
        self.assertIn('fastest_reviewers', analysis)
        
        # Check reviewer analysis
        reviewer_analysis = analysis['reviewer_analysis']
        self.assertIn('reviewer1', reviewer_analysis)
        self.assertIn('reviewer2', reviewer_analysis)
        self.assertIn('reviewer3', reviewer_analysis)
        
        # Check reviewer1 stats
        reviewer1_stats = reviewer_analysis['reviewer1']
        self.assertEqual(reviewer1_stats['total_reviews'], 2)
        self.assertEqual(reviewer1_stats['approval_rate'], 100.0)  # Both approvals
        self.assertEqual(reviewer1_stats['change_request_rate'], 0.0)
        self.assertEqual(reviewer1_stats['comment_rate'], 0.0)
        
        # Check reviewer2 stats
        reviewer2_stats = reviewer_analysis['reviewer2']
        self.assertEqual(reviewer2_stats['total_reviews'], 1)
        self.assertEqual(reviewer2_stats['approval_rate'], 0.0)
        self.assertEqual(reviewer2_stats['change_request_rate'], 100.0)  # One change request
        
        # Check totals
        self.assertEqual(analysis['total_reviewers'], 3)
        
        # Check most active reviewers list
        most_active = analysis['most_active_reviewers']
        self.assertIsInstance(most_active, list)
        self.assertGreater(len(most_active), 0)
        
        # reviewer1 should be most active with 2 reviews
        self.assertEqual(most_active[0]['reviewer'], 'reviewer1')
        self.assertEqual(most_active[0]['review_count'], 2)
    
    def test_analyze_issue_resolution_patterns(self):
        """Test issue resolution pattern analysis."""
        analysis = self.processor.analyze_issue_resolution_patterns(self.test_issues)
        
        # Check structure
        self.assertIn('label_analysis', analysis)
        self.assertIn('assignee_analysis', analysis)
        self.assertIn('total_labels', analysis)
        self.assertIn('total_assignees', analysis)
        
        # Check label analysis
        label_analysis = analysis['label_analysis']
        self.assertIn('bug', label_analysis)
        self.assertIn('feature', label_analysis)
        self.assertIn('documentation', label_analysis)
        
        # Check bug label stats
        bug_stats = label_analysis['bug']
        self.assertEqual(bug_stats['total_issues'], 1)
        self.assertEqual(bug_stats['closed_issues'], 1)
        self.assertEqual(bug_stats['resolution_rate'], 100.0)
        
        # Check feature label stats
        feature_stats = label_analysis['feature']
        self.assertEqual(feature_stats['total_issues'], 1)
        self.assertEqual(feature_stats['closed_issues'], 0)
        self.assertEqual(feature_stats['resolution_rate'], 0.0)
        
        # Check assignee analysis
        assignee_analysis = analysis['assignee_analysis']
        self.assertIn('assignee1', assignee_analysis)
        self.assertIn('assignee2', assignee_analysis)
        
        # Check assignee1 stats (assigned to issues 1 and 3, both closed)
        assignee1_stats = assignee_analysis['assignee1']
        self.assertEqual(assignee1_stats['total_issues'], 2)
        self.assertEqual(assignee1_stats['closed_issues'], 2)
        self.assertEqual(assignee1_stats['resolution_rate'], 100.0)
        
        # Check assignee2 stats (assigned to issue 2, open)
        assignee2_stats = assignee_analysis['assignee2']
        self.assertEqual(assignee2_stats['total_issues'], 1)
        self.assertEqual(assignee2_stats['closed_issues'], 0)
        self.assertEqual(assignee2_stats['resolution_rate'], 0.0)
    
    def test_review_response_times(self):
        """Test review response time calculations."""
        # Create PR with known timing
        pr_created = datetime(2023, 1, 1, 10, 0, 0)
        review_time = pr_created + timedelta(hours=3)
        
        test_pr = PullRequest(
            number=1,
            title='Timing Test PR',
            author='author1',
            created_at=pr_created,
            state=PullRequestState.OPEN,
            reviews=[
                Review(
                    reviewer='reviewer1',
                    state='APPROVED',
                    submitted_at=review_time
                )
            ]
        )
        
        metrics = self.processor.calculate_review_metrics([test_pr])
        
        # Should be 3 hours response time
        self.assertAlmostEqual(metrics.average_review_time, 3.0, places=1)
    
    def test_issue_resolution_times(self):
        """Test issue resolution time calculations."""
        # Create issue with known timing
        issue_created = datetime(2023, 1, 1, 10, 0, 0)
        issue_closed = issue_created + timedelta(hours=24)
        
        test_issue = Issue(
            number=1,
            title='Timing Test Issue',
            author='author1',
            created_at=issue_created,
            state=IssueState.CLOSED,
            closed_at=issue_closed
        )
        
        metrics = self.processor.calculate_issue_metrics([test_issue])
        
        # Should be 24 hours resolution time
        self.assertAlmostEqual(metrics.average_time_to_close, 24.0, places=1)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with PR that has no reviews
        no_review_pr = PullRequest(
            number=1,
            title='No Review PR',
            author='author1',
            created_at=self.base_time,
            state=PullRequestState.OPEN,
            reviews=[]
        )
        
        metrics = self.processor.calculate_review_metrics([no_review_pr])
        self.assertEqual(metrics.total_reviews_given, 0)
        self.assertEqual(metrics.review_participation_rate, 0.0)
        
        # Test with issue that was never closed
        open_issue = Issue(
            number=1,
            title='Open Issue',
            author='author1',
            created_at=self.base_time,
            state=IssueState.OPEN
        )
        
        issue_metrics = self.processor.calculate_issue_metrics([open_issue])
        self.assertEqual(issue_metrics.closed_issues, 0)
        self.assertEqual(issue_metrics.resolution_rate, 0.0)
        self.assertIsNone(issue_metrics.average_time_to_close)
    
    def test_participation_rate_calculation(self):
        """Test review participation rate calculation logic."""
        # Create PRs where reviewer1 could review 2 PRs but only reviewed 1
        prs = [
            PullRequest(
                number=1,
                title='PR 1',
                author='author1',
                created_at=self.base_time,
                state=PullRequestState.OPEN,
                reviews=[
                    Review('reviewer1', 'APPROVED', self.base_time + timedelta(hours=1))
                ]
            ),
            PullRequest(
                number=2,
                title='PR 2',
                author='author2',
                created_at=self.base_time,
                state=PullRequestState.OPEN,
                reviews=[]  # reviewer1 didn't review this
            ),
            PullRequest(
                number=3,
                title='PR 3',
                author='reviewer1',  # reviewer1's own PR
                created_at=self.base_time,
                state=PullRequestState.OPEN,
                reviews=[]
            )
        ]
        
        metrics = self.processor.calculate_review_metrics(prs, target_author='reviewer1')
        
        # reviewer1 could review 2 PRs (not their own), reviewed 1 = 50%
        self.assertEqual(metrics.review_participation_rate, 50.0)


if __name__ == '__main__':
    unittest.main()