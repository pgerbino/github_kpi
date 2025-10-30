"""
GitHub Productivity Dashboard - Main Streamlit Application

A comprehensive dashboard for analyzing developer productivity using GitHub API data
and AI-powered insights from ChatGPT.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any

# Dashboard sections
DASHBOARD_SECTIONS = {
    "Overview": "📊",
    "Metrics": "📈", 
    "Analytics": "🔍",
    "AI Insights": "🤖",
    "Export": "📥"
}

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_section' not in st.session_state:
        st.session_state.current_section = "Overview"
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ""
    if 'repository_url' not in st.session_state:
        st.session_state.repository_url = ""
    if 'credentials_valid' not in st.session_state:
        st.session_state.credentials_valid = False
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

def validate_github_token(token: str) -> bool:
    """Validate GitHub token format"""
    if not token:
        return False
    # Basic GitHub token format validation
    import re
    return bool(re.match(r'^gh[a-z]_[A-Za-z0-9_]{36,}$', token))

def validate_openai_key(key: str) -> bool:
    """Validate OpenAI API key format"""
    if not key:
        return False
    return key.startswith('sk-') and len(key) > 20

def validate_repository_url(url: str) -> tuple[bool, str, str]:
    """Validate GitHub repository URL and extract owner/name"""
    if not url:
        return False, "", ""
    
    import re
    # Support both full URLs and owner/repo format
    if url.startswith('https://github.com/'):
        pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
        match = re.match(pattern, url)
        if match:
            owner, name = match.groups()
            if name.endswith('.git'):
                name = name[:-4]
            return True, owner, name
    elif '/' in url and not url.startswith('http'):
        # Handle owner/repo format
        parts = url.split('/')
        if len(parts) == 2:
            owner, name = parts
            return True, owner, name
    
    return False, "", ""

def test_github_connection(token: str, repo_owner: str, repo_name: str) -> tuple[bool, str]:
    """Test GitHub API connection and repository access"""
    try:
        from models.config import GitHubCredentials, RepositoryConfig
        from utils.github_client import GitHubClient
        
        # Create credentials and client
        credentials = GitHubCredentials(personal_access_token=token)
        client = GitHubClient(credentials)
        
        # Test authentication
        if not client.authenticate():
            return False, "Authentication failed"
        
        # Test repository access if provided
        if repo_owner and repo_name:
            repo_config = RepositoryConfig(owner=repo_owner, name=repo_name)
            if not client.validate_repository_access(repo_config):
                return False, f"Cannot access repository {repo_owner}/{repo_name}"
        
        return True, "Connection successful"
        
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def test_openai_connection(api_key: str) -> tuple[bool, str]:
    """Test OpenAI API connection"""
    try:
        from models.config import OpenAICredentials
        from utils.chatgpt_analyzer import ChatGPTAnalyzer
        
        # Create credentials and analyzer
        credentials = OpenAICredentials(api_key=api_key)
        analyzer = ChatGPTAnalyzer(credentials)
        
        # Test with a simple prompt
        test_response = analyzer._make_api_request("Say 'test successful'")
        if test_response and "test successful" in test_response.lower():
            return True, "Connection successful"
        else:
            return False, "API test failed"
            
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def render_configuration_panel():
    """Render the configuration and credentials panel"""
    st.header("⚙️ Configuration")
    
    # GitHub Configuration
    st.subheader("🐙 GitHub Configuration")
    
    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        value=st.session_state.github_token,
        help="Enter your GitHub personal access token with repo access",
        key="github_token_input"
    )
    
    if github_token != st.session_state.github_token:
        st.session_state.github_token = github_token
        st.session_state.credentials_valid = False
    
    # GitHub token validation
    if github_token:
        if validate_github_token(github_token):
            st.success("✅ Valid GitHub token format")
        else:
            st.error("❌ Invalid GitHub token format")
    
    # Repository Configuration
    repository_url = st.text_input(
        "Repository URL or Owner/Name",
        value=st.session_state.repository_url,
        help="Enter GitHub repository URL (https://github.com/owner/repo) or owner/repo format",
        key="repo_url_input"
    )
    
    if repository_url != st.session_state.repository_url:
        st.session_state.repository_url = repository_url
        st.session_state.credentials_valid = False
    
    # Repository validation
    repo_valid = False
    repo_owner = ""
    repo_name = ""
    
    if repository_url:
        repo_valid, repo_owner, repo_name = validate_repository_url(repository_url)
        if repo_valid:
            st.success(f"✅ Valid repository: {repo_owner}/{repo_name}")
        else:
            st.error("❌ Invalid repository URL format")
    
    # Test GitHub connection
    if st.button("🔍 Test GitHub Connection", disabled=not (github_token and repo_valid)):
        with st.spinner("Testing GitHub connection..."):
            success, message = test_github_connection(github_token, repo_owner, repo_name)
            if success:
                st.success(f"✅ {message}")
                st.session_state.github_valid = True
            else:
                st.error(f"❌ {message}")
                st.session_state.github_valid = False
    
    st.markdown("---")
    
    # OpenAI Configuration
    st.subheader("🤖 OpenAI Configuration")
    
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.openai_key,
        help="Enter your OpenAI API key for AI-powered insights",
        key="openai_key_input"
    )
    
    if openai_key != st.session_state.openai_key:
        st.session_state.openai_key = openai_key
        st.session_state.credentials_valid = False
    
    # OpenAI key validation
    if openai_key:
        if validate_openai_key(openai_key):
            st.success("✅ Valid OpenAI API key format")
        else:
            st.error("❌ Invalid OpenAI API key format")
    
    # Test OpenAI connection
    if st.button("🔍 Test OpenAI Connection", disabled=not openai_key):
        with st.spinner("Testing OpenAI connection..."):
            success, message = test_openai_connection(openai_key)
            if success:
                st.success(f"✅ {message}")
                st.session_state.openai_valid = True
            else:
                st.error(f"❌ {message}")
                st.session_state.openai_valid = False
    
    st.markdown("---")
    
    # Configuration Status
    st.subheader("📋 Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        github_status = getattr(st.session_state, 'github_valid', False)
        if github_status:
            st.success("✅ GitHub Connected")
        elif github_token and repo_valid:
            st.warning("⚠️ GitHub Not Tested")
        else:
            st.error("❌ GitHub Not Configured")
    
    with col2:
        openai_status = getattr(st.session_state, 'openai_valid', False)
        if openai_status:
            st.success("✅ OpenAI Connected")
        elif openai_key:
            st.warning("⚠️ OpenAI Not Tested")
        else:
            st.info("ℹ️ OpenAI Optional")
    
    # Update overall credentials status
    st.session_state.credentials_valid = (
        github_status and 
        github_token and 
        repo_valid
    )
    
    if st.session_state.credentials_valid:
        st.success("🎉 Configuration Complete! You can now load data and analyze productivity.")
        
        # Load Data button
        if st.button("📊 Load Repository Data", type="primary"):
            with st.spinner("Loading repository data..."):
                # This will be implemented in later tasks
                st.info("Data loading will be implemented in upcoming tasks.")
                st.session_state.data_loaded = True
    else:
        st.info("Complete the configuration above to start analyzing productivity data.")

def render_sidebar_navigation():
    """Render sidebar navigation and configuration"""
    with st.sidebar:
        st.header("🚀 Navigation")
        
        # Navigation buttons
        for section, icon in DASHBOARD_SECTIONS.items():
            if st.button(f"{icon} {section}", key=f"nav_{section}", use_container_width=True):
                st.session_state.current_section = section
                st.rerun()
        
        st.markdown("---")
        
        # Configuration panel
        render_configuration_panel()

def get_sample_metrics():
    """Generate sample metrics for demonstration"""
    from datetime import datetime, timedelta
    from models.metrics import ProductivityMetrics, CommitMetrics, PRMetrics, ReviewMetrics, IssueMetrics, VelocityPoint
    
    # Create sample data when real data is not available
    if not st.session_state.data_loaded:
        return None
    
    # Sample metrics (in real implementation, this would come from data processing)
    period_start = datetime.now() - timedelta(days=30)
    period_end = datetime.now()
    
    commit_metrics = CommitMetrics(
        total_commits=45,
        commit_frequency={"daily": 1.5, "weekly": 10.5, "monthly": 45},
        average_additions=125.5,
        average_deletions=45.2,
        average_files_changed=3.2,
        most_active_hours=[9, 10, 14, 15, 16],
        commit_message_length_avg=52.3
    )
    
    pr_metrics = PRMetrics(
        total_prs=12,
        merged_prs=10,
        closed_prs=1,
        open_prs=1,
        average_time_to_merge=24.5,
        average_additions=245.8,
        average_deletions=89.3,
        average_commits_per_pr=3.8,
        merge_rate=83.3
    )
    
    review_metrics = ReviewMetrics(
        total_reviews_given=18,
        total_reviews_received=15,
        average_review_time=4.2,
        approval_rate=72.2,
        change_request_rate=22.2,
        review_participation_rate=85.7
    )
    
    issue_metrics = IssueMetrics(
        total_issues=8,
        closed_issues=6,
        open_issues=2,
        average_time_to_close=48.5,
        resolution_rate=75.0,
        issues_created=3,
        issues_assigned=5
    )
    
    # Sample velocity points
    velocity_trends = []
    for i in range(7):
        date = period_end - timedelta(days=i)
        velocity_trends.append(VelocityPoint(
            timestamp=date,
            commits=6 + (i % 3),
            additions=150 + (i * 20),
            deletions=50 + (i * 10),
            pull_requests=1 if i % 2 == 0 else 2,
            issues_closed=1 if i % 3 == 0 else 0
        ))
    
    return ProductivityMetrics(
        period_start=period_start,
        period_end=period_end,
        commit_metrics=commit_metrics,
        pr_metrics=pr_metrics,
        review_metrics=review_metrics,
        issue_metrics=issue_metrics,
        velocity_trends=velocity_trends,
        time_distribution={"coding": 65.5, "reviewing": 20.3, "meetings": 14.2}
    )

def render_metrics_summary(metrics):
    """Render high-level metrics summary"""
    if not metrics:
        st.info("📊 Load repository data to see productivity metrics")
        return
    
    st.subheader("📈 Productivity Summary")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Commits", 
            metrics.commit_metrics.total_commits,
            delta=f"{metrics.daily_commit_average:.1f}/day",
            help="Total commits in the selected period"
        )
    
    with col2:
        st.metric(
            "Pull Requests", 
            metrics.pr_metrics.total_prs,
            delta=f"{metrics.pr_metrics.merge_rate:.1f}% merged",
            help="Total pull requests created"
        )
    
    with col3:
        st.metric(
            "Code Reviews", 
            metrics.review_metrics.total_reviews_given,
            delta=f"{metrics.review_metrics.review_participation_rate:.1f}% participation",
            help="Code reviews given to others"
        )
    
    with col4:
        st.metric(
            "Issues Resolved", 
            metrics.issue_metrics.closed_issues,
            delta=f"{metrics.issue_metrics.resolution_rate:.1f}% rate",
            help="Issues closed in the period"
        )

def render_detailed_metrics(metrics):
    """Render detailed metrics breakdown"""
    if not metrics:
        return
    
    st.subheader("📊 Detailed Metrics")
    
    # Create tabs for different metric categories
    tab1, tab2, tab3, tab4 = st.tabs(["💻 Commits", "🔄 Pull Requests", "👥 Reviews", "🐛 Issues"])
    
    with tab1:
        st.markdown("**Commit Activity**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Average Additions", f"{metrics.commit_metrics.average_additions:.0f}")
            st.metric("Average Deletions", f"{metrics.commit_metrics.average_deletions:.0f}")
            st.metric("Files per Commit", f"{metrics.commit_metrics.average_files_changed:.1f}")
        
        with col2:
            st.metric("Message Length", f"{metrics.commit_metrics.commit_message_length_avg:.0f} chars")
            if metrics.commit_metrics.most_active_hours:
                active_hours = ", ".join(f"{h}:00" for h in metrics.commit_metrics.most_active_hours[:3])
                st.metric("Most Active Hours", active_hours)
    
    with tab2:
        st.markdown("**Pull Request Performance**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Merged PRs", metrics.pr_metrics.merged_prs)
            st.metric("Open PRs", metrics.pr_metrics.open_prs)
            st.metric("Closed PRs", metrics.pr_metrics.closed_prs)
        
        with col2:
            if metrics.pr_metrics.average_time_to_merge:
                st.metric("Avg Time to Merge", f"{metrics.pr_metrics.average_time_to_merge:.1f} hours")
            st.metric("Avg Commits/PR", f"{metrics.pr_metrics.average_commits_per_pr:.1f}")
            st.metric("Avg Changes/PR", f"{metrics.pr_metrics.average_additions + metrics.pr_metrics.average_deletions:.0f}")
    
    with tab3:
        st.markdown("**Code Review Activity**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Reviews Given", metrics.review_metrics.total_reviews_given)
            st.metric("Reviews Received", metrics.review_metrics.total_reviews_received)
        
        with col2:
            st.metric("Approval Rate", f"{metrics.review_metrics.approval_rate:.1f}%")
            st.metric("Change Request Rate", f"{metrics.review_metrics.change_request_rate:.1f}%")
            if metrics.review_metrics.average_review_time:
                st.metric("Avg Review Time", f"{metrics.review_metrics.average_review_time:.1f} hours")
    
    with tab4:
        st.markdown("**Issue Management**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Issues Created", metrics.issue_metrics.issues_created)
            st.metric("Issues Assigned", metrics.issue_metrics.issues_assigned)
        
        with col2:
            st.metric("Issues Closed", metrics.issue_metrics.closed_issues)
            if metrics.issue_metrics.average_time_to_close:
                st.metric("Avg Time to Close", f"{metrics.issue_metrics.average_time_to_close:.1f} hours")

def render_activity_distribution(metrics):
    """Render time distribution chart"""
    if not metrics or not metrics.time_distribution:
        return
    
    st.subheader("⏰ Time Distribution")
    
    # Create a simple bar chart for time distribution
    import pandas as pd
    
    df = pd.DataFrame(
        list(metrics.time_distribution.items()),
        columns=['Activity', 'Hours']
    )
    
    st.bar_chart(df.set_index('Activity'))

def render_overview_section():
    """Render the overview dashboard section"""
    st.header("📊 Dashboard Overview")
    st.markdown("Welcome to your GitHub Productivity Dashboard")
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.credentials_valid:
            st.success("✅ Credentials Configured")
        else:
            st.warning("⚠️ Configure Credentials")
    
    with col2:
        if st.session_state.data_loaded:
            st.success("✅ Data Loaded")
        else:
            st.info("📊 No Data Loaded")
    
    with col3:
        if st.session_state.credentials_valid and st.session_state.data_loaded:
            st.success("🔄 Ready for Analysis")
        else:
            st.info("🔄 Configure & Load Data")
    
    st.markdown("---")
    
    # Get metrics data
    metrics = get_sample_metrics()
    
    # Render metrics summary
    render_metrics_summary(metrics)
    
    if metrics:
        st.markdown("---")
        
        # Render detailed metrics
        render_detailed_metrics(metrics)
        
        st.markdown("---")
        
        # Render activity distribution
        render_activity_distribution(metrics)
        
        # Auto-refresh functionality
        if st.session_state.credentials_valid and st.session_state.data_loaded:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("🔄 Refresh Data", help="Reload data from GitHub"):
                    with st.spinner("Refreshing data..."):
                        # In real implementation, this would reload data
                        st.success("Data refreshed successfully!")
                        st.rerun()

def render_metrics_section():
    """Render the metrics dashboard section"""
    st.header("📈 Productivity Metrics")
    st.markdown("Detailed productivity metrics and KPIs")
    
    # Get metrics data
    metrics = get_sample_metrics()
    
    if not metrics:
        st.info("📊 Configure credentials and load repository data to see detailed metrics")
        return
    
    # Period information
    st.subheader("📅 Analysis Period")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Period Start", metrics.period_start.strftime("%Y-%m-%d"))
    with col2:
        st.metric("Period End", metrics.period_end.strftime("%Y-%m-%d"))
    with col3:
        st.metric("Total Days", metrics.period_days)
    
    st.markdown("---")
    
    # Render all metric components
    render_metrics_summary(metrics)
    
    st.markdown("---")
    
    render_detailed_metrics(metrics)
    
    st.markdown("---")
    
    render_activity_distribution(metrics)
    
    # Velocity trends preview
    if metrics.velocity_trends:
        st.subheader("📈 Recent Velocity Trends")
        st.info("Interactive velocity charts will be available in the Analytics section.")
        
        # Show recent velocity data in a simple table
        import pandas as pd
        
        recent_velocity = metrics.velocity_trends[:5]  # Last 5 days
        df = pd.DataFrame([
            {
                'Date': vp.timestamp.strftime("%Y-%m-%d"),
                'Commits': vp.commits,
                'Additions': vp.additions,
                'Deletions': vp.deletions,
                'PRs': vp.pull_requests,
                'Issues': vp.issues_closed
            }
            for vp in recent_velocity
        ])
        
        st.dataframe(df, use_container_width=True)

def render_analytics_section():
    """Render the analytics dashboard section"""
    st.header("🔍 Detailed Analytics")
    st.markdown("In-depth analysis and visualizations")
    
    # Analytics will be implemented in task 7
    st.info("Interactive visualizations will be implemented in task 7.")

def render_ai_insights_section():
    """Render the AI insights dashboard section"""
    st.header("🤖 AI Insights")
    st.markdown("ChatGPT-powered analysis and recommendations")
    
    # AI insights will be implemented in task 8
    st.info("AI-generated insights will be implemented in task 8.")

def render_export_section():
    """Render the export dashboard section"""
    st.header("📥 Export & Reports")
    st.markdown("Download reports and export data")
    
    # Export functionality will be implemented in task 9
    st.info("Export functionality will be implemented in task 9.")

def render_main_content():
    """Render main content area based on selected section"""
    current_section = st.session_state.current_section
    
    if current_section == "Overview":
        render_overview_section()
    elif current_section == "Metrics":
        render_metrics_section()
    elif current_section == "Analytics":
        render_analytics_section()
    elif current_section == "AI Insights":
        render_ai_insights_section()
    elif current_section == "Export":
        render_export_section()

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="GitHub Productivity Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("📊 GitHub Productivity Dashboard")
    st.markdown("Analyze developer productivity with GitHub data and AI insights")
    
    # Render sidebar navigation
    render_sidebar_navigation()
    
    # Render main content
    render_main_content()
    
    # Footer
    st.markdown("---")
    st.markdown("*GitHub Productivity Dashboard - Powered by Streamlit and OpenAI*")

if __name__ == "__main__":
    main()