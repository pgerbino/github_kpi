"""
Unit tests for metrics calculator.

Tests metric calculations with known datasets and validates time-series data generation.
"""

import unittest
from datetime import datetime, timedelta
from typing import List

from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from models.metrics import MetricPeriod, VelocityPoint, CommitMetrics, PRMetrics
from utils.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    """Test cases for MetricsCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()
        self.base_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # Create test commits
        self.test_commits = [
            Commit(
                sha='commit1',
                author='user1',
                timestamp=self.base_time,
                message='First commit',
                additions=10,
                deletions=5,
                files_changed=2
            ),
            Commit(
                sha='commit2',
                author='user1',
                timestamp=self.base_time + timedelta(hours=2),
                message='Second commit with longer message',
                additions=20,
                deletions=10,
                files_changed=3
            ),
            Commit(
                sha='commit3',
                author='user2',
                timestamp=self.base_time + timedelta(days=1),
                message='Third commit',
                additions=15,
                deletions=8,
                files_changed=1
            )
        ]
        
        # Create test pull requests
        self.test_reviews = [
            Review(
                reviewer='reviewer1',
                state='APPROVED',
                submitted_at=self.base_time + timedelta(hours=1)
            ),
            Review(
                reviewer='reviewer2',
                state='CHANGES_REQUESTED',
                submitted_at=self.base_time + timedelta(hours=2)
            )
        ]
        
        self.test_pull_requests = [
            PullRequest(
                number=1,
                title='Test PR 1',
                author='user1',
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
                author='user2',
                created_at=self.base_time + timedelta(days=1),
                state=PullRequestState.OPEN,
                additions=25,
                deletions=12,
                commits=3,
                reviews=[]
            )
        ]
        
        # Create test issues
        self.test_issues = [
            Issue(
                number=1,
                title='Test Issue 1',
                author='user1',
                created_at=self.base_time,
                state=IssueState.CLOSED,
                closed_at=self.base_time + timedelta(hours=48),
                assignee='user2',
                labels=['bug', 'high-priority']
            ),
            Issue(
                number=2,
                title='Test Issue 2',
                author='user2',
                created_at=self.base_time + timedelta(days=1),
                state=IssueState.OPEN,
                assignee='user1',
                labels=['feature']
            )
        ]
    
    def test_calculate_commit_metrics_empty_list(self):
        """Test commit metrics calculation with empty commit list."""
        metrics = self.calculator.calculate_commit_metrics([])
        
        self.assertEqual(metrics.total_commits, 0)
        self.assertEqual(metrics.average_additions, 0.0)
        self.assertEqual(metrics.average_deletions, 0.0)
        self.assertEqual(metrics.average_files_changed, 0.0)
        self.assertEqual(metrics.commit_message_length_avg, 0.0)
        self.assertEqual(len(metrics.most_active_hours), 0)
        self.assertEqual(len(metrics.commit_frequency), 0)
    
    def test_calculate_commit_metrics_with_data(self):
        """Test commit metrics calculation with test data."""
        metrics = self.calculator.calculate_commit_metrics(self.test_commits)
        
        self.assertEqual(metrics.total_commits, 3)
        
        # Test averages
        expected_avg_additions = (10 + 20 + 15) / 3  # 15.0
        expected_avg_deletions = (5 + 10 + 8) / 3   # 7.67
        expected_avg_files = (2 + 3 + 1) / 3         # 2.0
        
        self.assertAlmostEqual(metrics.average_additions, expected_avg_additions, places=2)
        self.assertAlmostEqual(metrics.average_deletions, expected_avg_deletions, places=2)
        self.assertAlmostEqual(metrics.average_files_changed, expected_avg_files, places=2)
        
        # Test commit frequency structure
        self.assertIn('daily', metrics.commit_frequency)
        self.assertIn('weekly', metrics.commit_frequency)
        self.assertIn('monthly', metrics.commit_frequency)
        self.assertIn('hourly', metrics.commit_frequency)
        
        # Test most active hours
        self.assertIsInstance(metrics.most_active_hours, list)
        self.assertIn(12, metrics.most_active_hours)  # Base time hour
    
    def test_calculate_pr_metrics_empty_list(self):
        """Test PR metrics calculation with empty PR list."""
        metrics = self.calculator.calculate_pr_metrics([])
        
        self.assertEqual(metrics.total_prs, 0)
        self.assertEqual(metrics.merged_prs, 0)
        self.assertEqual(metrics.closed_prs, 0)
        self.assertEqual(metrics.open_prs, 0)
        self.assertEqual(metrics.merge_rate, 0.0)
        self.assertIsNone(metrics.average_time_to_merge)
        self.assertEqual(metrics.average_additions, 0.0)
        self.assertEqual(metrics.average_deletions, 0.0)
        self.assertEqual(metrics.average_commits_per_pr, 0.0)
    
    def test_calculate_pr_metrics_with_data(self):
        """Test PR metrics calculation with test data."""
        metrics = self.calculator.calculate_pr_metrics(self.test_pull_requests)
        
        self.assertEqual(metrics.total_prs, 2)
        self.assertEqual(metrics.merged_prs, 1)
        self.assertEqual(metrics.closed_prs, 0)
        self.assertEqual(metrics.open_prs, 1)
        
        # Test merge rate
        expected_merge_rate = (1 / 2) * 100  # 50%
        self.assertEqual(metrics.merge_rate, expected_merge_rate)
        
        # Test averages
        expected_avg_additions = (30 + 25) / 2  # 27.5
        expected_avg_deletions = (15 + 12) / 2  # 13.5
        expected_avg_commits = (2 + 3) / 2      # 2.5
        
        self.assertAlmostEqual(metrics.average_additions, expected_avg_additions, places=2)
        self.assertAlmostEqual(metrics.average_deletions, expected_avg_deletions, places=2)
        self.assertAlmostEqual(metrics.average_commits_per_pr, expected_avg_commits, places=2)
        
        # Test time to merge (should be 24 hours for the merged PR)
        self.assertIsNotNone(metrics.average_time_to_merge)
        self.assertEqual(metrics.average_time_to_merge, 24.0)
    
    def test_generate_time_series_data_empty(self):
        """Test time series generation with empty data."""
        velocity_points = self.calculator.generate_time_series_data([], [], [])
        
        self.assertEqual(len(velocity_points), 0)
    
    def test_generate_time_series_data_daily(self):
        """Test daily time series generation."""
        velocity_points = self.calculator.generate_time_series_data(
            self.test_commits, 
            self.test_pull_requests, 
            self.test_issues,
            MetricPeriod.DAILY
        )
        
        self.assertGreater(len(velocity_points), 0)
        
        # Check that all velocity points are VelocityPoint instances
        for point in velocity_points:
            self.assertIsInstance(point, VelocityPoint)
            self.assertGreaterEqual(point.commits, 0)
            self.assertGreaterEqual(point.additions, 0)
            self.assertGreaterEqual(point.deletions, 0)
            self.assertGreaterEqual(point.pull_requests, 0)
            self.assertGreaterEqual(point.issues_closed, 0)
        
        # Test that first day has expected data
        first_day = velocity_points[0]
        self.assertEqual(first_day.commits, 2)  # Two commits on first day
        self.assertEqual(first_day.additions, 30)  # 10 + 20
        self.assertEqual(first_day.deletions, 15)  # 5 + 10
        self.assertEqual(first_day.pull_requests, 1)  # One PR created on first day
    
    def test_generate_time_series_data_weekly(self):
        """Test weekly time series generation."""
        velocity_points = self.calculator.generate_time_series_data(
            self.test_commits, 
            self.test_pull_requests, 
            self.test_issues,
            MetricPeriod.WEEKLY
        )
        
        self.assertGreater(len(velocity_points), 0)
        
        # Should have fewer points than daily
        daily_points = self.calculator.generate_time_series_data(
            self.test_commits, 
            self.test_pull_requests, 
            self.test_issues,
            MetricPeriod.DAILY
        )
        self.assertLessEqual(len(velocity_points), len(daily_points))
    
    def test_calculate_productivity_metrics_comprehensive(self):
        """Test comprehensive productivity metrics calculation."""
        period_start = self.base_time - timedelta(days=1)
        period_end = self.base_time + timedelta(days=2)
        
        metrics = self.calculator.calculate_productivity_metrics(
            self.test_commits,
            self.test_pull_requests,
            self.test_issues,
            period_start,
            period_end
        )
        
        # Test basic structure
        self.assertEqual(metrics.period_start, period_start)
        self.assertEqual(metrics.period_end, period_end)
        self.assertEqual(metrics.period_days, 3)
        
        # Test that all metric components are present
        self.assertIsInstance(metrics.commit_metrics, CommitMetrics)
        self.assertIsInstance(metrics.pr_metrics, PRMetrics)
        self.assertIsNotNone(metrics.review_metrics)
        self.assertIsNotNone(metrics.issue_metrics)
        
        # Test velocity trends
        self.assertIsInstance(metrics.velocity_trends, list)
        self.assertGreater(len(metrics.velocity_trends), 0)
        
        # Test time distribution
        self.assertIsInstance(metrics.time_distribution, dict)
        
        # Test daily commit average
        expected_daily_avg = 3 / 3  # 3 commits over 3 days
        self.assertEqual(metrics.daily_commit_average, expected_daily_avg)
    
    def test_commit_frequency_calculation(self):
        """Test detailed commit frequency calculation."""
        metrics = self.calculator.calculate_commit_metrics(self.test_commits)
        
        # Test daily frequency
        daily_freq = metrics.commit_frequency['daily']
        self.assertIn('2023-01-01', daily_freq)
        self.assertIn('2023-01-02', daily_freq)
        self.assertEqual(daily_freq['2023-01-01'], 2)  # Two commits on first day
        self.assertEqual(daily_freq['2023-01-02'], 1)  # One commit on second day
        
        # Test hourly frequency
        hourly_freq = metrics.commit_frequency['hourly']
        self.assertIn('12', hourly_freq)  # Base time hour
        self.assertIn('14', hourly_freq)  # Base time + 2 hours
        self.assertEqual(hourly_freq['12'], 2)  # Two commits at hour 12
        self.assertEqual(hourly_freq['14'], 1)  # One commit at hour 14
    
    def test_most_active_hours_calculation(self):
        """Test most active hours calculation."""
        # Create commits at specific hours
        commits_with_hours = [
            Commit('sha1', 'user1', datetime(2023, 1, 1, 9, 0), 'msg1', 10, 5, 1),
            Commit('sha2', 'user1', datetime(2023, 1, 1, 9, 30), 'msg2', 10, 5, 1),
            Commit('sha3', 'user1', datetime(2023, 1, 1, 14, 0), 'msg3', 10, 5, 1),
            Commit('sha4', 'user1', datetime(2023, 1, 1, 14, 30), 'msg4', 10, 5, 1),
            Commit('sha5', 'user1', datetime(2023, 1, 1, 14, 45), 'msg5', 10, 5, 1),
        ]
        
        metrics = self.calculator.calculate_commit_metrics(commits_with_hours)
        
        # Hour 14 should be most active (3 commits), then hour 9 (2 commits)
        self.assertIn(14, metrics.most_active_hours)
        self.assertIn(9, metrics.most_active_hours)
        self.assertEqual(metrics.most_active_hours[0], 14)  # Most active first
    
    def test_time_distribution_calculation(self):
        """Test time distribution calculation."""
        time_dist = self.calculator._calculate_time_distribution(
            self.test_commits, 
            self.test_pull_requests
        )
        
        self.assertIn('coding', time_dist)
        self.assertIn('code_review', time_dist)
        
        # Percentages should sum to 100 (excluding 'other')
        total_percentage = time_dist['coding'] + time_dist['code_review']
        self.assertAlmostEqual(total_percentage, 100.0, places=1)
        
        # All values should be non-negative
        for value in time_dist.values():
            self.assertGreaterEqual(value, 0.0)
    
    def test_velocity_point_properties(self):
        """Test VelocityPoint properties and calculations."""
        velocity_points = self.calculator.generate_time_series_data(
            self.test_commits, 
            self.test_pull_requests, 
            self.test_issues
        )
        
        for point in velocity_points:
            # Test total_changes property
            expected_total = point.additions + point.deletions
            self.assertEqual(point.total_changes, expected_total)
            
            # Test that timestamp is a datetime
            self.assertIsInstance(point.timestamp, datetime)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with single commit
        single_commit = [self.test_commits[0]]
        metrics = self.calculator.calculate_commit_metrics(single_commit)
        self.assertEqual(metrics.total_commits, 1)
        self.assertEqual(metrics.average_additions, 10.0)
        
        # Test with single PR
        single_pr = [self.test_pull_requests[0]]
        pr_metrics = self.calculator.calculate_pr_metrics(single_pr)
        self.assertEqual(pr_metrics.total_prs, 1)
        self.assertEqual(pr_metrics.merge_rate, 100.0)  # 1 merged out of 1
        
        # Test with same timestamp commits
        same_time_commits = [
            Commit('sha1', 'user1', self.base_time, 'msg1', 10, 5, 1),
            Commit('sha2', 'user2', self.base_time, 'msg2', 15, 8, 2),
        ]
        
        velocity_points = self.calculator.generate_time_series_data(
            same_time_commits, [], []
        )
        
        # Should still generate valid velocity points
        self.assertGreater(len(velocity_points), 0)
        first_point = velocity_points[0]
        self.assertEqual(first_point.commits, 2)
        self.assertEqual(first_point.additions, 25)  # 10 + 15


if __name__ == '__main__':
    unittest.main()