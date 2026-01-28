"""Profile analysis service."""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.engine import (
    extract_profile_features,
    WeightedScorer,
    PentagonScores,
    ProfileFeatures,
)
from src.services.sela_api_client import SelaAPIClient, ProfileData


# Brand name normalization mapping (lowercase key -> display name)
BRAND_ALIASES = {
    "sela": "Sela Network",
    "selanetwork": "Sela Network",
    "sela_network": "Sela Network",
    "openai": "OpenAI",
    "chatgpt": "OpenAI",
    "gpt": "OpenAI",
    "tesla": "Tesla",
    "tsla": "Tesla",
    "spacex": "SpaceX",
    "x": "X",
    "twitter": "X",
    "google": "Google",
    "anthropic": "Anthropic",
    "claude": "Anthropic",
    "meta": "Meta",
    "facebook": "Meta",
    "instagram": "Meta",
    "apple": "Apple",
    "microsoft": "Microsoft",
    "msft": "Microsoft",
    "amazon": "Amazon",
    "aws": "Amazon",
    "nvidia": "NVIDIA",
    "nvda": "NVIDIA",
    "bitcoin": "Bitcoin",
    "btc": "Bitcoin",
    "ethereum": "Ethereum",
    "eth": "Ethereum",
    "solana": "Solana",
    "sol": "Solana",
    "grok": "Grok",
    "grokipedia": "Grok",
}

# Common words to exclude from brand detection
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "this", "that", "these", "those", "i", "you", "he", "she", "it", "we",
    "they", "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "also", "now", "new", "like", "get", "got", "go", "going",
    "make", "made", "think", "know", "see", "come", "take", "want", "look",
    "use", "find", "give", "tell", "work", "call", "try", "ask", "seem",
    "feel", "leave", "put", "mean", "keep", "let", "begin", "show", "hear",
    "play", "run", "move", "live", "believe", "hold", "bring", "happen",
    "write", "provide", "sit", "stand", "lose", "pay", "meet", "include",
    "continue", "set", "learn", "change", "lead", "understand", "watch",
    "follow", "stop", "create", "speak", "read", "allow", "add", "spend",
    "grow", "open", "walk", "win", "offer", "remember", "love", "consider",
    "appear", "buy", "wait", "serve", "die", "send", "expect", "build",
    "stay", "fall", "cut", "reach", "kill", "remain", "via", "rt", "dm",
    "lol", "lmao", "omg", "wtf", "idk", "imo", "imho", "tbh", "fyi",
    "today", "tomorrow", "yesterday", "week", "month", "year", "time",
    "day", "night", "morning", "evening", "people", "man", "woman",
    "child", "world", "life", "hand", "part", "place", "case", "thing",
}


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
    summary: str
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

        # Generate summary
        summary = self._generate_summary(profile, features, scores)

        return ProfileAnalysisResult(
            username=username,
            scores=scores,
            features=features,
            insights=insights,
            recommendations=recommendations,
            summary=summary,
            raw_data=profile,
        )

    def _calculate_profile_scores(self, features: ProfileFeatures) -> PentagonScores:
        """Calculate pentagon scores from profile features."""

        # Normalize engagement rate to 0-100 scale
        # Typical engagement rate is 0.01-0.05 (1-5%)
        # Ensure minimum 3% base rate to prevent score collapse
        effective_engagement_rate = max(features.avg_engagement_rate, 0.03)
        engagement_normalized = min(100, effective_engagement_rate * 2000)

        # Reach: Based on average views
        # Normalize assuming 10K views is baseline "good"
        # Ensure minimum score of 10
        reach = max(10, min(100, (features.avg_views / 10000) * 50 + 25))

        # Engagement: Direct from engagement rate with minimum of 5
        engagement = max(5, engagement_normalized)

        # Virality: Based on retweet ratio and average retweets with minimum of 5
        virality = max(5, min(100, (features.avg_retweets / 100) * 30 + features.retweet_ratio * 30))

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

    def _extract_brand_mentions(
        self,
        profile: ProfileData,
        min_count: int = 2,
    ) -> list[tuple[str, int]]:
        """Extract frequently mentioned brands/companies from tweets.

        Args:
            profile: Profile data with tweets
            min_count: Minimum mention count to include

        Returns:
            List of (brand_name, count) tuples, sorted by count descending
        """
        if not profile.tweets:
            return []

        word_counts: Counter[str] = Counter()

        for tweet in profile.tweets:
            # Skip retweets to focus on original content
            if tweet.is_retweet:
                continue

            content = tweet.content

            # Extract @mentions (likely company accounts)
            mentions = re.findall(r'@(\w+)', content)
            for mention in mentions:
                # Skip common bot/service accounts
                if mention.lower() not in {"twitter", "x", "youtube", "instagram"}:
                    word_counts[mention] += 2  # Weight mentions higher

            # Extract #hashtags (potential brand/topic tags)
            hashtags = re.findall(r'#(\w+)', content)
            for tag in hashtags:
                if len(tag) > 2 and tag.lower() not in STOP_WORDS:
                    word_counts[tag] += 1

            # Extract capitalized words (potential brand names)
            # Match words that start with uppercase and have 2+ chars
            cap_words = re.findall(r'\b([A-Z][a-zA-Z]{1,})\b', content)
            for word in cap_words:
                lower = word.lower()
                if lower not in STOP_WORDS and len(word) > 2:
                    word_counts[word] += 1

        # Normalize brand names and combine counts
        normalized_counts: Counter[str] = Counter()
        for word, count in word_counts.items():
            lower = word.lower()
            # Use normalized name if exists, otherwise use original
            normalized_name = BRAND_ALIASES.get(lower, word)
            normalized_counts[normalized_name] += count

        # Filter by minimum count and return sorted
        filtered = [(word, count) for word, count in normalized_counts.items() if count >= min_count]
        return sorted(filtered, key=lambda x: x[1], reverse=True)

    def _generate_summary(
        self,
        profile: ProfileData,
        features: ProfileFeatures,
        scores: PentagonScores,
    ) -> str:
        """Generate a 2-line summary of the profile.

        Args:
            profile: Profile data with tweets
            features: Extracted profile features
            scores: Calculated pentagon scores

        Returns:
            2-line summary string
        """
        lines = []

        # Line 1: Brand/topic + account characteristics
        brand_mentions = self._extract_brand_mentions(profile, min_count=2)

        if brand_mentions:
            # Use top mentioned brand
            top_brand = brand_mentions[0][0]
            lines.append(f"An account primarily focused on {top_brand}-related content.")
        else:
            # Fallback to reach score-based description
            if scores.reach >= 70:
                lines.append("A high-reach account with strong visibility.")
            elif scores.reach >= 40:
                lines.append("An active account with moderate reach.")
            else:
                lines.append("A growing account building its audience.")

        # Line 2: Describe top 2 strengths based on scores
        score_dict = scores.to_dict()
        sorted_scores = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
        top_two = sorted_scores[:2]

        strength_descriptions = {
            "reach": "strong visibility",
            "engagement": "high audience interaction",
            "virality": "viral potential",
            "quality": "consistent quality content",
            "longevity": "lasting content impact",
        }

        strengths = [strength_descriptions[s[0]] for s in top_two]
        lines.append(f"Key strengths: {strengths[0]} and {strengths[1]}.")

        return "\n".join(lines)
