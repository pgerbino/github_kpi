"""
Interactive visualization components for GitHub Productivity Dashboard.

This module contains Plotly-based interactive charts and visualizations
for displaying productivity metrics and trends.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from models.metrics import ProductivityMetrics, VelocityPoint


def create_commit_frequency_chart(metrics: ProductivityMetrics, 
                                 date_range: Optional[tuple] = None,
                                 developer_filter: Optional[str] = None) -> go.Figure:
    """
    Create interactive time-series chart for commit frequency trends.
    
    Args:
        metrics: ProductivityMetrics containing velocity trends
        date_range: Optional tuple of (start_date, end_date) for filtering
        developer_filter: Optional developer name for filtering (not implemented yet)
    
    Returns:
        Plotly figure object
    """
    if not metrics.velocity_trends:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No velocity data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Commit Frequency Trends",
            xaxis_title="Date",
            yaxis_title="Commits per Day"
        )
        return fig
    
    # Filter data by date range if provided
    velocity_data = metrics.velocity_trends
    if date_range:
        start_date, end_date = date_range
        velocity_data = [
            vp for vp in velocity_data 
            if start_date <= vp.timestamp.date() <= end_date
        ]
    
    # Sort by timestamp
    velocity_data = sorted(velocity_data, key=lambda x: x.timestamp)
    
    # Extract data for plotting
    dates = [vp.timestamp for vp in velocity_data]
    commits = [vp.commits for vp in velocity_data]
    
    # Create the figure
    fig = go.Figure()
    
    # Add commit frequency line
    fig.add_trace(go.Scatter(
        x=dates,
        y=commits,
        mode='lines+markers',
        name='Daily Commits',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6, color='#1f77b4'),
        hovertemplate='<b>%{x}</b><br>Commits: %{y}<extra></extra>'
    ))
    
    # Add trend line if we have enough data points
    if len(velocity_data) > 2:
        # Calculate simple moving average (7-day window)
        window_size = min(7, len(commits))
        if window_size > 1:
            moving_avg = []
            for i in range(len(commits)):
                start_idx = max(0, i - window_size + 1)
                avg = sum(commits[start_idx:i+1]) / (i - start_idx + 1)
                moving_avg.append(avg)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=moving_avg,
                mode='lines',
                name=f'{window_size}-Day Average',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='<b>%{x}</b><br>Average: %{y:.1f}<extra></extra>'
            ))
    
    # Update layout
    fig.update_layout(
        title="Commit Frequency Trends",
        xaxis_title="Date",
        yaxis_title="Commits per Day",
        hovermode='x unified',
        showlegend=True,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # Update x-axis to show dates nicely
    fig.update_xaxes(
        tickformat='%Y-%m-%d',
        tickangle=45
    )
    
    return fig


def create_code_volume_chart(metrics: ProductivityMetrics,
                           date_range: Optional[tuple] = None,
                           developer_filter: Optional[str] = None) -> go.Figure:
    """
    Create interactive time-series chart for code volume trends (additions/deletions).
    
    Args:
        metrics: ProductivityMetrics containing velocity trends
        date_range: Optional tuple of (start_date, end_date) for filtering
        developer_filter: Optional developer name for filtering (not implemented yet)
    
    Returns:
        Plotly figure object
    """
    if not metrics.velocity_trends:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No velocity data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Code Volume Trends",
            xaxis_title="Date",
            yaxis_title="Lines of Code"
        )
        return fig
    
    # Filter data by date range if provided
    velocity_data = metrics.velocity_trends
    if date_range:
        start_date, end_date = date_range
        velocity_data = [
            vp for vp in velocity_data 
            if start_date <= vp.timestamp.date() <= end_date
        ]
    
    # Sort by timestamp
    velocity_data = sorted(velocity_data, key=lambda x: x.timestamp)
    
    # Extract data for plotting
    dates = [vp.timestamp for vp in velocity_data]
    additions = [vp.additions for vp in velocity_data]
    deletions = [vp.deletions for vp in velocity_data]
    net_changes = [vp.additions - vp.deletions for vp in velocity_data]
    
    # Create the figure
    fig = go.Figure()
    
    # Add additions line
    fig.add_trace(go.Scatter(
        x=dates,
        y=additions,
        mode='lines+markers',
        name='Lines Added',
        line=dict(color='#2ca02c', width=2),
        marker=dict(size=4, color='#2ca02c'),
        hovertemplate='<b>%{x}</b><br>Added: %{y}<extra></extra>'
    ))
    
    # Add deletions line
    fig.add_trace(go.Scatter(
        x=dates,
        y=deletions,
        mode='lines+markers',
        name='Lines Deleted',
        line=dict(color='#d62728', width=2),
        marker=dict(size=4, color='#d62728'),
        hovertemplate='<b>%{x}</b><br>Deleted: %{y}<extra></extra>'
    ))
    
    # Add net changes line
    fig.add_trace(go.Scatter(
        x=dates,
        y=net_changes,
        mode='lines+markers',
        name='Net Changes',
        line=dict(color='#1f77b4', width=2, dash='dot'),
        marker=dict(size=4, color='#1f77b4'),
        hovertemplate='<b>%{x}</b><br>Net: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Code Volume Trends",
        xaxis_title="Date",
        yaxis_title="Lines of Code",
        hovermode='x unified',
        showlegend=True,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # Update x-axis to show dates nicely
    fig.update_xaxes(
        tickformat='%Y-%m-%d',
        tickangle=45
    )
    
    return fig


def create_velocity_overview_chart(metrics: ProductivityMetrics,
                                 date_range: Optional[tuple] = None) -> go.Figure:
    """
    Create multi-metric velocity overview chart with subplots.
    
    Args:
        metrics: ProductivityMetrics containing velocity trends
        date_range: Optional tuple of (start_date, end_date) for filtering
    
    Returns:
        Plotly figure object with subplots
    """
    if not metrics.velocity_trends:
        # Create empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="No velocity data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Velocity Overview")
        return fig
    
    # Filter data by date range if provided
    velocity_data = metrics.velocity_trends
    if date_range:
        start_date, end_date = date_range
        velocity_data = [
            vp for vp in velocity_data 
            if start_date <= vp.timestamp.date() <= end_date
        ]
    
    # Sort by timestamp
    velocity_data = sorted(velocity_data, key=lambda x: x.timestamp)
    
    # Extract data for plotting
    dates = [vp.timestamp for vp in velocity_data]
    commits = [vp.commits for vp in velocity_data]
    prs = [vp.pull_requests for vp in velocity_data]
    issues = [vp.issues_closed for vp in velocity_data]
    total_changes = [vp.total_changes for vp in velocity_data]
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Commits', 'Pull Requests', 'Issues Closed', 'Code Changes'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Add commits subplot
    fig.add_trace(
        go.Scatter(x=dates, y=commits, mode='lines+markers', name='Commits',
                  line=dict(color='#1f77b4'), marker=dict(size=4)),
        row=1, col=1
    )
    
    # Add PRs subplot
    fig.add_trace(
        go.Scatter(x=dates, y=prs, mode='lines+markers', name='Pull Requests',
                  line=dict(color='#ff7f0e'), marker=dict(size=4)),
        row=1, col=2
    )
    
    # Add issues subplot
    fig.add_trace(
        go.Scatter(x=dates, y=issues, mode='lines+markers', name='Issues Closed',
                  line=dict(color='#2ca02c'), marker=dict(size=4)),
        row=2, col=1
    )
    
    # Add code changes subplot
    fig.add_trace(
        go.Scatter(x=dates, y=total_changes, mode='lines+markers', name='Total Changes',
                  line=dict(color='#d62728'), marker=dict(size=4)),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title="Velocity Overview - Multiple Metrics",
        height=500,
        showlegend=False,
        margin=dict(l=0, r=0, t=60, b=0)
    )
    
    # Update all x-axes
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(tickformat='%m-%d', tickangle=45, row=i, col=j)
    
    return fig


def render_time_series_section(metrics: ProductivityMetrics):
    """
    Render the time-series charts section with filtering options.
    
    Args:
        metrics: ProductivityMetrics to visualize
    """
    st.subheader("📈 Time-Series Analysis")
    
    if not metrics:
        st.info("📊 Load repository data to see time-series analysis")
        return
    
    # Date range filtering
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Calculate default date range (last 30 days or available data range)
        if metrics.velocity_trends:
            min_date = min(vp.timestamp.date() for vp in metrics.velocity_trends)
            max_date = max(vp.timestamp.date() for vp in metrics.velocity_trends)
            default_start = max(min_date, max_date - timedelta(days=30))
        else:
            default_start = metrics.period_start.date()
            max_date = metrics.period_end.date()
        
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=metrics.period_start.date(),
            max_value=metrics.period_end.date(),
            key="ts_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=metrics.period_start.date(),
            max_value=metrics.period_end.date(),
            key="ts_end_date"
        )
    
    with col3:
        # Developer filter (placeholder for future implementation)
        developer_filter = st.selectbox(
            "Developer",
            options=["All Developers"],
            index=0,
            key="ts_developer_filter",
            help="Developer filtering will be implemented in future updates"
        )
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    date_range = (start_date, end_date)
    dev_filter = None if developer_filter == "All Developers" else developer_filter
    
    # Create tabs for different chart types
    tab1, tab2, tab3 = st.tabs(["📊 Commit Frequency", "📝 Code Volume", "🔄 Velocity Overview"])
    
    with tab1:
        st.markdown("**Daily commit frequency with trend analysis**")
        
        # Create and display commit frequency chart
        commit_chart = create_commit_frequency_chart(metrics, date_range, dev_filter)
        st.plotly_chart(commit_chart, use_container_width=True)
        
        # Show summary statistics
        if metrics.velocity_trends:
            filtered_data = [
                vp for vp in metrics.velocity_trends 
                if start_date <= vp.timestamp.date() <= end_date
            ]
            
            if filtered_data:
                total_commits = sum(vp.commits for vp in filtered_data)
                avg_commits = total_commits / len(filtered_data) if filtered_data else 0
                max_commits = max(vp.commits for vp in filtered_data)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Commits", total_commits)
                with col2:
                    st.metric("Daily Average", f"{avg_commits:.1f}")
                with col3:
                    st.metric("Peak Day", max_commits)
    
    with tab2:
        st.markdown("**Code additions, deletions, and net changes over time**")
        
        # Create and display code volume chart
        volume_chart = create_code_volume_chart(metrics, date_range, dev_filter)
        st.plotly_chart(volume_chart, use_container_width=True)
        
        # Show summary statistics
        if metrics.velocity_trends:
            filtered_data = [
                vp for vp in metrics.velocity_trends 
                if start_date <= vp.timestamp.date() <= end_date
            ]
            
            if filtered_data:
                total_additions = sum(vp.additions for vp in filtered_data)
                total_deletions = sum(vp.deletions for vp in filtered_data)
                net_changes = total_additions - total_deletions
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Additions", total_additions, delta=f"+{total_additions}")
                with col2:
                    st.metric("Total Deletions", total_deletions, delta=f"-{total_deletions}")
                with col3:
                    st.metric("Net Changes", net_changes, delta=f"{'+' if net_changes >= 0 else ''}{net_changes}")
    
    with tab3:
        st.markdown("**Multi-metric velocity overview**")
        
        # Create and display velocity overview chart
        velocity_chart = create_velocity_overview_chart(metrics, date_range)
        st.plotly_chart(velocity_chart, use_container_width=True)
        
        # Show period summary
        if metrics.velocity_trends:
            filtered_data = [
                vp for vp in metrics.velocity_trends 
                if start_date <= vp.timestamp.date() <= end_date
            ]
            
            if filtered_data:
                st.markdown("**Period Summary**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_commits = sum(vp.commits for vp in filtered_data)
                    st.metric("Commits", total_commits)
                
                with col2:
                    total_prs = sum(vp.pull_requests for vp in filtered_data)
                    st.metric("Pull Requests", total_prs)
                
                with col3:
                    total_issues = sum(vp.issues_closed for vp in filtered_data)
                    st.metric("Issues Closed", total_issues)
                
                with col4:
                    total_changes = sum(vp.total_changes for vp in filtered_data)
                    st.metric("Code Changes", total_changes)

def create_pr_metrics_chart(metrics: ProductivityMetrics,
                           date_range: Optional[tuple] = None,
                           repository_filter: Optional[str] = None) -> go.Figure:
    """
    Create detailed pull request metrics chart.
    
    Args:
        metrics: ProductivityMetrics containing PR data
        date_range: Optional tuple of (start_date, end_date) for filtering
        repository_filter: Optional repository name for filtering
    
    Returns:
        Plotly figure object
    """
    pr_metrics = metrics.pr_metrics
    
    # Create pie chart for PR status distribution
    labels = []
    values = []
    colors = []
    
    if pr_metrics.merged_prs > 0:
        labels.append(f'Merged ({pr_metrics.merged_prs})')
        values.append(pr_metrics.merged_prs)
        colors.append('#2ca02c')
    
    if pr_metrics.open_prs > 0:
        labels.append(f'Open ({pr_metrics.open_prs})')
        values.append(pr_metrics.open_prs)
        colors.append('#1f77b4')
    
    if pr_metrics.closed_prs > 0:
        labels.append(f'Closed ({pr_metrics.closed_prs})')
        values.append(pr_metrics.closed_prs)
        colors.append('#d62728')
    
    if not values:
        # Create empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No pull request data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Pull Request Status Distribution")
        return fig
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Pull Request Status Distribution",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=True
    )
    
    return fig


def create_pr_performance_chart(metrics: ProductivityMetrics) -> go.Figure:
    """
    Create pull request performance metrics chart.
    
    Args:
        metrics: ProductivityMetrics containing PR data
    
    Returns:
        Plotly figure object
    """
    pr_metrics = metrics.pr_metrics
    
    # Create bar chart for PR performance metrics
    categories = ['Avg Time to Merge (hrs)', 'Avg Commits per PR', 'Avg Lines per PR', 'Merge Rate (%)']
    values = [
        pr_metrics.average_time_to_merge or 0,
        pr_metrics.average_commits_per_pr,
        pr_metrics.average_additions + pr_metrics.average_deletions,
        pr_metrics.merge_rate
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.1f}' for v in values],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Pull Request Performance Metrics",
        xaxis_title="Metrics",
        yaxis_title="Value",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_review_participation_chart(metrics: ProductivityMetrics) -> go.Figure:
    """
    Create code review participation chart.
    
    Args:
        metrics: ProductivityMetrics containing review data
    
    Returns:
        Plotly figure object
    """
    review_metrics = metrics.review_metrics
    
    # Create grouped bar chart for review activity
    categories = ['Reviews Given', 'Reviews Received']
    values = [review_metrics.total_reviews_given, review_metrics.total_reviews_received]
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=['#1f77b4', '#ff7f0e'],
            text=values,
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Code Review Participation",
        xaxis_title="Review Type",
        yaxis_title="Count",
        height=300,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_review_quality_chart(metrics: ProductivityMetrics) -> go.Figure:
    """
    Create code review quality metrics chart.
    
    Args:
        metrics: ProductivityMetrics containing review data
    
    Returns:
        Plotly figure object
    """
    review_metrics = metrics.review_metrics
    
    # Create stacked bar chart for review outcomes
    categories = ['Review Outcomes']
    approval_rate = review_metrics.approval_rate
    change_request_rate = review_metrics.change_request_rate
    other_rate = 100 - approval_rate - change_request_rate
    
    fig = go.Figure(data=[
        go.Bar(
            name='Approved',
            x=categories,
            y=[approval_rate],
            marker_color='#2ca02c',
            hovertemplate='<b>Approved</b><br>Rate: %{y:.1f}%<extra></extra>'
        ),
        go.Bar(
            name='Changes Requested',
            x=categories,
            y=[change_request_rate],
            marker_color='#ff7f0e',
            hovertemplate='<b>Changes Requested</b><br>Rate: %{y:.1f}%<extra></extra>'
        ),
        go.Bar(
            name='Other',
            x=categories,
            y=[other_rate],
            marker_color='#d62728',
            hovertemplate='<b>Other</b><br>Rate: %{y:.1f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Review Quality Distribution",
        xaxis_title="",
        yaxis_title="Percentage (%)",
        barmode='stack',
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=True
    )
    
    return fig


def create_issue_resolution_chart(metrics: ProductivityMetrics,
                                 date_range: Optional[tuple] = None) -> go.Figure:
    """
    Create issue resolution metrics chart.
    
    Args:
        metrics: ProductivityMetrics containing issue data
        date_range: Optional tuple of (start_date, end_date) for filtering
    
    Returns:
        Plotly figure object
    """
    issue_metrics = metrics.issue_metrics
    
    # Create donut chart for issue status
    labels = []
    values = []
    colors = []
    
    if issue_metrics.closed_issues > 0:
        labels.append(f'Closed ({issue_metrics.closed_issues})')
        values.append(issue_metrics.closed_issues)
        colors.append('#2ca02c')
    
    if issue_metrics.open_issues > 0:
        labels.append(f'Open ({issue_metrics.open_issues})')
        values.append(issue_metrics.open_issues)
        colors.append('#ff7f0e')
    
    if not values:
        # Create empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No issue data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(title="Issue Resolution Status")
        return fig
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.5,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    # Add center text showing resolution rate
    fig.add_annotation(
        text=f"{issue_metrics.resolution_rate:.1f}%<br>Resolution Rate",
        x=0.5, y=0.5,
        font_size=16,
        showarrow=False
    )
    
    fig.update_layout(
        title="Issue Resolution Status",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=True
    )
    
    return fig


def create_issue_performance_chart(metrics: ProductivityMetrics) -> go.Figure:
    """
    Create issue performance metrics chart.
    
    Args:
        metrics: ProductivityMetrics containing issue data
    
    Returns:
        Plotly figure object
    """
    issue_metrics = metrics.issue_metrics
    
    # Create bar chart for issue metrics
    categories = ['Issues Created', 'Issues Assigned', 'Issues Closed', 'Avg Time to Close (hrs)']
    values = [
        issue_metrics.issues_created,
        issue_metrics.issues_assigned,
        issue_metrics.closed_issues,
        issue_metrics.average_time_to_close or 0
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'{v:.0f}' if i < 3 else f'{v:.1f}' for i, v in enumerate(values)],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Issue Management Performance",
        xaxis_title="Metrics",
        yaxis_title="Value",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def render_detailed_analytics_section(metrics: ProductivityMetrics):
    """
    Render detailed analytics and drill-down views section.
    
    Args:
        metrics: ProductivityMetrics to visualize
    """
    st.subheader("🔍 Detailed Analytics")
    
    if not metrics:
        st.info("📊 Load repository data to see detailed analytics")
        return
    
    # Filtering options
    st.markdown("**Filters**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        start_date = st.date_input(
            "Start Date",
            value=metrics.period_start.date(),
            min_value=metrics.period_start.date(),
            max_value=metrics.period_end.date(),
            key="analytics_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=metrics.period_end.date(),
            min_value=metrics.period_start.date(),
            max_value=metrics.period_end.date(),
            key="analytics_end_date"
        )
    
    with col3:
        # Repository filter (placeholder)
        repository_filter = st.selectbox(
            "Repository",
            options=["All Repositories"],
            index=0,
            key="analytics_repo_filter",
            help="Repository filtering will be implemented in future updates"
        )
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date must be before end date")
        return
    
    date_range = (start_date, end_date)
    repo_filter = None if repository_filter == "All Repositories" else repository_filter
    
    st.markdown("---")
    
    # Create tabs for different analytics categories
    tab1, tab2, tab3 = st.tabs(["🔄 Pull Requests", "👥 Code Reviews", "🐛 Issues"])
    
    with tab1:
        st.markdown("**Pull Request Analytics and Performance**")
        
        # PR metrics in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            # PR status distribution
            pr_status_chart = create_pr_metrics_chart(metrics, date_range, repo_filter)
            st.plotly_chart(pr_status_chart, use_container_width=True)
        
        with col2:
            # PR performance metrics
            pr_performance_chart = create_pr_performance_chart(metrics)
            st.plotly_chart(pr_performance_chart, use_container_width=True)
        
        # PR summary statistics
        st.markdown("**Pull Request Summary**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total PRs",
                metrics.pr_metrics.total_prs,
                help="Total pull requests in the period"
            )
        
        with col2:
            st.metric(
                "Merge Rate",
                f"{metrics.pr_metrics.merge_rate:.1f}%",
                help="Percentage of PRs that were merged"
            )
        
        with col3:
            if metrics.pr_metrics.average_time_to_merge:
                st.metric(
                    "Avg Merge Time",
                    f"{metrics.pr_metrics.average_time_to_merge:.1f}h",
                    help="Average time from PR creation to merge"
                )
            else:
                st.metric("Avg Merge Time", "N/A")
        
        with col4:
            st.metric(
                "Avg Size",
                f"{metrics.pr_metrics.average_additions + metrics.pr_metrics.average_deletions:.0f}",
                help="Average lines changed per PR"
            )
    
    with tab2:
        st.markdown("**Code Review Analytics and Participation**")
        
        # Review metrics in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Review participation
            review_participation_chart = create_review_participation_chart(metrics)
            st.plotly_chart(review_participation_chart, use_container_width=True)
        
        with col2:
            # Review quality distribution
            review_quality_chart = create_review_quality_chart(metrics)
            st.plotly_chart(review_quality_chart, use_container_width=True)
        
        # Review summary statistics
        st.markdown("**Code Review Summary**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Reviews Given",
                metrics.review_metrics.total_reviews_given,
                help="Total reviews provided to others"
            )
        
        with col2:
            st.metric(
                "Reviews Received",
                metrics.review_metrics.total_reviews_received,
                help="Total reviews received on your PRs"
            )
        
        with col3:
            st.metric(
                "Participation Rate",
                f"{metrics.review_metrics.review_participation_rate:.1f}%",
                help="Percentage of PRs where you participated in reviews"
            )
        
        with col4:
            if metrics.review_metrics.average_review_time:
                st.metric(
                    "Avg Review Time",
                    f"{metrics.review_metrics.average_review_time:.1f}h",
                    help="Average time to complete a review"
                )
            else:
                st.metric("Avg Review Time", "N/A")
    
    with tab3:
        st.markdown("**Issue Resolution Analytics**")
        
        # Issue metrics in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Issue resolution status
            issue_resolution_chart = create_issue_resolution_chart(metrics, date_range)
            st.plotly_chart(issue_resolution_chart, use_container_width=True)
        
        with col2:
            # Issue performance metrics
            issue_performance_chart = create_issue_performance_chart(metrics)
            st.plotly_chart(issue_performance_chart, use_container_width=True)
        
        # Issue summary statistics
        st.markdown("**Issue Management Summary**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Issues",
                metrics.issue_metrics.total_issues,
                help="Total issues in the period"
            )
        
        with col2:
            st.metric(
                "Resolution Rate",
                f"{metrics.issue_metrics.resolution_rate:.1f}%",
                help="Percentage of issues that were resolved"
            )
        
        with col3:
            st.metric(
                "Issues Created",
                metrics.issue_metrics.issues_created,
                help="Issues you created"
            )
        
        with col4:
            if metrics.issue_metrics.average_time_to_close:
                st.metric(
                    "Avg Resolution Time",
                    f"{metrics.issue_metrics.average_time_to_close:.1f}h",
                    help="Average time to close an issue"
                )
            else:
                st.metric("Avg Resolution Time", "N/A")
    
    # Additional insights section
    st.markdown("---")
    st.subheader("📊 Key Insights")
    
    insights = []
    
    # Generate insights based on metrics
    if metrics.pr_metrics.merge_rate > 80:
        insights.append("🎉 Excellent PR merge rate - most pull requests are being successfully merged")
    elif metrics.pr_metrics.merge_rate < 50:
        insights.append("⚠️ Low PR merge rate - consider reviewing PR quality or approval processes")
    
    if metrics.review_metrics.review_participation_rate > 70:
        insights.append("👥 Strong code review participation - good collaboration practices")
    elif metrics.review_metrics.review_participation_rate < 30:
        insights.append("📝 Low review participation - consider encouraging more peer reviews")
    
    if metrics.issue_metrics.resolution_rate > 75:
        insights.append("🐛 Good issue resolution rate - effective bug tracking and fixing")
    elif metrics.issue_metrics.resolution_rate < 40:
        insights.append("🔧 Low issue resolution rate - may need to focus on closing open issues")
    
    if metrics.commit_metrics.total_commits > 0 and metrics.pr_metrics.total_prs > 0:
        commits_per_pr = metrics.commit_metrics.total_commits / metrics.pr_metrics.total_prs
        if commits_per_pr > 10:
            insights.append("📦 Large PRs detected - consider breaking down changes into smaller PRs")
        elif commits_per_pr < 2:
            insights.append("⚡ Small, focused PRs - good practice for code review and integration")
    
    if insights:
        for insight in insights:
            st.info(insight)
    else:
        st.info("📈 Load more data to generate personalized insights")