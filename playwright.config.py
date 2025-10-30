"""
Playwright configuration for GitHub Productivity Dashboard UI tests.
"""

from playwright.sync_api import Playwright
import pytest


def pytest_configure(config):
    """Configure pytest for Playwright tests."""
    config.addinivalue_line(
        "markers", "ui: mark test as UI test requiring Playwright"
    )


def pytest_collection_modifyitems(config, items):
    """Add UI marker to Playwright tests."""
    for item in items:
        if "test_ui_playwright" in str(item.fspath):
            item.add_marker(pytest.mark.ui)


# Playwright configuration
PLAYWRIGHT_CONFIG = {
    "headless": True,  # Set to False to see browser during tests
    "slow_mo": 100,    # Slow down operations by 100ms for better visibility
    "timeout": 30000,  # 30 second timeout for operations
    "viewport": {"width": 1280, "height": 720},
    "ignore_https_errors": True,
    "screenshot": "only-on-failure",
    "video": "retain-on-failure",
}

# Browser configuration
BROWSERS = ["chromium"]  # Can add "firefox", "webkit" for cross-browser testing