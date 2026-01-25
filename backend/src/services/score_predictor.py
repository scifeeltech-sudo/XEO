"""Score prediction service for posts."""

from dataclasses import dataclass, field
from typing import Literal, Optional

from src.engine import (
    extract_post_features,
    extract_profile_features,
    WeightedScorer,
    PentagonScores,
    ActionProbabilities,
    PostFeatures,
)
from src.services.sela_api_client import SelaAPIClient, TweetData


@dataclass
class QuickTip:
    """Structured quick tip for post optimization."""
    tip_id: str
    description: str
    impact: str
    target_score: str
    selectable: bool = True


@dataclass
class ContextInfo:
    """Context information for reply/quote posts."""
    target_post: TweetData
    context_adjustments: dict[str, str]
    recommendations: list[str]


@dataclass
class PostAnalysisResult:
    """Result of post analysis."""
    scores: PentagonScores
    probabilities: ActionProbabilities
    features: PostFeatures
    quick_tips: list[QuickTip]
    context: Optional[ContextInfo] = None


class ScorePredictor:
    """Service for predicting post scores."""

    def __init__(self):
        self.client = SelaAPIClient()
        self.scorer = WeightedScorer()
        self._profile_cache: dict[str, any] = {}

    async def predict(
        self,
        username: str,
        content: str,
        post_type: Literal["original", "reply", "quote", "thread"] = "original",
        target_post_url: Optional[str] = None,
        media_type: Optional[Literal["image", "video", "gif"]] = None,
    ) -> PostAnalysisResult:
        """
        Predict scores for a post.

        Args:
            username: Author's X username
            content: Post content
            post_type: Type of post
            target_post_url: URL of target post (for reply/quote)
            media_type: Type of media attached

        Returns:
            PostAnalysisResult with scores and recommendations
        """
        # Get or fetch profile data
        profile_features = await self._get_profile_features(username)

        # Extract post features
        post_features = extract_post_features(
            content,
            media_type=media_type,
            is_quote=(post_type == "quote"),
        )

        # Get context for reply/quote
        context = None
        context_boost = None

        if post_type in ("reply", "quote") and target_post_url:
            context, context_boost = await self._analyze_context(target_post_url)

        # Calculate scores
        scores, probs = self.scorer.analyze_post(
            post_features,
            profile_features,
            context_boost,
        )

        # Generate quick tips
        quick_tips = self._generate_quick_tips(post_features, scores)

        return PostAnalysisResult(
            scores=scores,
            probabilities=probs,
            features=post_features,
            quick_tips=quick_tips,
            context=context,
        )

    async def _get_profile_features(self, username: str):
        """Get profile features (with caching)."""
        if username in self._profile_cache:
            return self._profile_cache[username]

        response = await self.client.get_twitter_profile(username, post_count=20)

        if response.success and response.profile:
            features = extract_profile_features(response.profile)
            self._profile_cache[username] = features
            return features

        # Return default features if fetch fails
        from src.engine.feature_extractor import ProfileFeatures
        return ProfileFeatures(
            username=username,
            tweet_count=0,
            avg_engagement_rate=0.02,
            avg_likes=100,
            avg_retweets=10,
            avg_replies=5,
            avg_views=1000,
            retweet_ratio=0.2,
            quote_ratio=0.1,
            media_ratio=0.5,
            engagement_consistency=0.7,
        )

    async def _analyze_context(
        self,
        target_post_url: str,
    ) -> tuple[Optional[ContextInfo], Optional[dict[str, float]]]:
        """Analyze target post context for reply/quote."""

        target_post = await self.client.get_post_context(target_post_url)

        if not target_post:
            return None, None

        # Calculate context boosts
        context_boost = {}
        adjustments = {}
        recommendations = []

        # Large account bonus
        if target_post.views_count > 100000:
            context_boost["p_click"] = 0.25
            context_boost["p_profile_click"] = 0.20
            adjustments["large_account_bonus"] = "+25%"
            recommendations.append("대형 계정 포스트로 높은 노출이 예상됩니다")

        # Freshness bonus (if posted within last hour)
        if target_post.posted_at:
            from datetime import datetime, timezone
            age_minutes = (datetime.now(timezone.utc) - target_post.posted_at).total_seconds() / 60

            if age_minutes < 60:
                context_boost["p_click"] = context_boost.get("p_click", 0) + 0.15
                adjustments["freshness_bonus"] = "+15%"
                recommendations.append(f"포스트가 {int(age_minutes)}분 전에 작성되어 신선도 보너스가 적용됩니다")

        # Reply competition penalty
        if target_post.replies_count > 1000:
            penalty = -0.10
            context_boost["p_click"] = context_boost.get("p_click", 0) + penalty
            adjustments["reply_competition"] = "-10%"
            recommendations.append(f"현재 답글 {target_post.replies_count:,}개로 경쟁이 있으니 차별화된 관점을 제시하세요")

        context = ContextInfo(
            target_post=target_post,
            context_adjustments=adjustments,
            recommendations=recommendations,
        )

        return context, context_boost

    def _generate_quick_tips(
        self,
        features: PostFeatures,
        scores: PentagonScores,
    ) -> list[QuickTip]:
        """Generate quick improvement tips."""
        tips = []

        if not features.has_emoji:
            tips.append(QuickTip(
                tip_id="add_emoji",
                description="이모지를 추가하면 engagement +8% 예상",
                impact="+8%",
                target_score="engagement",
            ))

        if not features.has_question:
            tips.append(QuickTip(
                tip_id="add_question",
                description="질문 형태로 바꾸면 reply율 +15% 예상",
                impact="+15%",
                target_score="engagement",
            ))

        if not features.has_media:
            tips.append(QuickTip(
                tip_id="add_media_hint",
                description="이미지를 추가하면 reach +20% 예상",
                impact="+20%",
                target_score="reach",
                selectable=False,  # Can't auto-apply media
            ))

        if features.char_count < 50:
            tips.append(QuickTip(
                tip_id="expand_content",
                description="내용을 조금 더 추가하면 dwell time 증가 예상",
                impact="+10%",
                target_score="longevity",
                selectable=False,  # Needs user input
            ))
        elif features.char_count > 250:
            tips.append(QuickTip(
                tip_id="shorten_content",
                description="내용을 간결하게 줄이면 완독률 상승 예상",
                impact="+5%",
                target_score="quality",
                selectable=False,  # Needs user decision
            ))

        if features.hashtag_count == 0:
            tips.append(QuickTip(
                tip_id="add_hashtag",
                description="관련 해시태그 1-2개를 추가해보세요",
                impact="+5%",
                target_score="reach",
            ))
        elif features.hashtag_count > 3:
            tips.append(QuickTip(
                tip_id="reduce_hashtags",
                description="해시태그를 3개 이하로 줄이면 품질 점수 상승",
                impact="+3%",
                target_score="quality",
                selectable=False,
            ))

        if not features.has_cta:
            tips.append(QuickTip(
                tip_id="add_cta",
                description="CTA를 추가하면 참여도 +10% 예상",
                impact="+10%",
                target_score="engagement",
            ))

        return tips[:5]  # Return max 5 tips
