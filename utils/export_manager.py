"""
Export manager for GitHub Productivity Dashboard.

This module provides functionality to export productivity metrics and AI insights
in various formats including CSV, text files, and PDF reports.
"""

import csv
import json
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
import pandas as pd

from models.metrics import ProductivityMetrics, AnalysisReport
from models.config import GitHubCredentials, OpenAICredentials


class CSVExporter:
    """Handles CSV export functionality for productivity metrics."""
    
    def __init__(self):
        """Initialize CSV exporter."""
        pass
    
    def export_productivity_metrics(self, metrics: ProductivityMetrics, 
                                  include_config: bool = True) -> str:
        """
        Export productivity metrics to CSV format.
        
        Args:
            metrics: ProductivityMetrics to export
            include_config: Whether to include configuration details
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        
        # Write header with metadata
        if include_config:
            output.write("# GitHub Productivity Dashboard - Metrics Export\n")
            output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"# Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}\n")
            output.write(f"# Total Days: {metrics.period_days}\n")
            output.write("\n")
        
        # Export summary metrics
        output.write("## Summary Metrics\n")
        writer = csv.writer(output)
        
        # Write summary data
        summary_data = [
            ["Metric Category", "Metric Name", "Value", "Unit"],
            ["Period", "Start Date", metrics.period_start.strftime('%Y-%m-%d'), "date"],
            ["Period", "End Date", metrics.period_end.strftime('%Y-%m-%d'), "date"],
            ["Period", "Total Days", str(metrics.period_days), "days"],
            ["Commits", "Total Commits", str(metrics.commit_metrics.total_commits), "count"],
            ["Commits", "Daily Average", f"{metrics.daily_commit_average:.2f}", "commits/day"],
            ["Commits", "Average Additions", f"{metrics.commit_metrics.average_additions:.1f}", "lines"],
            ["Commits", "Average Deletions", f"{metrics.commit_metrics.average_deletions:.1f}", "lines"],
            ["Commits", "Average Files Changed", f"{metrics.commit_metrics.average_files_changed:.1f}", "files"],
            ["Commits", "Average Message Length", f"{metrics.commit_metrics.commit_message_length_avg:.1f}", "characters"],
            ["Pull Requests", "Total PRs", str(metrics.pr_metrics.total_prs), "count"],
            ["Pull Requests", "Merged PRs", str(metrics.pr_metrics.merged_prs), "count"],
            ["Pull Requests", "Open PRs", str(metrics.pr_metrics.open_prs), "count"],
            ["Pull Requests", "Closed PRs", str(metrics.pr_metrics.closed_prs), "count"],
            ["Pull Requests", "Merge Rate", f"{metrics.pr_metrics.merge_rate:.1f}", "percentage"],
            ["Pull Requests", "Average Additions", f"{metrics.pr_metrics.average_additions:.1f}", "lines"],
            ["Pull Requests", "Average Deletions", f"{metrics.pr_metrics.average_deletions:.1f}", "lines"],
            ["Pull Requests", "Average Commits per PR", f"{metrics.pr_metrics.average_commits_per_pr:.1f}", "commits"],
            ["Code Reviews", "Reviews Given", str(metrics.review_metrics.total_reviews_given), "count"],
            ["Code Reviews", "Reviews Received", str(metrics.review_metrics.total_reviews_received), "count"],
            ["Code Reviews", "Approval Rate", f"{metrics.review_metrics.approval_rate:.1f}", "percentage"],
            ["Code Reviews", "Change Request Rate", f"{metrics.review_metrics.change_request_rate:.1f}", "percentage"],
            ["Code Reviews", "Participation Rate", f"{metrics.review_metrics.review_participation_rate:.1f}", "percentage"],
            ["Issues", "Total Issues", str(metrics.issue_metrics.total_issues), "count"],
            ["Issues", "Closed Issues", str(metrics.issue_metrics.closed_issues), "count"],
            ["Issues", "Open Issues", str(metrics.issue_metrics.open_issues), "count"],
            ["Issues", "Resolution Rate", f"{metrics.issue_metrics.resolution_rate:.1f}", "percentage"],
            ["Issues", "Issues Created", str(metrics.issue_metrics.issues_created), "count"],
            ["Issues", "Issues Assigned", str(metrics.issue_metrics.issues_assigned), "count"],
        ]
        
        # Add time-based metrics if available
        if metrics.pr_metrics.average_time_to_merge:
            summary_data.append(["Pull Requests", "Average Time to Merge", f"{metrics.pr_metrics.average_time_to_merge:.1f}", "hours"])
        
        if metrics.review_metrics.average_review_time:
            summary_data.append(["Code Reviews", "Average Review Time", f"{metrics.review_metrics.average_review_time:.1f}", "hours"])
        
        if metrics.issue_metrics.average_time_to_close:
            summary_data.append(["Issues", "Average Time to Close", f"{metrics.issue_metrics.average_time_to_close:.1f}", "hours"])
        
        writer.writerows(summary_data)
        
        # Export velocity trends if available
        if metrics.velocity_trends:
            output.write("\n\n## Velocity Trends\n")
            velocity_data = [["Date", "Commits", "Additions", "Deletions", "Pull Requests", "Issues Closed", "Total Changes"]]
            
            for vp in metrics.velocity_trends:
                velocity_data.append([
                    vp.timestamp.strftime('%Y-%m-%d'),
                    str(vp.commits),
                    str(vp.additions),
                    str(vp.deletions),
                    str(vp.pull_requests),
                    str(vp.issues_closed),
                    str(vp.total_changes)
                ])
            
            writer.writerows(velocity_data)
        
        # Export commit frequency data
        if metrics.commit_metrics.commit_frequency:
            output.write("\n\n## Commit Frequency\n")
            
            # Daily frequency
            if 'daily' in metrics.commit_metrics.commit_frequency:
                output.write("### Daily Frequency\n")
                daily_data = [["Date", "Commits"]]
                for date, count in sorted(metrics.commit_metrics.commit_frequency['daily'].items()):
                    daily_data.append([date, str(count)])
                writer.writerows(daily_data)
            
            # Hourly frequency
            if 'hourly' in metrics.commit_metrics.commit_frequency:
                output.write("\n### Hourly Distribution\n")
                hourly_data = [["Hour", "Commits"]]
                for hour in range(24):
                    count = metrics.commit_metrics.commit_frequency['hourly'].get(str(hour), 0)
                    hourly_data.append([f"{hour:02d}:00", str(count)])
                writer.writerows(hourly_data)
        
        # Export time distribution
        if metrics.time_distribution:
            output.write("\n\n## Time Distribution\n")
            time_data = [["Activity", "Percentage"]]
            for activity, percentage in metrics.time_distribution.items():
                time_data.append([activity.replace('_', ' ').title(), f"{percentage:.1f}"])
            writer.writerows(time_data)
        
        # Export most active hours
        if metrics.commit_metrics.most_active_hours:
            output.write("\n\n## Most Active Hours\n")
            active_hours_data = [["Rank", "Hour", "Activity Level"]]
            for i, hour in enumerate(metrics.commit_metrics.most_active_hours, 1):
                active_hours_data.append([str(i), f"{hour:02d}:00", "High"])
            writer.writerows(active_hours_data)
        
        return output.getvalue()
    
    def export_velocity_trends_only(self, metrics: ProductivityMetrics) -> str:
        """
        Export only velocity trends data to CSV format.
        
        Args:
            metrics: ProductivityMetrics containing velocity data
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        output.write("# GitHub Productivity Dashboard - Velocity Trends Export\n")
        output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}\n")
        output.write("\n")
        
        if not metrics.velocity_trends:
            output.write("No velocity data available\n")
            return output.getvalue()
        
        # Write velocity data
        velocity_data = [
            ["Date", "Commits", "Additions", "Deletions", "Net Changes", 
             "Pull Requests", "Issues Closed", "Total Activity Score"]
        ]
        
        for vp in sorted(metrics.velocity_trends, key=lambda x: x.timestamp):
            net_changes = vp.additions - vp.deletions
            activity_score = vp.commits + vp.pull_requests + vp.issues_closed
            
            velocity_data.append([
                vp.timestamp.strftime('%Y-%m-%d'),
                str(vp.commits),
                str(vp.additions),
                str(vp.deletions),
                str(net_changes),
                str(vp.pull_requests),
                str(vp.issues_closed),
                str(activity_score)
            ])
        
        writer.writerows(velocity_data)
        return output.getvalue()
    
    def export_metrics_comparison(self, current_metrics: ProductivityMetrics, 
                                previous_metrics: ProductivityMetrics) -> str:
        """
        Export comparison between two metrics periods.
        
        Args:
            current_metrics: Current period metrics
            previous_metrics: Previous period metrics
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        output.write("# GitHub Productivity Dashboard - Metrics Comparison\n")
        output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Current Period: {current_metrics.period_start.strftime('%Y-%m-%d')} to {current_metrics.period_end.strftime('%Y-%m-%d')}\n")
        output.write(f"# Previous Period: {previous_metrics.period_start.strftime('%Y-%m-%d')} to {previous_metrics.period_end.strftime('%Y-%m-%d')}\n")
        output.write("\n")
        
        # Comparison data
        comparison_data = [
            ["Metric", "Current Period", "Previous Period", "Change", "Change %"]
        ]
        
        # Helper function to calculate change
        def calculate_change(current: float, previous: float) -> tuple[float, float]:
            change = current - previous
            change_percent = (change / max(previous, 0.001)) * 100 if previous != 0 else 0
            return change, change_percent
        
        # Compare key metrics
        metrics_to_compare = [
            ("Total Commits", current_metrics.commit_metrics.total_commits, previous_metrics.commit_metrics.total_commits),
            ("Daily Commit Average", current_metrics.daily_commit_average, previous_metrics.daily_commit_average),
            ("Total PRs", current_metrics.pr_metrics.total_prs, previous_metrics.pr_metrics.total_prs),
            ("PR Merge Rate", current_metrics.pr_metrics.merge_rate, previous_metrics.pr_metrics.merge_rate),
            ("Reviews Given", current_metrics.review_metrics.total_reviews_given, previous_metrics.review_metrics.total_reviews_given),
            ("Reviews Received", current_metrics.review_metrics.total_reviews_received, previous_metrics.review_metrics.total_reviews_received),
            ("Issues Closed", current_metrics.issue_metrics.closed_issues, previous_metrics.issue_metrics.closed_issues),
            ("Issue Resolution Rate", current_metrics.issue_metrics.resolution_rate, previous_metrics.issue_metrics.resolution_rate),
        ]
        
        for metric_name, current_val, previous_val in metrics_to_compare:
            change, change_percent = calculate_change(current_val, previous_val)
            comparison_data.append([
                metric_name,
                f"{current_val:.1f}" if isinstance(current_val, float) else str(current_val),
                f"{previous_val:.1f}" if isinstance(previous_val, float) else str(previous_val),
                f"{change:+.1f}" if isinstance(change, float) else f"{change:+}",
                f"{change_percent:+.1f}%"
            ])
        
        writer.writerows(comparison_data)
        return output.getvalue()


class ReportExporter:
    """Handles text and PDF report export functionality."""
    
    def __init__(self):
        """Initialize report exporter."""
        pass
    
    def export_ai_analysis_report(self, analysis_report: AnalysisReport, 
                                metrics: ProductivityMetrics,
                                include_metadata: bool = True) -> str:
        """
        Export AI analysis report to text format.
        
        Args:
            analysis_report: AnalysisReport to export
            metrics: Associated ProductivityMetrics
            include_metadata: Whether to include metadata
            
        Returns:
            Text report content
        """
        output = []
        
        if include_metadata:
            output.extend([
                "=" * 60,
                "GITHUB PRODUCTIVITY DASHBOARD - AI ANALYSIS REPORT",
                "=" * 60,
                "",
                f"Generated: {analysis_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Analysis Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}",
                f"Total Days Analyzed: {metrics.period_days}",
                f"Confidence Score: {analysis_report.confidence_score * 100:.1f}%",
                "",
                "=" * 60,
                ""
            ])
        
        # Executive Summary
        output.extend([
            "EXECUTIVE SUMMARY",
            "-" * 20,
            "",
            analysis_report.summary,
            "",
        ])
        
        # Key Insights
        if analysis_report.key_insights:
            output.extend([
                "KEY INSIGHTS",
                "-" * 12,
                ""
            ])
            
            for i, insight in enumerate(analysis_report.key_insights, 1):
                output.append(f"{i}. {insight}")
            
            output.append("")
        
        # Recommendations
        if analysis_report.recommendations:
            output.extend([
                "RECOMMENDATIONS",
                "-" * 15,
                ""
            ])
            
            for i, recommendation in enumerate(analysis_report.recommendations, 1):
                output.append(f"{i}. {recommendation}")
            
            output.append("")
        
        # Anomalies
        if analysis_report.anomalies:
            output.extend([
                "ANOMALIES AND ALERTS",
                "-" * 19,
                ""
            ])
            
            for anomaly in analysis_report.anomalies:
                output.extend([
                    f"• {anomaly.metric_name.upper()} [{anomaly.severity}]",
                    f"  {anomaly.description}",
                    f"  Detected: {anomaly.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    ""
                ])
        
        # Metrics Summary
        output.extend([
            "PRODUCTIVITY METRICS SUMMARY",
            "-" * 28,
            "",
            f"Commits: {metrics.commit_metrics.total_commits} total ({metrics.daily_commit_average:.1f}/day average)",
            f"Pull Requests: {metrics.pr_metrics.total_prs} total ({metrics.pr_metrics.merge_rate:.1f}% merge rate)",
            f"Code Reviews: {metrics.review_metrics.total_reviews_given} given, {metrics.review_metrics.total_reviews_received} received",
            f"Issues: {metrics.issue_metrics.closed_issues}/{metrics.issue_metrics.total_issues} resolved ({metrics.issue_metrics.resolution_rate:.1f}% rate)",
            "",
        ])
        
        # Velocity Trends Summary
        if metrics.velocity_trends:
            recent_trends = metrics.velocity_trends[-7:]  # Last 7 data points
            avg_commits = sum(vp.commits for vp in recent_trends) / len(recent_trends)
            avg_changes = sum(vp.total_changes for vp in recent_trends) / len(recent_trends)
            
            output.extend([
                "RECENT VELOCITY TRENDS (Last 7 Data Points)",
                "-" * 42,
                "",
                f"Average Daily Commits: {avg_commits:.1f}",
                f"Average Daily Code Changes: {avg_changes:.0f}",
                f"Most Recent Activity: {recent_trends[-1].timestamp.strftime('%Y-%m-%d')}",
                "",
            ])
        
        # Footer
        if include_metadata:
            output.extend([
                "=" * 60,
                "End of Report",
                "",
                "This report was generated by the GitHub Productivity Dashboard",
                "using AI-powered analysis from OpenAI's ChatGPT API.",
                "=" * 60
            ])
        
        return "\n".join(output)
    
    def export_comprehensive_insights(self, insights: Dict[str, Any], 
                                    metrics: ProductivityMetrics) -> str:
        """
        Export comprehensive AI insights to text format.
        
        Args:
            insights: Comprehensive insights dictionary
            metrics: Associated ProductivityMetrics
            
        Returns:
            Text report content
        """
        output = []
        
        # Header
        output.extend([
            "=" * 70,
            "GITHUB PRODUCTIVITY DASHBOARD - COMPREHENSIVE INSIGHTS REPORT",
            "=" * 70,
            "",
            f"Generated: {insights.get('generated_at', datetime.now().isoformat())}",
            f"Analysis Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}",
            "",
        ])
        
        # Performance Score
        if 'performance_score' in insights:
            score = insights['performance_score']
            score_level = "Excellent" if score >= 80 else "Good" if score >= 60 else "Needs Improvement"
            
            output.extend([
                "OVERALL PERFORMANCE SCORE",
                "-" * 25,
                "",
                f"Score: {score}/100 ({score_level})",
                "",
            ])
        
        # Overview
        if 'overview' in insights and insights['overview']:
            overview = insights['overview']
            output.extend([
                "EXECUTIVE OVERVIEW",
                "-" * 18,
                "",
                overview.get('summary', 'No summary available'),
                "",
            ])
            
            if 'key_insights' in overview:
                output.append("Key Insights:")
                for insight in overview['key_insights']:
                    output.append(f"• {insight}")
                output.append("")
        
        # Trend Analysis
        if 'trends' in insights and insights['trends']:
            trends = insights['trends']
            output.extend([
                "TREND ANALYSIS",
                "-" * 14,
                "",
                f"Overall Direction: {trends.get('trend_direction', 'Unknown').title()}",
                "",
            ])
            
            if 'key_patterns' in trends:
                output.append("Key Patterns:")
                for pattern in trends['key_patterns']:
                    output.append(f"• {pattern}")
                output.append("")
        
        # Category-specific insights
        categories = [
            ('commit_insights', 'COMMIT PATTERNS'),
            ('pr_insights', 'PULL REQUEST PATTERNS'),
            ('review_insights', 'CODE REVIEW PATTERNS'),
            ('issue_insights', 'ISSUE MANAGEMENT PATTERNS')
        ]
        
        for key, title in categories:
            if key in insights and insights[key]:
                category_data = insights[key]
                output.extend([
                    title,
                    "-" * len(title),
                    ""
                ])
                
                for insight_key, insight_value in category_data.items():
                    if insight_key != 'recommendations':
                        display_key = insight_key.replace('_', ' ').title()
                        output.append(f"{display_key}: {insight_value}")
                
                if 'recommendations' in category_data and category_data['recommendations']:
                    output.append("")
                    output.append("Recommendations:")
                    for rec in category_data['recommendations']:
                        output.append(f"• {rec}")
                
                output.append("")
        
        # Anomalies
        if 'anomalies' in insights and insights['anomalies']:
            output.extend([
                "ANOMALIES AND ALERTS",
                "-" * 19,
                ""
            ])
            
            for anomaly in insights['anomalies']:
                severity = anomaly.get('severity', 'UNKNOWN')
                description = anomaly.get('description', 'No description')
                output.append(f"[{severity}] {description}")
            
            output.append("")
        
        # Recommendations Summary
        if 'recommendations' in insights and insights['recommendations']:
            output.extend([
                "ACTION ITEMS & RECOMMENDATIONS",
                "-" * 30,
                ""
            ])
            
            for i, rec in enumerate(insights['recommendations'], 1):
                output.append(f"{i}. {rec}")
            
            output.append("")
        
        # Footer
        output.extend([
            "=" * 70,
            "End of Comprehensive Insights Report",
            "",
            "This report provides detailed analysis of your GitHub productivity",
            "patterns and actionable recommendations for improvement.",
            "=" * 70
        ])
        
        return "\n".join(output)
    
    def export_executive_summary(self, executive_summary: Dict[str, Any], 
                               metrics: ProductivityMetrics) -> str:
        """
        Export executive summary report.
        
        Args:
            executive_summary: Executive summary data
            metrics: Associated ProductivityMetrics
            
        Returns:
            Text report content
        """
        output = []
        
        # Header
        output.extend([
            "=" * 50,
            "EXECUTIVE PRODUCTIVITY SUMMARY",
            "=" * 50,
            "",
            f"Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ])
        
        # Overall Assessment
        assessment = executive_summary.get('overall_assessment', 'Satisfactory')
        output.extend([
            "OVERALL ASSESSMENT",
            "-" * 18,
            "",
            f"Status: {assessment}",
            "",
            executive_summary.get('executive_summary', 'No summary available'),
            "",
        ])
        
        # Key Achievements
        if 'key_achievements' in executive_summary:
            output.extend([
                "KEY ACHIEVEMENTS",
                "-" * 16,
                ""
            ])
            
            for achievement in executive_summary['key_achievements']:
                output.append(f"✓ {achievement}")
            
            output.append("")
        
        # Areas of Concern
        if 'concerns' in executive_summary and executive_summary['concerns']:
            output.extend([
                "AREAS OF CONCERN",
                "-" * 16,
                ""
            ])
            
            for concern in executive_summary['concerns']:
                output.append(f"⚠ {concern}")
            
            output.append("")
        
        # Strategic Recommendations
        if 'strategic_recommendations' in executive_summary:
            output.extend([
                "STRATEGIC RECOMMENDATIONS",
                "-" * 24,
                ""
            ])
            
            for i, rec in enumerate(executive_summary['strategic_recommendations'], 1):
                output.append(f"{i}. {rec}")
            
            output.append("")
        
        # Productivity Trend
        trend = executive_summary.get('productivity_trend', 'Stable')
        output.extend([
            "PRODUCTIVITY TREND",
            "-" * 18,
            "",
            f"Direction: {trend}",
            "",
        ])
        
        # Key Metrics
        output.extend([
            "KEY METRICS",
            "-" * 11,
            "",
            f"Total Commits: {metrics.commit_metrics.total_commits}",
            f"Pull Requests: {metrics.pr_metrics.total_prs} ({metrics.pr_metrics.merge_rate:.1f}% merged)",
            f"Code Reviews: {metrics.review_metrics.total_reviews_given} given",
            f"Issues Resolved: {metrics.issue_metrics.closed_issues}",
            "",
        ])
        
        # Footer
        output.extend([
            "=" * 50,
            "End of Executive Summary",
            "=" * 50
        ])
        
        return "\n".join(output)


class ExportManager:
    """Main export manager that coordinates different export types."""
    
    def __init__(self):
        """Initialize export manager with sub-exporters."""
        self.csv_exporter = CSVExporter()
        self.report_exporter = ReportExporter()
    
    def create_export_filename(self, export_type: str, metrics: ProductivityMetrics, 
                             extension: str) -> str:
        """
        Create standardized filename for exports.
        
        Args:
            export_type: Type of export (metrics, analysis, etc.)
            metrics: ProductivityMetrics for date range
            extension: File extension
            
        Returns:
            Formatted filename
        """
        start_date = metrics.period_start.strftime('%Y%m%d')
        end_date = metrics.period_end.strftime('%Y%m%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"github_productivity_{export_type}_{start_date}_{end_date}_{timestamp}.{extension}"
    
    def get_export_metadata(self, metrics: ProductivityMetrics, 
                          additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get standardized export metadata.
        
        Args:
            metrics: ProductivityMetrics
            additional_info: Additional metadata to include
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'export_timestamp': datetime.now().isoformat(),
            'analysis_period_start': metrics.period_start.isoformat(),
            'analysis_period_end': metrics.period_end.isoformat(),
            'total_days': metrics.period_days,
            'dashboard_version': '1.0.0',
            'export_format_version': '1.0'
        }
        
        if additional_info:
            metadata.update(additional_info)
        
        return metadata


class VisualizationExporter:
    """Handles export of dashboard visualizations and screenshots."""
    
    def __init__(self):
        """Initialize visualization exporter."""
        pass
    
    def export_plotly_chart_html(self, fig, title: str = "Chart") -> str:
        """
        Export Plotly figure to standalone HTML.
        
        Args:
            fig: Plotly figure object
            title: Chart title
            
        Returns:
            HTML content as string
        """
        try:
            import plotly.offline as pyo
            
            # Configure the HTML
            config = {
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
            }
            
            # Generate HTML
            html_content = pyo.plot(
                fig, 
                output_type='div', 
                include_plotlyjs=True,
                config=config,
                div_id=f"chart_{title.lower().replace(' ', '_')}"
            )
            
            # Wrap in complete HTML document
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title} - GitHub Productivity Dashboard</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Generated by GitHub Productivity Dashboard on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="chart-container">
        {html_content}
    </div>
    <div class="footer">
        <p>GitHub Productivity Dashboard - Powered by Streamlit and Plotly</p>
    </div>
</body>
</html>
"""
            return full_html
            
        except Exception as e:
            return f"<html><body><h1>Error exporting chart</h1><p>{str(e)}</p></body></html>"
    
    def create_dashboard_screenshot_html(self, metrics: ProductivityMetrics) -> str:
        """
        Create HTML version of dashboard for screenshot/PDF conversion.
        
        Args:
            metrics: ProductivityMetrics to display
            
        Returns:
            HTML content as string
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Productivity Dashboard Report</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .metric-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 0;
        }}
        .metric-card .unit {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #007bff;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .details-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }}
        .detail-section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .detail-section h3 {{
            color: #495057;
            margin-top: 0;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 5px 0;
            border-bottom: 1px solid #dee2e6;
        }}
        .stat-row:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            font-weight: 500;
            color: #495057;
        }}
        .stat-value {{
            color: #007bff;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .period-info {{
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .period-info strong {{
            color: #1976d2;
        }}
        @media print {{
            body {{ background-color: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 GitHub Productivity Dashboard</h1>
            <p>Comprehensive Developer Productivity Analysis</p>
        </div>
        
        <div class="period-info">
            <strong>Analysis Period:</strong> {metrics.period_start.strftime('%B %d, %Y')} to {metrics.period_end.strftime('%B %d, %Y')} 
            ({metrics.period_days} days)
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Commits</h3>
                <div class="value">{metrics.commit_metrics.total_commits}</div>
                <div class="unit">{metrics.daily_commit_average:.1f}/day avg</div>
            </div>
            <div class="metric-card">
                <h3>Pull Requests</h3>
                <div class="value">{metrics.pr_metrics.total_prs}</div>
                <div class="unit">{metrics.pr_metrics.merge_rate:.1f}% merged</div>
            </div>
            <div class="metric-card">
                <h3>Code Reviews</h3>
                <div class="value">{metrics.review_metrics.total_reviews_given}</div>
                <div class="unit">reviews given</div>
            </div>
            <div class="metric-card">
                <h3>Issues Resolved</h3>
                <div class="value">{metrics.issue_metrics.closed_issues}</div>
                <div class="unit">{metrics.issue_metrics.resolution_rate:.1f}% rate</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Detailed Metrics</h2>
            <div class="details-grid">
                <div class="detail-section">
                    <h3>💻 Commit Activity</h3>
                    <div class="stat-row">
                        <span class="stat-label">Average Additions</span>
                        <span class="stat-value">{metrics.commit_metrics.average_additions:.0f} lines</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Deletions</span>
                        <span class="stat-value">{metrics.commit_metrics.average_deletions:.0f} lines</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Files per Commit</span>
                        <span class="stat-value">{metrics.commit_metrics.average_files_changed:.1f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Message Length</span>
                        <span class="stat-value">{metrics.commit_metrics.commit_message_length_avg:.0f} chars</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>🔄 Pull Request Performance</h3>
                    <div class="stat-row">
                        <span class="stat-label">Merged PRs</span>
                        <span class="stat-value">{metrics.pr_metrics.merged_prs}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Open PRs</span>
                        <span class="stat-value">{metrics.pr_metrics.open_prs}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Commits/PR</span>
                        <span class="stat-value">{metrics.pr_metrics.average_commits_per_pr:.1f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Average Changes/PR</span>
                        <span class="stat-value">{metrics.pr_metrics.average_additions + metrics.pr_metrics.average_deletions:.0f} lines</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>👥 Code Review Activity</h3>
                    <div class="stat-row">
                        <span class="stat-label">Reviews Given</span>
                        <span class="stat-value">{metrics.review_metrics.total_reviews_given}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Reviews Received</span>
                        <span class="stat-value">{metrics.review_metrics.total_reviews_received}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Approval Rate</span>
                        <span class="stat-value">{metrics.review_metrics.approval_rate:.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Participation Rate</span>
                        <span class="stat-value">{metrics.review_metrics.review_participation_rate:.1f}%</span>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>🐛 Issue Management</h3>
                    <div class="stat-row">
                        <span class="stat-label">Issues Created</span>
                        <span class="stat-value">{metrics.issue_metrics.issues_created}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Issues Assigned</span>
                        <span class="stat-value">{metrics.issue_metrics.issues_assigned}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Issues Closed</span>
                        <span class="stat-value">{metrics.issue_metrics.closed_issues}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Resolution Rate</span>
                        <span class="stat-value">{metrics.issue_metrics.resolution_rate:.1f}%</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>GitHub Productivity Dashboard - Powered by Streamlit and AI</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    def create_chart_collection_html(self, charts_data: List[Dict[str, Any]], 
                                   metrics: ProductivityMetrics) -> str:
        """
        Create HTML collection of multiple charts for export.
        
        Args:
            charts_data: List of chart data dictionaries
            metrics: ProductivityMetrics for context
            
        Returns:
            HTML content as string
        """
        charts_html = []
        
        for chart_info in charts_data:
            chart_title = chart_info.get('title', 'Chart')
            chart_description = chart_info.get('description', '')
            
            # This would normally contain the actual chart HTML
            # For now, we'll create a placeholder
            chart_html = f"""
            <div class="chart-section">
                <h3>{chart_title}</h3>
                {f'<p class="chart-description">{chart_description}</p>' if chart_description else ''}
                <div class="chart-placeholder">
                    <p>Chart: {chart_title}</p>
                    <p>This would contain the interactive {chart_title.lower()} visualization</p>
                </div>
            </div>
            """
            charts_html.append(chart_html)
        
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Productivity Charts - Dashboard Export</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
        }}
        .chart-section {{
            background-color: white;
            margin-bottom: 30px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-section h3 {{
            color: #495057;
            margin-top: 0;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }}
        .chart-description {{
            color: #6c757d;
            margin-bottom: 20px;
            font-style: italic;
        }}
        .chart-placeholder {{
            background-color: #f8f9fa;
            border: 2px dashed #dee2e6;
            padding: 40px;
            text-align: center;
            border-radius: 8px;
            color: #6c757d;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 GitHub Productivity Charts</h1>
            <p>Analysis Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        {''.join(charts_html)}
        
        <div class="footer">
            <p>GitHub Productivity Dashboard - Interactive Charts Export</p>
        </div>
    </div>
</body>
</html>
"""
        return full_html


class PDFExporter:
    """Handles PDF export functionality (requires additional dependencies)."""
    
    def __init__(self):
        """Initialize PDF exporter."""
        self.available = self._check_dependencies()
    
    def _check_dependencies(self) -> bool:
        """Check if PDF export dependencies are available."""
        try:
            # These would be optional dependencies
            # import weasyprint  # or reportlab, pdfkit, etc.
            return False  # Disabled for now
        except ImportError:
            return False
    
    def html_to_pdf(self, html_content: str) -> bytes:
        """
        Convert HTML content to PDF bytes.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            PDF content as bytes
        """
        if not self.available:
            raise RuntimeError("PDF export dependencies not available")
        
        # This would use a library like weasyprint or pdfkit
        # For now, return placeholder
        return b"PDF export not implemented - install weasyprint or similar library"
    
    def create_pdf_report(self, metrics: ProductivityMetrics, 
                         analysis_report: Optional[AnalysisReport] = None) -> bytes:
        """
        Create PDF report from metrics and analysis.
        
        Args:
            metrics: ProductivityMetrics to include
            analysis_report: Optional AnalysisReport to include
            
        Returns:
            PDF content as bytes
        """
        if not self.available:
            raise RuntimeError("PDF export dependencies not available")
        
        # Create HTML content
        viz_exporter = VisualizationExporter()
        html_content = viz_exporter.create_dashboard_screenshot_html(metrics)
        
        # Convert to PDF
        return self.html_to_pdf(html_content)


# Update the main ExportManager class
class ExportManager:
    """Main export manager that coordinates different export types."""
    
    def __init__(self):
        """Initialize export manager with sub-exporters."""
        self.csv_exporter = CSVExporter()
        self.report_exporter = ReportExporter()
        self.viz_exporter = VisualizationExporter()
        self.pdf_exporter = PDFExporter()
    
    def create_export_filename(self, export_type: str, metrics: ProductivityMetrics, 
                             extension: str) -> str:
        """
        Create standardized filename for exports.
        
        Args:
            export_type: Type of export (metrics, analysis, etc.)
            metrics: ProductivityMetrics for date range
            extension: File extension
            
        Returns:
            Formatted filename
        """
        start_date = metrics.period_start.strftime('%Y%m%d')
        end_date = metrics.period_end.strftime('%Y%m%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"github_productivity_{export_type}_{start_date}_{end_date}_{timestamp}.{extension}"
    
    def get_export_metadata(self, metrics: ProductivityMetrics, 
                          additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get standardized export metadata.
        
        Args:
            metrics: ProductivityMetrics
            additional_info: Additional metadata to include
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'export_timestamp': datetime.now().isoformat(),
            'analysis_period_start': metrics.period_start.isoformat(),
            'analysis_period_end': metrics.period_end.isoformat(),
            'total_days': metrics.period_days,
            'dashboard_version': '1.0.0',
            'export_format_version': '1.0'
        }
        
        if additional_info:
            metadata.update(additional_info)
        
        return metadata
    
    def export_dashboard_html(self, metrics: ProductivityMetrics) -> str:
        """
        Export complete dashboard as HTML for screenshot/PDF conversion.
        
        Args:
            metrics: ProductivityMetrics to export
            
        Returns:
            HTML content as string
        """
        return self.viz_exporter.create_dashboard_screenshot_html(metrics)
    
    def export_charts_html(self, charts_data: List[Dict[str, Any]], 
                         metrics: ProductivityMetrics) -> str:
        """
        Export charts collection as HTML.
        
        Args:
            charts_data: List of chart information
            metrics: ProductivityMetrics for context
            
        Returns:
            HTML content as string
        """
        return self.viz_exporter.create_chart_collection_html(charts_data, metrics)
    
    def is_pdf_export_available(self) -> bool:
        """Check if PDF export is available."""
        return self.pdf_exporter.available