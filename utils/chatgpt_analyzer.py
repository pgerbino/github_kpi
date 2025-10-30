"""
ChatGPT analyzer for GitHub Productivity Dashboard.

This module provides AI-powered analysis and insights generation using OpenAI's ChatGPT API.
It includes prompt management, productivity analysis, and user question answering functionality.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from openai import OpenAI
from openai.types.chat import ChatCompletion

from models.config import OpenAICredentials
from models.metrics import ProductivityMetrics, AnalysisReport, Anomaly
from utils.error_handler import error_handler, with_error_handling, safe_execute


class PromptManager:
    """Manages structured prompts for productivity analysis."""
    
    @staticmethod
    def get_productivity_analysis_prompt(metrics: ProductivityMetrics) -> str:
        """Generate prompt for comprehensive productivity analysis."""
        metrics_summary = {
            'period': f"{metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}",
            'total_commits': metrics.commit_metrics.total_commits,
            'total_prs': metrics.pr_metrics.total_prs,
            'merged_prs': metrics.pr_metrics.merged_prs,
            'merge_rate': metrics.pr_metrics.merge_rate,
            'total_reviews_given': metrics.review_metrics.total_reviews_given,
            'total_reviews_received': metrics.review_metrics.total_reviews_received,
            'approval_rate': metrics.review_metrics.approval_rate,
            'total_issues': metrics.issue_metrics.total_issues,
            'closed_issues': metrics.issue_metrics.closed_issues,
            'resolution_rate': metrics.issue_metrics.resolution_rate,
            'daily_commit_average': metrics.daily_commit_average
        }
        
        return f"""
You are a senior software engineering productivity analyst. Analyze the following developer productivity metrics and provide comprehensive insights.

PRODUCTIVITY METRICS DATA:
{json.dumps(metrics_summary, indent=2)}

DETAILED METRICS:
- Commit Activity: {metrics.commit_metrics.total_commits} commits, avg {metrics.commit_metrics.average_additions:.1f} additions, {metrics.commit_metrics.average_deletions:.1f} deletions per commit
- Pull Requests: {metrics.pr_metrics.total_prs} total, {metrics.pr_metrics.merged_prs} merged ({metrics.pr_metrics.merge_rate:.1f}% merge rate)
- Code Reviews: {metrics.review_metrics.total_reviews_given} given, {metrics.review_metrics.total_reviews_received} received
- Issues: {metrics.issue_metrics.total_issues} total, {metrics.issue_metrics.closed_issues} closed ({metrics.issue_metrics.resolution_rate:.1f}% resolution rate)

Please provide:
1. SUMMARY: A 2-3 sentence overview of overall productivity
2. KEY_INSIGHTS: 3-5 specific observations about patterns, strengths, or areas of concern
3. RECOMMENDATIONS: 3-5 actionable suggestions for improvement
4. ANOMALIES: Any unusual patterns or outliers that warrant attention

Format your response as JSON with the following structure:
{{
    "summary": "Brief overview of productivity",
    "key_insights": ["insight 1", "insight 2", "insight 3"],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "anomalies": [
        {{
            "metric_name": "metric name",
            "description": "description of anomaly",
            "severity": "LOW|MEDIUM|HIGH"
        }}
    ],
    "confidence_score": 0.85
}}

Focus on actionable insights that can help improve developer productivity and code quality.
"""
    
    @staticmethod
    def get_trend_analysis_prompt(metrics: ProductivityMetrics) -> str:
        """Generate prompt for trend analysis."""
        velocity_data = [
            {
                'date': vp.timestamp.strftime('%Y-%m-%d'),
                'commits': vp.commits,
                'additions': vp.additions,
                'deletions': vp.deletions,
                'pull_requests': vp.pull_requests,
                'issues_closed': vp.issues_closed
            }
            for vp in metrics.velocity_trends[-30:]  # Last 30 data points
        ]
        
        return f"""
You are a data analyst specializing in software development productivity trends. Analyze the following time-series productivity data.

VELOCITY TRENDS DATA:
{json.dumps(velocity_data, indent=2)}

ANALYSIS PERIOD: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}

Please identify:
1. Overall trends (increasing, decreasing, stable)
2. Cyclical patterns (weekly, monthly cycles)
3. Significant changes or inflection points
4. Correlation between different metrics
5. Seasonal or temporal patterns

Provide insights about:
- Productivity momentum and consistency
- Work patterns and rhythms
- Potential external factors affecting productivity
- Predictive insights for future performance

Format as JSON:
{{
    "trend_direction": "increasing|decreasing|stable|volatile",
    "key_patterns": ["pattern 1", "pattern 2"],
    "inflection_points": [
        {{
            "date": "YYYY-MM-DD",
            "description": "what changed",
            "impact": "positive|negative|neutral"
        }}
    ],
    "predictions": ["prediction 1", "prediction 2"],
    "confidence_score": 0.80
}}
"""
    
    @staticmethod
    def get_user_question_prompt(question: str, metrics: ProductivityMetrics) -> str:
        """Generate prompt for answering user questions about productivity data."""
        context_summary = {
            'period': f"{metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}",
            'commits': metrics.commit_metrics.total_commits,
            'prs': metrics.pr_metrics.total_prs,
            'reviews': metrics.review_metrics.total_reviews_given,
            'issues': metrics.issue_metrics.total_issues
        }
        
        return f"""
You are a productivity analyst assistant. Answer the user's question about their GitHub productivity data.

USER QUESTION: {question}

PRODUCTIVITY CONTEXT:
{json.dumps(context_summary, indent=2)}

AVAILABLE DATA:
- Commit metrics: frequency, code changes, timing patterns
- Pull request metrics: creation, merge rates, review times
- Code review metrics: participation, approval rates
- Issue metrics: creation, resolution rates, response times
- Time-series velocity data showing trends over time

Please provide a helpful, specific answer based on the available data. If the question cannot be answered with the available data, explain what additional information would be needed.

Keep the response conversational but informative, and include specific numbers from the data when relevant.
"""
    
    @staticmethod
    def get_anomaly_detection_prompt(metrics: ProductivityMetrics) -> str:
        """Generate prompt for anomaly detection in productivity data."""
        recent_velocity = metrics.velocity_trends[-14:] if len(metrics.velocity_trends) >= 14 else metrics.velocity_trends
        
        velocity_summary = [
            {
                'date': vp.timestamp.strftime('%Y-%m-%d'),
                'total_activity': vp.commits + vp.pull_requests + vp.issues_closed,
                'code_changes': vp.additions + vp.deletions
            }
            for vp in recent_velocity
        ]
        
        return f"""
You are an anomaly detection specialist for software development productivity. Analyze the recent productivity data for unusual patterns.

RECENT ACTIVITY DATA:
{json.dumps(velocity_summary, indent=2)}

BASELINE METRICS:
- Average daily commits: {metrics.daily_commit_average:.1f}
- Typical PR merge rate: {metrics.pr_metrics.merge_rate:.1f}%
- Standard review approval rate: {metrics.review_metrics.approval_rate:.1f}%

Look for:
1. Sudden spikes or drops in activity
2. Unusual patterns compared to historical averages
3. Inconsistent work patterns
4. Metrics that deviate significantly from norms

For each anomaly found, assess:
- Severity (LOW/MEDIUM/HIGH)
- Potential causes
- Impact on overall productivity
- Whether it requires attention

Format as JSON:
{{
    "anomalies": [
        {{
            "metric_name": "commits_per_day",
            "date": "YYYY-MM-DD",
            "expected_value": 2.5,
            "actual_value": 0.1,
            "severity": "HIGH",
            "description": "Significant drop in daily commit activity"
        }}
    ],
    "overall_assessment": "Normal|Concerning|Critical",
    "confidence_score": 0.90
}}
"""


class ChatGPTAnalyzer:
    """AI-powered productivity analyzer using OpenAI's ChatGPT API."""
    
    def __init__(self, credentials: OpenAICredentials):
        """Initialize the ChatGPT analyzer with API credentials."""
        self.credentials = credentials
        self.client = OpenAI(
            api_key=credentials.api_key,
            organization=credentials.organization_id
        )
        self.prompt_manager = PromptManager()
        self.logger = logging.getLogger(__name__)
    
    def _make_api_call(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Make API call to ChatGPT with retry logic and enhanced error handling."""
        for attempt in range(max_retries):
            try:
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.credentials.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior software engineering productivity analyst with expertise in GitHub metrics and developer performance analysis."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.credentials.max_tokens,
                    temperature=self.credentials.temperature,
                    response_format={"type": "json_object"}
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                self.logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                # Handle specific OpenAI errors
                error_str = str(e).lower()
                if 'rate limit' in error_str and attempt < max_retries - 1:
                    # Wait longer for rate limit errors
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                    self.logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                    continue
                elif 'quota' in error_str or 'billing' in error_str:
                    # Don't retry quota/billing errors
                    error_handler.handle_openai_api_error(e, "api_call")
                    raise
                elif attempt == max_retries - 1:
                    # Last attempt failed
                    error_handler.handle_openai_api_error(e, "api_call")
                    raise
                else:
                    # Wait before retry for other errors
                    wait_time = 2 ** attempt
                    import time
                    time.sleep(wait_time)
        
        return None
    
    @with_error_handling(context="ChatGPTAnalyzer.analyze_productivity_trends")
    def analyze_productivity_trends(self, metrics: ProductivityMetrics) -> AnalysisReport:
        """Generate comprehensive productivity analysis and insights."""
        try:
            prompt = self.prompt_manager.get_productivity_analysis_prompt(metrics)
            response_text = self._make_api_call(prompt)
            
            if not response_text:
                # Create fallback report
                return self._create_fallback_analysis_report(metrics)
            
            # Parse JSON response
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse ChatGPT response as JSON: {str(e)}")
                return self._create_fallback_analysis_report(metrics)
            
            # Extract anomalies if present
            anomalies = []
            for anomaly_data in response_data.get('anomalies', []):
                try:
                    anomaly = Anomaly(
                        metric_name=anomaly_data.get('metric_name', 'unknown'),
                        timestamp=datetime.now(),  # Current time for analysis
                        expected_value=0.0,  # Will be set by anomaly detection
                        actual_value=0.0,   # Will be set by anomaly detection
                        severity=anomaly_data.get('severity', 'LOW'),
                        description=anomaly_data.get('description', 'No description available')
                    )
                    anomalies.append(anomaly)
                except Exception as e:
                    self.logger.warning(f"Failed to parse anomaly data: {str(e)}")
                    continue
            
            # Create analysis report with validation
            report = AnalysisReport(
                generated_at=datetime.now(),
                summary=response_data.get('summary', 'Analysis completed successfully'),
                key_insights=response_data.get('key_insights', []),
                recommendations=response_data.get('recommendations', []),
                anomalies=anomalies,
                confidence_score=max(0.0, min(1.0, response_data.get('confidence_score', 0.8)))
            )
            
            self.logger.info("Successfully generated productivity analysis")
            return report
            
        except Exception as e:
            error_handler.handle_openai_api_error(e, "analyze_productivity_trends")
            return self._create_fallback_analysis_report(metrics)
    
    def _create_fallback_analysis_report(self, metrics: ProductivityMetrics) -> AnalysisReport:
        """Create a fallback analysis report when AI analysis fails."""
        # Generate basic insights based on metrics
        insights = []
        recommendations = []
        
        # Basic commit analysis
        if metrics.commit_metrics.total_commits > 0:
            daily_avg = metrics.daily_commit_average
            if daily_avg >= 2:
                insights.append("High commit frequency indicates active development")
            elif daily_avg >= 1:
                insights.append("Moderate commit frequency shows steady progress")
            else:
                insights.append("Low commit frequency may indicate larger, less frequent changes")
                recommendations.append("Consider making more frequent, smaller commits")
        
        # Basic PR analysis
        if metrics.pr_metrics.total_prs > 0:
            merge_rate = metrics.pr_metrics.merge_rate
            if merge_rate >= 80:
                insights.append("High pull request merge rate indicates good code quality")
            elif merge_rate >= 60:
                insights.append("Moderate pull request merge rate with room for improvement")
            else:
                insights.append("Low pull request merge rate may indicate quality issues")
                recommendations.append("Focus on improving code quality before submission")
        
        # Basic review analysis
        if metrics.review_metrics.total_reviews_given > 0:
            insights.append("Active participation in code reviews shows good collaboration")
        else:
            recommendations.append("Consider participating more in code reviews")
        
        return AnalysisReport(
            generated_at=datetime.now(),
            summary=f"Basic analysis completed for {metrics.period_days} day period with {metrics.commit_metrics.total_commits} commits and {metrics.pr_metrics.total_prs} pull requests.",
            key_insights=insights if insights else ["Analysis data available for review"],
            recommendations=recommendations if recommendations else ["Continue current development practices"],
            anomalies=[],
            confidence_score=0.6  # Lower confidence for fallback analysis
        )
    
    def identify_anomalies(self, metrics: ProductivityMetrics) -> List[Anomaly]:
        """Identify anomalies and unusual patterns in productivity data."""
        try:
            prompt = self.prompt_manager.get_anomaly_detection_prompt(metrics)
            response_text = self._make_api_call(prompt)
            
            if not response_text:
                raise ValueError("Failed to get response from ChatGPT API")
            
            response_data = json.loads(response_text)
            anomalies = []
            
            for anomaly_data in response_data.get('anomalies', []):
                anomaly = Anomaly(
                    metric_name=anomaly_data['metric_name'],
                    timestamp=datetime.fromisoformat(anomaly_data['date']) if 'date' in anomaly_data else datetime.now(),
                    expected_value=anomaly_data.get('expected_value', 0.0),
                    actual_value=anomaly_data.get('actual_value', 0.0),
                    severity=anomaly_data['severity'],
                    description=anomaly_data['description']
                )
                anomalies.append(anomaly)
            
            self.logger.info(f"Identified {len(anomalies)} anomalies")
            return anomalies
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse anomaly detection response: {str(e)}")
            return []
        
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {str(e)}")
            return []
    
    def generate_recommendations(self, metrics: ProductivityMetrics) -> List[str]:
        """Generate actionable recommendations for improving productivity."""
        try:
            # Use the main analysis prompt which includes recommendations
            analysis_report = self.analyze_productivity_trends(metrics)
            return analysis_report.recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return [
                "Focus on maintaining consistent commit patterns",
                "Improve code review participation and response times",
                "Consider breaking down large pull requests for faster reviews"
            ]
    
    def answer_user_question(self, question: str, metrics: ProductivityMetrics) -> str:
        """Answer user questions about their productivity data."""
        try:
            prompt = self.prompt_manager.get_user_question_prompt(question, metrics)
            response_text = self._make_api_call(prompt)
            
            if not response_text:
                return "I'm sorry, I couldn't process your question at the moment. Please try again."
            
            # For user questions, we expect a direct text response, not JSON
            # But let's handle both cases
            try:
                response_data = json.loads(response_text)
                return response_data.get('answer', response_text)
            except json.JSONDecodeError:
                # Direct text response
                return response_text
            
        except Exception as e:
            self.logger.error(f"Error answering user question: {str(e)}")
            return f"I encountered an error while analyzing your question: {str(e)}"
    
    def analyze_trends(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Analyze productivity trends over time."""
        try:
            prompt = self.prompt_manager.get_trend_analysis_prompt(metrics)
            response_text = self._make_api_call(prompt)
            
            if not response_text:
                raise ValueError("Failed to get response from ChatGPT API")
            
            response_data = json.loads(response_text)
            
            self.logger.info("Successfully analyzed productivity trends")
            return response_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse trend analysis response: {str(e)}")
            return {
                "trend_direction": "stable",
                "key_patterns": ["Unable to analyze trends at this time"],
                "confidence_score": 0.0
            }
        
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {str(e)}")
            return {
                "trend_direction": "unknown",
                "key_patterns": [f"Analysis error: {str(e)}"],
                "confidence_score": 0.0
            }
    
    def validate_credentials(self) -> bool:
        """Validate OpenAI API credentials by making a test call."""
        try:
            test_response = self.client.chat.completions.create(
                model=self.credentials.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello, this is a test message. Please respond with 'OK'."
                    }
                ],
                max_tokens=10,
                temperature=0
            )
            
            return test_response.choices[0].message.content is not None
            
        except Exception as e:
            error_handler.handle_openai_api_error(e, "credential_validation")
            return False


class ProductivityInsightGenerator:
    """Advanced productivity insight generation and analysis."""
    
    def __init__(self, analyzer: ChatGPTAnalyzer):
        """Initialize with a ChatGPT analyzer instance."""
        self.analyzer = analyzer
        self.logger = logging.getLogger(__name__)
    
    def generate_comprehensive_insights(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Generate comprehensive insights combining multiple analysis types."""
        insights = {
            'overview': {},
            'trends': {},
            'anomalies': [],
            'recommendations': [],
            'performance_score': 0.0,
            'generated_at': datetime.now().isoformat()
        }
        
        try:
            # Get main analysis report
            analysis_report = self.analyzer.analyze_productivity_trends(metrics)
            insights['overview'] = {
                'summary': analysis_report.summary,
                'key_insights': analysis_report.key_insights,
                'confidence_score': analysis_report.confidence_score
            }
            insights['recommendations'] = analysis_report.recommendations
            insights['anomalies'] = [anomaly.to_dict() for anomaly in analysis_report.anomalies]
            
            # Get trend analysis
            trend_analysis = self.analyzer.analyze_trends(metrics)
            insights['trends'] = trend_analysis
            
            # Calculate performance score
            insights['performance_score'] = self._calculate_performance_score(metrics)
            
            # Generate specific insights for different aspects
            insights['commit_insights'] = self._analyze_commit_patterns(metrics)
            insights['pr_insights'] = self._analyze_pr_patterns(metrics)
            insights['review_insights'] = self._analyze_review_patterns(metrics)
            insights['issue_insights'] = self._analyze_issue_patterns(metrics)
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive insights: {str(e)}")
            insights['error'] = str(e)
        
        return insights
    
    def _calculate_performance_score(self, metrics: ProductivityMetrics) -> float:
        """Calculate overall performance score based on multiple factors."""
        try:
            # Scoring factors (0-1 scale)
            commit_score = min(metrics.daily_commit_average / 3.0, 1.0)  # Target: 3 commits/day
            pr_score = metrics.pr_metrics.merge_rate / 100.0  # Merge rate as percentage
            review_score = min(metrics.review_metrics.approval_rate / 80.0, 1.0)  # Target: 80% approval
            issue_score = metrics.issue_metrics.resolution_rate / 100.0  # Resolution rate
            
            # Weighted average
            weights = {'commits': 0.3, 'prs': 0.3, 'reviews': 0.2, 'issues': 0.2}
            total_score = (
                commit_score * weights['commits'] +
                pr_score * weights['prs'] +
                review_score * weights['reviews'] +
                issue_score * weights['issues']
            )
            
            return round(total_score * 100, 1)  # Convert to 0-100 scale
            
        except Exception as e:
            self.logger.error(f"Error calculating performance score: {str(e)}")
            return 0.0
    
    def _analyze_commit_patterns(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Analyze commit patterns and provide insights."""
        commit_metrics = metrics.commit_metrics
        
        insights = {
            'consistency': 'unknown',
            'code_quality_indicator': 'unknown',
            'activity_level': 'unknown',
            'recommendations': []
        }
        
        try:
            # Analyze consistency
            if metrics.daily_commit_average >= 2:
                insights['consistency'] = 'high'
            elif metrics.daily_commit_average >= 1:
                insights['consistency'] = 'moderate'
            else:
                insights['consistency'] = 'low'
                insights['recommendations'].append("Consider making more frequent, smaller commits")
            
            # Analyze code quality indicators
            avg_changes = commit_metrics.average_additions + commit_metrics.average_deletions
            if avg_changes > 500:
                insights['code_quality_indicator'] = 'large_commits'
                insights['recommendations'].append("Consider breaking down large commits into smaller, focused changes")
            elif avg_changes < 50:
                insights['code_quality_indicator'] = 'small_commits'
            else:
                insights['code_quality_indicator'] = 'balanced'
            
            # Activity level
            if commit_metrics.total_commits > metrics.period_days * 2:
                insights['activity_level'] = 'high'
            elif commit_metrics.total_commits > metrics.period_days:
                insights['activity_level'] = 'moderate'
            else:
                insights['activity_level'] = 'low'
            
        except Exception as e:
            self.logger.error(f"Error analyzing commit patterns: {str(e)}")
        
        return insights
    
    def _analyze_pr_patterns(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Analyze pull request patterns and provide insights."""
        pr_metrics = metrics.pr_metrics
        
        insights = {
            'merge_efficiency': 'unknown',
            'pr_size_assessment': 'unknown',
            'collaboration_level': 'unknown',
            'recommendations': []
        }
        
        try:
            # Merge efficiency
            if pr_metrics.merge_rate >= 80:
                insights['merge_efficiency'] = 'excellent'
            elif pr_metrics.merge_rate >= 60:
                insights['merge_efficiency'] = 'good'
            else:
                insights['merge_efficiency'] = 'needs_improvement'
                insights['recommendations'].append("Focus on improving PR quality before submission")
            
            # PR size assessment
            avg_changes = pr_metrics.average_additions + pr_metrics.average_deletions
            if avg_changes > 1000:
                insights['pr_size_assessment'] = 'too_large'
                insights['recommendations'].append("Consider breaking down large PRs for easier review")
            elif avg_changes < 100:
                insights['pr_size_assessment'] = 'small'
            else:
                insights['pr_size_assessment'] = 'appropriate'
            
            # Collaboration level based on PR activity
            if pr_metrics.total_prs > metrics.period_days / 7:  # More than 1 PR per week
                insights['collaboration_level'] = 'high'
            elif pr_metrics.total_prs > 0:
                insights['collaboration_level'] = 'moderate'
            else:
                insights['collaboration_level'] = 'low'
                insights['recommendations'].append("Consider creating more pull requests for better collaboration")
            
        except Exception as e:
            self.logger.error(f"Error analyzing PR patterns: {str(e)}")
        
        return insights
    
    def _analyze_review_patterns(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Analyze code review patterns and provide insights."""
        review_metrics = metrics.review_metrics
        
        insights = {
            'review_participation': 'unknown',
            'review_quality': 'unknown',
            'team_collaboration': 'unknown',
            'recommendations': []
        }
        
        try:
            # Review participation
            total_reviews = review_metrics.total_reviews_given + review_metrics.total_reviews_received
            if total_reviews > metrics.period_days / 2:  # More than 1 review every 2 days
                insights['review_participation'] = 'high'
            elif total_reviews > 0:
                insights['review_participation'] = 'moderate'
            else:
                insights['review_participation'] = 'low'
                insights['recommendations'].append("Increase participation in code reviews")
            
            # Review quality based on approval rate
            if review_metrics.approval_rate >= 70:
                insights['review_quality'] = 'constructive'
            elif review_metrics.approval_rate >= 50:
                insights['review_quality'] = 'balanced'
            else:
                insights['review_quality'] = 'thorough'
            
            # Team collaboration
            review_balance = abs(review_metrics.total_reviews_given - review_metrics.total_reviews_received)
            if review_balance <= max(review_metrics.total_reviews_given, review_metrics.total_reviews_received) * 0.3:
                insights['team_collaboration'] = 'balanced'
            elif review_metrics.total_reviews_given > review_metrics.total_reviews_received:
                insights['team_collaboration'] = 'reviewer_focused'
            else:
                insights['team_collaboration'] = 'contributor_focused'
                insights['recommendations'].append("Consider participating more in reviewing others' code")
            
        except Exception as e:
            self.logger.error(f"Error analyzing review patterns: {str(e)}")
        
        return insights
    
    def _analyze_issue_patterns(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Analyze issue handling patterns and provide insights."""
        issue_metrics = metrics.issue_metrics
        
        insights = {
            'issue_resolution_efficiency': 'unknown',
            'problem_solving_activity': 'unknown',
            'maintenance_focus': 'unknown',
            'recommendations': []
        }
        
        try:
            # Resolution efficiency
            if issue_metrics.resolution_rate >= 80:
                insights['issue_resolution_efficiency'] = 'excellent'
            elif issue_metrics.resolution_rate >= 60:
                insights['issue_resolution_efficiency'] = 'good'
            else:
                insights['issue_resolution_efficiency'] = 'needs_improvement'
                insights['recommendations'].append("Focus on resolving open issues more efficiently")
            
            # Problem solving activity
            if issue_metrics.total_issues > metrics.period_days / 7:  # More than 1 issue per week
                insights['problem_solving_activity'] = 'high'
            elif issue_metrics.total_issues > 0:
                insights['problem_solving_activity'] = 'moderate'
            else:
                insights['problem_solving_activity'] = 'low'
            
            # Maintenance focus
            if issue_metrics.issues_created > issue_metrics.issues_assigned:
                insights['maintenance_focus'] = 'issue_reporter'
            elif issue_metrics.issues_assigned > issue_metrics.issues_created:
                insights['maintenance_focus'] = 'issue_resolver'
            else:
                insights['maintenance_focus'] = 'balanced'
            
        except Exception as e:
            self.logger.error(f"Error analyzing issue patterns: {str(e)}")
        
        return insights
    
    def generate_executive_summary(self, metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Generate executive summary for management reporting."""
        try:
            summary_prompt = f"""
You are creating an executive summary for management about developer productivity. 

METRICS SUMMARY:
- Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}
- Total Commits: {metrics.commit_metrics.total_commits}
- Pull Requests: {metrics.pr_metrics.total_prs} (Merge Rate: {metrics.pr_metrics.merge_rate:.1f}%)
- Code Reviews: {metrics.review_metrics.total_reviews_given} given, {metrics.review_metrics.total_reviews_received} received
- Issues: {metrics.issue_metrics.closed_issues}/{metrics.issue_metrics.total_issues} resolved

Create a concise executive summary focusing on:
1. Overall productivity assessment
2. Key achievements and metrics
3. Areas of concern (if any)
4. Strategic recommendations

Format as JSON:
{{
    "overall_assessment": "Excellent|Good|Satisfactory|Needs Attention",
    "key_achievements": ["achievement 1", "achievement 2"],
    "concerns": ["concern 1", "concern 2"],
    "strategic_recommendations": ["recommendation 1", "recommendation 2"],
    "productivity_trend": "Improving|Stable|Declining",
    "executive_summary": "2-3 sentence summary for executives"
}}
"""
            
            response_text = self.analyzer._make_api_call(summary_prompt)
            if response_text:
                return json.loads(response_text)
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
        
        # Fallback summary
        return {
            "overall_assessment": "Satisfactory",
            "key_achievements": [f"Completed {metrics.commit_metrics.total_commits} commits"],
            "concerns": [],
            "strategic_recommendations": ["Continue current development practices"],
            "productivity_trend": "Stable",
            "executive_summary": f"Developer productivity remains stable with {metrics.commit_metrics.total_commits} commits and {metrics.pr_metrics.merge_rate:.1f}% PR merge rate during the analysis period."
        }
    
    def compare_periods(self, current_metrics: ProductivityMetrics, previous_metrics: ProductivityMetrics) -> Dict[str, Any]:
        """Compare productivity between two time periods."""
        try:
            comparison_prompt = f"""
Compare these two productivity periods and provide insights on changes and trends.

CURRENT PERIOD ({current_metrics.period_start.strftime('%Y-%m-%d')} to {current_metrics.period_end.strftime('%Y-%m-%d')}):
- Commits: {current_metrics.commit_metrics.total_commits}
- PRs: {current_metrics.pr_metrics.total_prs} (Merge Rate: {current_metrics.pr_metrics.merge_rate:.1f}%)
- Reviews: {current_metrics.review_metrics.total_reviews_given}
- Issues Resolved: {current_metrics.issue_metrics.closed_issues}

PREVIOUS PERIOD ({previous_metrics.period_start.strftime('%Y-%m-%d')} to {previous_metrics.period_end.strftime('%Y-%m-%d')}):
- Commits: {previous_metrics.commit_metrics.total_commits}
- PRs: {previous_metrics.pr_metrics.total_prs} (Merge Rate: {previous_metrics.pr_metrics.merge_rate:.1f}%)
- Reviews: {previous_metrics.review_metrics.total_reviews_given}
- Issues Resolved: {previous_metrics.issue_metrics.closed_issues}

Provide comparison analysis as JSON:
{{
    "overall_trend": "Improving|Declining|Stable",
    "significant_changes": [
        {{
            "metric": "commits",
            "change_percentage": 15.5,
            "direction": "increase|decrease",
            "significance": "high|medium|low"
        }}
    ],
    "insights": ["insight 1", "insight 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}}
"""
            
            response_text = self.analyzer._make_api_call(comparison_prompt)
            if response_text:
                return json.loads(response_text)
            
        except Exception as e:
            self.logger.error(f"Error comparing periods: {str(e)}")
        
        # Fallback comparison
        commit_change = ((current_metrics.commit_metrics.total_commits - previous_metrics.commit_metrics.total_commits) / 
                        max(previous_metrics.commit_metrics.total_commits, 1)) * 100
        
        return {
            "overall_trend": "Stable",
            "significant_changes": [
                {
                    "metric": "commits",
                    "change_percentage": round(commit_change, 1),
                    "direction": "increase" if commit_change > 0 else "decrease",
                    "significance": "medium" if abs(commit_change) > 20 else "low"
                }
            ],
            "insights": [f"Commit activity changed by {commit_change:.1f}%"],
            "recommendations": ["Continue monitoring productivity trends"]
        }