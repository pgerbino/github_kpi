"""
Core data models for GitHub Productivity Dashboard.

This module contains the fundamental data structures for representing
GitHub entities and productivity metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class PullRequestState(Enum):
    """Enumeration for pull request states."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class IssueState(Enum):
    """Enumeration for issue states."""
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Commit:
    """Represents a Git commit with productivity metrics."""
    sha: str
    author: str
    timestamp: datetime
    message: str
    additions: int
    deletions: int
    files_changed: int
    
    def __post_init__(self):
        """Validate commit data after initialization."""
        if not self.sha:
            raise ValueError("Commit SHA cannot be empty")
        if not self.author:
            raise ValueError("Commit author cannot be empty")
        if self.additions < 0 or self.deletions < 0:
            raise ValueError("Additions and deletions must be non-negative")
        if self.files_changed < 0:
            raise ValueError("Files changed must be non-negative")
    
    @property
    def net_changes(self) -> int:
        """Calculate net lines changed (additions - deletions)."""
        return self.additions - self.deletions
    
    @property
    def total_changes(self) -> int:
        """Calculate total lines changed (additions + deletions)."""
        return self.additions + self.deletions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert commit to dictionary for serialization."""
        return {
            'sha': self.sha,
            'author': self.author,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'additions': self.additions,
            'deletions': self.deletions,
            'files_changed': self.files_changed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Commit':
        """Create commit from dictionary."""
        return cls(
            sha=data['sha'],
            author=data['author'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            message=data['message'],
            additions=data['additions'],
            deletions=data['deletions'],
            files_changed=data['files_changed']
        )


@dataclass
class Review:
    """Represents a code review on a pull request."""
    reviewer: str
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED
    submitted_at: datetime
    body: Optional[str] = None
    
    def __post_init__(self):
        """Validate review data after initialization."""
        if not self.reviewer:
            raise ValueError("Reviewer cannot be empty")
        valid_states = ['APPROVED', 'CHANGES_REQUESTED', 'COMMENTED']
        if self.state not in valid_states:
            raise ValueError(f"Review state must be one of: {valid_states}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary for serialization."""
        return {
            'reviewer': self.reviewer,
            'state': self.state,
            'submitted_at': self.submitted_at.isoformat(),
            'body': self.body
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Create review from dictionary."""
        return cls(
            reviewer=data['reviewer'],
            state=data['state'],
            submitted_at=datetime.fromisoformat(data['submitted_at']),
            body=data.get('body')
        )


@dataclass
class PullRequest:
    """Represents a GitHub pull request with metrics."""
    number: int
    title: str
    author: str
    created_at: datetime
    state: PullRequestState
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    additions: int = 0
    deletions: int = 0
    commits: int = 0
    reviews: List[Review] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate pull request data after initialization."""
        if self.number <= 0:
            raise ValueError("Pull request number must be positive")
        if not self.title:
            raise ValueError("Pull request title cannot be empty")
        if not self.author:
            raise ValueError("Pull request author cannot be empty")
        if self.additions < 0 or self.deletions < 0:
            raise ValueError("Additions and deletions must be non-negative")
        if self.commits < 0:
            raise ValueError("Commits count must be non-negative")
    
    @property
    def is_merged(self) -> bool:
        """Check if pull request is merged."""
        return self.state == PullRequestState.MERGED and self.merged_at is not None
    
    @property
    def time_to_merge(self) -> Optional[int]:
        """Calculate time to merge in hours."""
        if self.merged_at:
            return int((self.merged_at - self.created_at).total_seconds() / 3600)
        return None
    
    @property
    def review_count(self) -> int:
        """Get number of reviews."""
        return len(self.reviews)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pull request to dictionary for serialization."""
        return {
            'number': self.number,
            'title': self.title,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'state': self.state.value,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'additions': self.additions,
            'deletions': self.deletions,
            'commits': self.commits,
            'reviews': [review.to_dict() for review in self.reviews]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PullRequest':
        """Create pull request from dictionary."""
        return cls(
            number=data['number'],
            title=data['title'],
            author=data['author'],
            created_at=datetime.fromisoformat(data['created_at']),
            state=PullRequestState(data['state']),
            merged_at=datetime.fromisoformat(data['merged_at']) if data.get('merged_at') else None,
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None,
            additions=data.get('additions', 0),
            deletions=data.get('deletions', 0),
            commits=data.get('commits', 0),
            reviews=[Review.from_dict(review) for review in data.get('reviews', [])]
        )


@dataclass
class Issue:
    """Represents a GitHub issue."""
    number: int
    title: str
    author: str
    created_at: datetime
    state: IssueState
    closed_at: Optional[datetime] = None
    assignee: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    body: Optional[str] = None
    
    def __post_init__(self):
        """Validate issue data after initialization."""
        if self.number <= 0:
            raise ValueError("Issue number must be positive")
        if not self.title:
            raise ValueError("Issue title cannot be empty")
        if not self.author:
            raise ValueError("Issue author cannot be empty")
    
    @property
    def is_closed(self) -> bool:
        """Check if issue is closed."""
        return self.state == IssueState.CLOSED and self.closed_at is not None
    
    @property
    def time_to_close(self) -> Optional[int]:
        """Calculate time to close in hours."""
        if self.closed_at:
            return int((self.closed_at - self.created_at).total_seconds() / 3600)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary for serialization."""
        return {
            'number': self.number,
            'title': self.title,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'state': self.state.value,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'assignee': self.assignee,
            'labels': self.labels,
            'body': self.body
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create issue from dictionary."""
        return cls(
            number=data['number'],
            title=data['title'],
            author=data['author'],
            created_at=datetime.fromisoformat(data['created_at']),
            state=IssueState(data['state']),
            closed_at=datetime.fromisoformat(data['closed_at']) if data.get('closed_at') else None,
            assignee=data.get('assignee'),
            labels=data.get('labels', []),
            body=data.get('body')
        )