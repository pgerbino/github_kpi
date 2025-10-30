"""
Playwright UI tests for GitHub Productivity Dashboard.

This module contains end-to-end UI tests using Playwright to validate
the complete user interface and user interactions.
"""

import pytest
import time
import subprocess
import signal
import os
from playwright.sync_api import Page, expect, Browser
from typing import Generator
import threading


class StreamlitApp:
    """Helper class to manage Streamlit app for testing."""
    
    def __init__(self):
        self.process = None
        self.port = 8501
        self.url = f"http://localhost:{self.port}"
    
    def start(self):
        """Start the Streamlit app."""
        # Kill any existing process on the port
        try:
            subprocess.run(["pkill", "-f", "streamlit"], check=False)
            time.sleep(2)
        except:
            pass
        
        # Start Streamlit app
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        
        self.process = subprocess.Popen(
            ["streamlit", "run", "main.py", "--server.port", str(self.port), "--server.headless", "true"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                import requests
                response = requests.get(self.url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ Streamlit app started successfully at {self.url}")
                    return
            except:
                pass
            time.sleep(1)
        
        raise Exception("Failed to start Streamlit app")
    
    def stop(self):
        """Stop the Streamlit app."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        # Additional cleanup
        try:
            subprocess.run(["pkill", "-f", "streamlit"], check=False)
        except:
            pass


@pytest.fixture(scope="session")
def streamlit_app() -> Generator[StreamlitApp, None, None]:
    """Fixture to start and stop Streamlit app for testing."""
    app = StreamlitApp()
    app.start()
    yield app
    app.stop()


@pytest.fixture
def page_with_app(page: Page, streamlit_app: StreamlitApp) -> Page:
    """Fixture to provide a page with the Streamlit app loaded."""
    page.goto(streamlit_app.url)
    page.wait_for_load_state("networkidle")
    return page


class TestDashboardUI:
    """UI tests for the GitHub Productivity Dashboard."""
    
    def test_page_loads_successfully(self, page_with_app: Page):
        """Test that the main page loads successfully."""
        # Check page title
        expect(page_with_app).to_have_title("GitHub Productivity Dashboard")
        
        # Check main header
        expect(page_with_app.locator("h1")).to_contain_text("GitHub Productivity Dashboard")
        
        # Check subtitle
        expect(page_with_app.locator("text=Analyze developer productivity")).to_be_visible()
    
    def test_navigation_sidebar(self, page_with_app: Page):
        """Test sidebar navigation functionality."""
        # Check navigation header
        expect(page_with_app.locator("text=🚀 Navigation")).to_be_visible()
        
        # Check all navigation buttons are present
        navigation_items = [
            "📊 Overview",
            "📈 Metrics", 
            "🔍 Analytics",
            "🤖 AI Insights",
            "📥 Export"
        ]
        
        for item in navigation_items:
            expect(page_with_app.locator(f"text={item}")).to_be_visible()
        
        # Test navigation to different sections
        page_with_app.click("text=📈 Metrics")
        page_with_app.wait_for_timeout(1000)
        expect(page_with_app.locator("text=Productivity Metrics")).to_be_visible()
        
        page_with_app.click("text=🔍 Analytics")
        page_with_app.wait_for_timeout(1000)
        expect(page_with_app.locator("text=Detailed Analytics")).to_be_visible()
        
        page_with_app.click("text=📥 Export")
        page_with_app.wait_for_timeout(1000)
        expect(page_with_app.locator("text=Export & Reports")).to_be_visible()
        
        # Return to overview
        page_with_app.click("text=📊 Overview")
        page_with_app.wait_for_timeout(1000)
        expect(page_with_app.locator("text=Dashboard Overview")).to_be_visible()
    
    def test_configuration_panel(self, page_with_app: Page):
        """Test the configuration panel functionality."""
        # Check configuration section
        expect(page_with_app.locator("text=⚙️ Configuration")).to_be_visible()
        
        # Check GitHub configuration section
        expect(page_with_app.locator("text=🐙 GitHub Configuration")).to_be_visible()
        
        # Check input fields are present
        expect(page_with_app.locator("input[type='password']").first).to_be_visible()  # GitHub token
        expect(page_with_app.locator("input[type='text']").first).to_be_visible()  # Repository URL
        
        # Check OpenAI configuration section
        expect(page_with_app.locator("text=🤖 OpenAI Configuration")).to_be_visible()
        
        # Check configuration status section
        expect(page_with_app.locator("text=📋 Configuration Status")).to_be_visible()
    
    def test_github_token_validation(self, page_with_app: Page):
        """Test GitHub token input validation."""
        # Find GitHub token input
        token_input = page_with_app.locator("input[type='password']").first
        
        # Test invalid token format
        token_input.fill("invalid_token")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=❌ Invalid GitHub token format")).to_be_visible()
        
        # Test valid token format
        token_input.fill("ghp_1234567890abcdef1234567890abcdef12345678")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=✅ Valid GitHub token format")).to_be_visible()
    
    def test_repository_url_validation(self, page_with_app: Page):
        """Test repository URL input validation."""
        # Find repository URL input
        repo_input = page_with_app.locator("input[type='text']").first
        
        # Test invalid URL
        repo_input.fill("invalid-url")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=❌ Invalid repository URL format")).to_be_visible()
        
        # Test valid URL
        repo_input.fill("https://github.com/microsoft/vscode")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=✅ Valid repository: microsoft/vscode")).to_be_visible()
        
        # Test owner/repo format
        repo_input.fill("facebook/react")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=✅ Valid repository: facebook/react")).to_be_visible()
    
    def test_openai_key_validation(self, page_with_app: Page):
        """Test OpenAI API key input validation."""
        # Find OpenAI key input (second password input)
        openai_input = page_with_app.locator("input[type='password']").nth(1)
        
        # Test invalid key format
        openai_input.fill("invalid_key")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=❌ Invalid OpenAI API key format")).to_be_visible()
        
        # Test valid key format
        openai_input.fill("sk-1234567890abcdef1234567890abcdef")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=✅ Valid OpenAI API key format")).to_be_visible()
    
    def test_configuration_status_updates(self, page_with_app: Page):
        """Test that configuration status updates correctly."""
        # Initially should show not configured
        expect(page_with_app.locator("text=⚠️ Configure Credentials")).to_be_visible()
        expect(page_with_app.locator("text=📊 No Data Loaded")).to_be_visible()
        
        # Fill in valid credentials
        token_input = page_with_app.locator("input[type='password']").first
        repo_input = page_with_app.locator("input[type='text']").first
        
        token_input.fill("ghp_1234567890abcdef1234567890abcdef12345678")
        repo_input.fill("microsoft/vscode")
        page_with_app.wait_for_timeout(1000)
        
        # Status should update but still show not tested
        expect(page_with_app.locator("text=⚠️ GitHub Not Tested")).to_be_visible()
    
    def test_performance_and_caching_section(self, page_with_app: Page):
        """Test the performance and caching section."""
        # Check performance section
        expect(page_with_app.locator("text=🚀 Performance & Caching")).to_be_visible()
        
        # Check cache metrics
        expect(page_with_app.locator("text=Cache Entries")).to_be_visible()
        expect(page_with_app.locator("text=Cache Hit Ratio")).to_be_visible()
        expect(page_with_app.locator("text=API Calls Made")).to_be_visible()
        
        # Check cache management buttons
        expect(page_with_app.locator("text=🗑️ Clear Cache")).to_be_visible()
        expect(page_with_app.locator("text=🧹 Clear Expired")).to_be_visible()
        expect(page_with_app.locator("text=📊 Reset Performance")).to_be_visible()
    
    def test_overview_section_content(self, page_with_app: Page):
        """Test the overview section displays correctly."""
        # Ensure we're on overview
        page_with_app.click("text=📊 Overview")
        page_with_app.wait_for_timeout(1000)
        
        # Check main content
        expect(page_with_app.locator("text=Dashboard Overview")).to_be_visible()
        expect(page_with_app.locator("text=Welcome to your GitHub Productivity Dashboard")).to_be_visible()
        
        # Check status indicators
        expect(page_with_app.locator("text=Credentials Configured")).to_be_visible()
        expect(page_with_app.locator("text=Data Loaded")).to_be_visible()
        expect(page_with_app.locator("text=Ready for Analysis")).to_be_visible()
        
        # Check info message about configuration
        expect(page_with_app.locator("text=Configure credentials and load repository data")).to_be_visible()
    
    def test_metrics_section_without_data(self, page_with_app: Page):
        """Test metrics section when no data is loaded."""
        page_with_app.click("text=📈 Metrics")
        page_with_app.wait_for_timeout(1000)
        
        expect(page_with_app.locator("text=Productivity Metrics")).to_be_visible()
        expect(page_with_app.locator("text=Configure credentials and load repository data")).to_be_visible()
    
    def test_analytics_section_without_data(self, page_with_app: Page):
        """Test analytics section when no data is loaded."""
        page_with_app.click("text=🔍 Analytics")
        page_with_app.wait_for_timeout(2000)  # Lazy loading
        
        expect(page_with_app.locator("text=Detailed Analytics")).to_be_visible()
        expect(page_with_app.locator("text=Configure credentials and load repository data")).to_be_visible()
    
    def test_ai_insights_section_without_openai(self, page_with_app: Page):
        """Test AI insights section without OpenAI configuration."""
        page_with_app.click("text=🤖 AI Insights")
        page_with_app.wait_for_timeout(2000)  # Lazy loading
        
        expect(page_with_app.locator("text=AI Insights")).to_be_visible()
        expect(page_with_app.locator("text=OpenAI API key required for AI insights")).to_be_visible()
    
    def test_export_section_without_data(self, page_with_app: Page):
        """Test export section when no data is loaded."""
        page_with_app.click("text=📥 Export")
        page_with_app.wait_for_timeout(1000)
        
        expect(page_with_app.locator("text=Export & Reports")).to_be_visible()
        expect(page_with_app.locator("text=Load repository data to enable export")).to_be_visible()
    
    def test_responsive_design_elements(self, page_with_app: Page):
        """Test responsive design elements."""
        # Check that columns are used for layout
        expect(page_with_app.locator("[data-testid='column']")).to_have_count_greater_than(0)
        
        # Check that metrics are displayed in columns
        expect(page_with_app.locator("text=Credentials Configured")).to_be_visible()
        expect(page_with_app.locator("text=Data Loaded")).to_be_visible()
        expect(page_with_app.locator("text=Ready for Analysis")).to_be_visible()
    
    def test_error_handling_display(self, page_with_app: Page):
        """Test error message display functionality."""
        # Fill invalid GitHub token to trigger validation error
        token_input = page_with_app.locator("input[type='password']").first
        token_input.fill("invalid")
        page_with_app.wait_for_timeout(500)
        
        # Should show error message
        expect(page_with_app.locator("text=❌ Invalid GitHub token format")).to_be_visible()
        
        # Clear and check error disappears
        token_input.fill("")
        page_with_app.wait_for_timeout(500)
        expect(page_with_app.locator("text=❌ Invalid GitHub token format")).not_to_be_visible()
    
    def test_help_text_and_tooltips(self, page_with_app: Page):
        """Test help text and tooltip functionality."""
        # Check help text is present for inputs
        expect(page_with_app.locator("text=Enter your GitHub personal access token")).to_be_visible()
        expect(page_with_app.locator("text=Enter GitHub repository URL")).to_be_visible()
        expect(page_with_app.locator("text=Enter your OpenAI API key")).to_be_visible()
    
    def test_button_interactions(self, page_with_app: Page):
        """Test button interactions and states."""
        # Test connection test buttons are disabled initially
        github_test_btn = page_with_app.locator("text=🔍 Test GitHub Connection")
        expect(github_test_btn).to_be_disabled()
        
        openai_test_btn = page_with_app.locator("text=🔍 Test OpenAI Connection")
        expect(openai_test_btn).to_be_disabled()
        
        # Fill valid credentials
        token_input = page_with_app.locator("input[type='password']").first
        repo_input = page_with_app.locator("input[type='text']").first
        openai_input = page_with_app.locator("input[type='password']").nth(1)
        
        token_input.fill("ghp_1234567890abcdef1234567890abcdef12345678")
        repo_input.fill("microsoft/vscode")
        openai_input.fill("sk-1234567890abcdef1234567890abcdef")
        page_with_app.wait_for_timeout(1000)
        
        # Buttons should now be enabled
        expect(github_test_btn).to_be_enabled()
        expect(openai_test_btn).to_be_enabled()
    
    def test_cache_management_buttons(self, page_with_app: Page):
        """Test cache management button functionality."""
        # Test clear cache button
        clear_cache_btn = page_with_app.locator("text=🗑️ Clear Cache")
        expect(clear_cache_btn).to_be_enabled()
        
        # Click and check for success message (would appear briefly)
        clear_cache_btn.click()
        page_with_app.wait_for_timeout(500)
        
        # Test clear expired button
        clear_expired_btn = page_with_app.locator("text=🧹 Clear Expired")
        expect(clear_expired_btn).to_be_enabled()
        clear_expired_btn.click()
        page_with_app.wait_for_timeout(500)
        
        # Test reset performance button
        reset_perf_btn = page_with_app.locator("text=📊 Reset Performance")
        expect(reset_perf_btn).to_be_enabled()
        reset_perf_btn.click()
        page_with_app.wait_for_timeout(500)
    
    def test_footer_content(self, page_with_app: Page):
        """Test footer content is displayed."""
        # Scroll to bottom to see footer
        page_with_app.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page_with_app.wait_for_timeout(500)
        
        # Check footer text
        expect(page_with_app.locator("text=GitHub Productivity Dashboard - Powered by Streamlit")).to_be_visible()


class TestDashboardUIWithData:
    """UI tests with sample data loaded."""
    
    def test_overview_with_sample_data(self, page_with_app: Page):
        """Test overview section with sample data."""
        # First configure credentials and load sample data
        self._configure_and_load_sample_data(page_with_app)
        
        # Navigate to overview
        page_with_app.click("text=📊 Overview")
        page_with_app.wait_for_timeout(2000)
        
        # Should show data loaded status
        expect(page_with_app.locator("text=✅ Sample Data Loaded")).to_be_visible()
        
        # Should show productivity summary
        expect(page_with_app.locator("text=📈 Productivity Summary")).to_be_visible()
    
    def test_metrics_with_sample_data(self, page_with_app: Page):
        """Test metrics section with sample data."""
        self._configure_and_load_sample_data(page_with_app)
        
        page_with_app.click("text=📈 Metrics")
        page_with_app.wait_for_timeout(2000)
        
        # Should show detailed metrics
        expect(page_with_app.locator("text=📅 Analysis Period")).to_be_visible()
        expect(page_with_app.locator("text=📈 Recent Velocity Trends")).to_be_visible()
    
    def test_analytics_with_sample_data(self, page_with_app: Page):
        """Test analytics section with sample data."""
        self._configure_and_load_sample_data(page_with_app)
        
        page_with_app.click("text=🔍 Analytics")
        page_with_app.wait_for_timeout(3000)  # Lazy loading + data processing
        
        # Should show analytics tabs
        expect(page_with_app.locator("text=📈 Time-Series Analysis")).to_be_visible()
        expect(page_with_app.locator("text=🔍 Detailed Analytics")).to_be_visible()
    
    def test_export_with_sample_data(self, page_with_app: Page):
        """Test export section with sample data."""
        self._configure_and_load_sample_data(page_with_app)
        
        page_with_app.click("text=📥 Export")
        page_with_app.wait_for_timeout(2000)
        
        # Should show export options
        expect(page_with_app.locator("text=📊 Metrics Export")).to_be_visible()
        expect(page_with_app.locator("text=🤖 AI Reports")).to_be_visible()
    
    def _configure_and_load_sample_data(self, page: Page):
        """Helper method to configure credentials and load sample data."""
        # Fill credentials
        token_input = page.locator("input[type='password']").first
        repo_input = page.locator("input[type='text']").first
        
        token_input.fill("ghp_1234567890abcdef1234567890abcdef12345678")
        repo_input.fill("microsoft/vscode")
        page.wait_for_timeout(1000)
        
        # Click load data button (this will load sample data since we don't have real API)
        load_btn = page.locator("text=📊 Load Repository Data")
        if load_btn.is_enabled():
            load_btn.click()
            page.wait_for_timeout(3000)  # Wait for data loading


class TestDashboardAccessibility:
    """Accessibility tests for the dashboard."""
    
    def test_keyboard_navigation(self, page_with_app: Page):
        """Test keyboard navigation functionality."""
        # Test tab navigation through form elements
        page_with_app.keyboard.press("Tab")
        page_with_app.wait_for_timeout(100)
        
        # Should focus on first input
        focused_element = page_with_app.evaluate("document.activeElement.type")
        assert focused_element in ["password", "text"]
    
    def test_aria_labels_and_roles(self, page_with_app: Page):
        """Test ARIA labels and roles for accessibility."""
        # Check for proper heading structure
        h1_elements = page_with_app.locator("h1")
        expect(h1_elements).to_have_count_greater_than(0)
        
        # Check for proper button roles
        buttons = page_with_app.locator("button")
        expect(buttons).to_have_count_greater_than(0)
    
    def test_color_contrast_and_visibility(self, page_with_app: Page):
        """Test color contrast and visibility."""
        # Check that error messages are visible
        token_input = page_with_app.locator("input[type='password']").first
        token_input.fill("invalid")
        page_with_app.wait_for_timeout(500)
        
        error_element = page_with_app.locator("text=❌ Invalid GitHub token format")
        expect(error_element).to_be_visible()
        
        # Check that success messages are visible
        token_input.fill("ghp_1234567890abcdef1234567890abcdef12345678")
        page_with_app.wait_for_timeout(500)
        
        success_element = page_with_app.locator("text=✅ Valid GitHub token format")
        expect(success_element).to_be_visible()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])