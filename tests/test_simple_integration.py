"""
Simple integration test for GitHub Productivity Dashboard core workflow.

This test validates the basic end-to-end functionality without complex mocking.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from models.metrics import ProductivityMetrics
from utils.metrics_calculator import MetricsCalculator
from utils.review_metrics_processor import ReviewMetricsProcessor


def test_basic_integration_workflow():
    """Test basic integration workflow with minimal data."""
    
    # Create minimal test data
    base_time = datetime.now() - timedelta(days=7)
    
    # Create sample commits
    commits = [
        Commit(
            sha="abc123",
            author="test-user",
            timestamp=base_time,
            message="Test commit",
            additions=50,
            deletions=20,
            files_changed=2
        ),
        Commit(
            sha="def456",
            author="test-user",
            timestamp=base_time + timedelta(days=1),
            message="Another commit",
            additions=30,
            deletions=10,
            files_changed=1
        )
    ]
    
    # Create sample pull requests
    pull_requests = [
        PullRequest(
            number=1,
            title="Test PR",
            author="test-user",
            created_at=base_time,
            state=PullRequestState.MERGED,
            merged_at=base_time + timedelta(hours=2),
            additions=80,
            deletions=30,
            commits=2,
            reviews=[
                Review(
                    reviewer="reviewer1",
                    state="APPROVED",
                    submitted_at=base_time + timedelta(hours=1)
                )
            ]
        )
    ]
    
    # Create sample issues
    issues = [
        Issue(
            number=1,
            title="Test issue",
            author="test-user",
            created_at=base_time,
            state=IssueState.CLOSED,
            closed_at=base_time + timedelta(hours=4),
            assignee="test-user",
            labels=["bug"]
        )
    ]
    
    # Test metrics calculation
    calculator = MetricsCalculator()
    processor = ReviewMetricsProcessor()
    
    # Calculate individual metrics
    commit_metrics = calculator.calculate_commit_metrics(commits)
    pr_metrics = calculator.calculate_pr_metrics(pull_requests)
    review_metrics = processor.calculate_review_metrics(pull_requests)
    issue_metrics = processor.calculate_issue_metrics(issues)
    
    # Validate basic metrics
    assert commit_metrics.total_commits == 2
    assert pr_metrics.total_prs == 1
    assert pr_metrics.merged_prs == 1
    assert issue_metrics.total_issues == 1
    assert issue_metrics.closed_issues == 1
    
    # Test velocity trends generation
    velocity_trends = calculator.generate_time_series_data(commits, pull_requests, issues)
    assert len(velocity_trends) > 0
    
    # Test integrated metrics creation using the full calculator method
    integrated_metrics = calculator.calculate_productivity_metrics(
        commits=commits,
        pull_requests=pull_requests,
        issues=issues,
        period_start=base_time,
        period_end=datetime.now()
    )
    
    # Validate integrated metrics
    assert integrated_metrics.commit_metrics.total_commits == 2
    assert integrated_metrics.pr_metrics.total_prs == 1
    assert integrated_metrics.issue_metrics.total_issues == 1
    assert integrated_metrics.period_days > 0
    
    print("✅ Basic integration workflow test passed!")


def test_export_integration():
    """Test export functionality integration."""
    
    # Create minimal test data
    base_time = datetime.now() - timedelta(days=7)
    
    commits = [
        Commit(
            sha="test123",
            author="test-user",
            timestamp=base_time,
            message="Export test commit",
            additions=25,
            deletions=5,
            files_changed=1
        )
    ]
    
    # Calculate metrics
    calculator = MetricsCalculator()
    integrated_metrics = calculator.calculate_productivity_metrics(
        commits=commits,
        pull_requests=[],
        issues=[],
        period_start=base_time,
        period_end=datetime.now()
    )
    
    # Test export functionality
    from utils.export_manager import ExportManager
    export_manager = ExportManager()
    
    # Test CSV export
    csv_content = export_manager.csv_exporter.export_productivity_metrics(
        integrated_metrics, include_config=True
    )
    
    # Validate export
    assert csv_content is not None
    assert len(csv_content) > 50  # Should have substantial content
    print(f"CSV content preview: {csv_content[:200]}...")
    # Check for key content instead of exact header
    assert 'commit' in csv_content.lower() or 'metric' in csv_content.lower()
    assert str(integrated_metrics.commit_metrics.total_commits) in csv_content
    
    # Test filename generation
    filename = export_manager.create_export_filename("test_metrics", integrated_metrics, "csv")
    assert filename.endswith('.csv')
    assert 'test_metrics' in filename
    
    print("✅ Export integration test passed!")


def test_performance_with_larger_dataset():
    """Test performance with a larger dataset."""
    
    # Create larger test dataset
    base_time = datetime.now() - timedelta(days=30)
    
    # Generate 100 commits
    commits = []
    for i in range(100):
        commit = Commit(
            sha=f"commit{i:03d}",
            author=f"user{i % 5}",  # 5 different users
            timestamp=base_time + timedelta(days=i % 30, hours=i % 24),
            message=f"Commit {i}",
            additions=10 + (i % 50),
            deletions=5 + (i % 20),
            files_changed=1 + (i % 5)
        )
        commits.append(commit)
    
    # Generate 20 pull requests
    pull_requests = []
    for i in range(20):
        pr = PullRequest(
            number=i + 1,
            title=f"PR {i}",
            author=f"user{i % 5}",
            created_at=base_time + timedelta(days=i),
            state=PullRequestState.MERGED if i % 3 != 0 else PullRequestState.OPEN,
            merged_at=base_time + timedelta(days=i, hours=2) if i % 3 != 0 else None,
            additions=50 + (i * 10),
            deletions=20 + (i * 5),
            commits=2 + (i % 3),
            reviews=[]
        )
        pull_requests.append(pr)
    
    # Test metrics calculation with larger dataset
    calculator = MetricsCalculator()
    
    start_time = datetime.now()
    integrated_metrics = calculator.calculate_productivity_metrics(
        commits=commits,
        pull_requests=pull_requests,
        issues=[],
        period_start=base_time,
        period_end=datetime.now()
    )
    calculation_time = (datetime.now() - start_time).total_seconds()
    
    # Validate results
    assert integrated_metrics.commit_metrics.total_commits == 100
    assert integrated_metrics.pr_metrics.total_prs == 20
    assert calculation_time < 5.0  # Should complete within 5 seconds
    
    print(f"✅ Performance test passed! Calculation time: {calculation_time:.2f}s")


if __name__ == "__main__":
    test_basic_integration_workflow()
    test_export_integration()
    test_performance_with_larger_dataset()
    print("🎉 All integration tests passed!")