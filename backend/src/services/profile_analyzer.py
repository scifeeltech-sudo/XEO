"""Profile analysis service."""

from dataclasses import dataclass
from typing import Optional

from src.engine import (
    extract_profile_features,
    WeightedScorer,
    PentagonScores,
    ProfileFeatures,
)
from src.services.sela_api_client import SelaAPIClient, ProfileData


@dataclass
class Insight:
    """Analysis insight."""
    category: str
    message: str
    priority: str  # "high", "medium", "low"


@dataclass
class Recommendation:
    """Improvement recommendation."""
    action: str
    expected_impact: str
    description: str


@dataclass
class ProfileAnalysisResult:
    """Result of profile analysis."""
    username: str
    scores: PentagonScores
    features: ProfileFeatures
    insights: list[Insight]
    recommendations: list[Recommendation]
    raw_data: Optional[ProfileData] = None


class ProfileAnalyzer:
    """Service for analyzing X profiles."""

    def __init__(self):
        self.client = SelaAPIClient()
        self.scorer = WeightedScorer()

    async def analyze(
        self,
        username: str,
        post_count: int = 20,
    ) -> ProfileAnalysisResult:
        """
        Analyze a user's X profile.

        Args:
            username: X username (without @)
            post_count: Number of recent posts to analyze

        Returns:
            ProfileAnalysisResult with scores, insights, and recommendations
        """
        # Fetch profile data
        response = await self.client.get_twitter_profile(username, post_count)

        if not response.success or not response.profile:
            raise ValueError(f"Failed to fetch profile: {response.error}")

        profile = response.profile

        # Extract features
        features = extract_profile_features(profile)

        # Calculate aggregate scores based on historical performance
        scores = self._calculate_profile_scores(features)

        # Generate insights
        insights = self._generate_insights(features, scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(features, scores)

        return ProfileAnalysisResult(
            username=username,
            scores=scores,
            features=features,
            insights=insights,
            recommendations=recommendations,
            raw_data=profile,
        )

    def _calculate_profile_scores(self, features: ProfileFeatures) -> PentagonScores:
        """Calculate pentagon scores from profile features."""

        # Normalize engagement rate to 0-100 scale
        # Typical engagement rate is 0.01-0.05 (1-5%)
        engagement_normalized = min(100, features.avg_engagement_rate * 2000)

        # Reach: Based on average views
        # Normalize assuming 10K views is baseline "good"
        reach = min(100, (features.avg_views / 10000) * 50 + 25)

        # Engagement: Direct from engagement rate
        engagement = engagement_normalized

        # Virality: Based on retweet ratio and average retweets
        virality = min(100, (features.avg_retweets / 100) * 30 + features.retweet_ratio * 30)

        # Quality: Based on consistency and low retweet ratio (more original content)
        quality = features.engagement_consistency * 50 + (1 - features.retweet_ratio) * 30 + 20

        # Longevity: Based on media ratio and reply engagement
        longevity = features.media_ratio * 30 + min(40, (features.avg_replies / 50) * 40) + 20

        return PentagonScores(
            reach=reach,
            engagement=engagement,
            virality=virality,
            quality=quality,
            longevity=longevity,
        )

    def _generate_insights(
        self,
        features: ProfileFeatures,
        scores: PentagonScores,
    ) -> list[Insight]:
        """Generate insights based on profile analysis."""
        insights = []

        # Engagement insights
        if features.avg_engagement_rate < 0.02:
            insights.append(Insight(
                category="engagement",
                message="Your engagement rate is below average. Try creating more interactive content.",
                priority="high",
            ))
        elif features.avg_engagement_rate > 0.05:
            insights.append(Insight(
                category="engagement",
                message="Your engagement rate is excellent! Keep up your current strategy.",
                priority="low",
            ))

        # Content mix insights
        if features.retweet_ratio > 0.5:
            insights.append(Insight(
                category="content",
                message="High retweet ratio detected. Consider creating more original content.",
                priority="medium",
            ))

        if features.media_ratio < 0.3:
            insights.append(Insight(
                category="media",
                message="Low media usage. Images and videos boost engagement significantly.",
                priority="medium",
            ))

        # Consistency insights
        if features.engagement_consistency < 0.5:
            insights.append(Insight(
                category="consistency",
                message="High engagement volatility. Try to maintain consistent content quality.",
                priority="medium",
            ))

        return insights

    def _generate_recommendations(
        self,
        features: ProfileFeatures,
        scores: PentagonScores,
    ) -> list[Recommendation]:
        """Generate recommendations based on profile analysis."""
        recommendations = []

        # Find weakest dimension
        score_dict = scores.to_dict()
        weakest = min(score_dict, key=score_dict.get)

        if weakest == "reach":
            recommendations.append(Recommendation(
                action="increase_posting_frequency",
                expected_impact="+20% reach",
                description="Post more frequently to create more exposure opportunities.",
            ))
        elif weakest == "engagement":
            recommendations.append(Recommendation(
                action="add_questions",
                expected_impact="+15% engagement",
                description="Add questions to your posts to encourage replies.",
            ))
        elif weakest == "virality":
            recommendations.append(Recommendation(
                action="create_shareable_content",
                expected_impact="+25% virality",
                description="Share valuable insights and information worth sharing.",
            ))
        elif weakest == "quality":
            recommendations.append(Recommendation(
                action="focus_on_original_content",
                expected_impact="+20% quality",
                description="Focus on original content rather than retweets.",
            ))
        elif weakest == "longevity":
            recommendations.append(Recommendation(
                action="add_media",
                expected_impact="+30% longevity",
                description="Add images or videos to increase dwell time.",
            ))

        # Media recommendation if low
        if features.media_ratio < 0.4:
            recommendations.append(Recommendation(
                action="increase_media_usage",
                expected_impact="+15% overall",
                description="Include media in at least 40% of your posts.",
            ))

        return recommendations
