"""Score prediction service for posts."""

import asyncio
import re
from dataclasses import dataclass, field
from functools import lru_cache
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
from src.services.x_algorithm_advisor import XAlgorithmAdvisor
from src.db.supabase_client import SupabaseCache

# Compiled regex patterns for faster language detection
_KOREAN_PATTERN = re.compile(r'[\uac00-\ud7af]')
_JAPANESE_PATTERN = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
_CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]')

# Language detection cache
_language_cache: dict[int, str] = {}


def detect_language(text: str) -> str:
    """Detect language from text content (with caching)."""
    if not text:
        return "en"

    # Check cache first using text hash
    text_hash = hash(text[:100])  # Only hash first 100 chars for speed
    if text_hash in _language_cache:
        return _language_cache[text_hash]

    # Korean characters (Hangul)
    if _KOREAN_PATTERN.search(text):
        result = "ko"
    # Japanese (Hiragana, Katakana)
    elif _JAPANESE_PATTERN.search(text):
        result = "ja"
    # Chinese characters (CJK)
    elif _CHINESE_PATTERN.search(text):
        result = "zh"
    else:
        result = "en"

    # Cache result (limit cache size to 1000 entries)
    if len(_language_cache) < 1000:
        _language_cache[text_hash] = result

    return result


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
        self.advisor = XAlgorithmAdvisor()
        self.cache = SupabaseCache()
        self._profile_cache: dict[str, any] = {}

    async def predict(
        self,
        username: str,
        content: str,
        post_type: Literal["original", "reply", "quote", "thread"] = "original",
        target_post_url: Optional[str] = None,
        media_type: Optional[Literal["image", "video", "gif"]] = None,
        target_language: Optional[Literal["ko", "en", "ja", "zh"]] = None,
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
        # Extract post features (sync, fast)
        post_features = extract_post_features(
            content,
            media_type=media_type,
            is_quote=(post_type == "quote"),
        )

        # Detect language once upfront
        detected_language = target_language or detect_language(content)

        # PARALLEL EXECUTION: Fetch profile and context simultaneously
        if post_type in ("reply", "quote") and target_post_url:
            # Run both tasks in parallel
            profile_task = self._get_profile_features(username)
            context_task = self._analyze_context(target_post_url)
            profile_features, (context, context_boost) = await asyncio.gather(
                profile_task, context_task
            )
        else:
            # Only fetch profile
            profile_features = await self._get_profile_features(username)
            context = None
            context_boost = None

        # Calculate scores (sync, fast)
        scores, probs = self.scorer.analyze_post(
            post_features,
            profile_features,
            context_boost,
        )

        # Generate quick tips using X Algorithm Advisor
        target_content = context.target_post.content if context else None
        if target_content and not target_language:
            detected_language = detect_language(target_content)

        quick_tips = await self._generate_algorithm_tips(
            content=content,
            scores=scores,
            features=post_features,
            post_type=post_type,
            target_content=target_content,
            target_language=detected_language,
        )

        return PostAnalysisResult(
            scores=scores,
            probabilities=probs,
            features=post_features,
            quick_tips=quick_tips,
            context=context,
        )

    async def _get_profile_features(self, username: str):
        """Get profile features (with multi-layer caching)."""
        # Layer 1: In-memory cache (fastest)
        if username in self._profile_cache:
            return self._profile_cache[username]

        # Layer 2: Supabase cache (persistent, 1-hour TTL)
        try:
            cached = await self.cache.get_profile_cache(username)
            if cached and cached.get("profile_data"):
                from src.engine.feature_extractor import ProfileFeatures
                features = ProfileFeatures(**cached["profile_data"])
                self._profile_cache[username] = features
                return features
        except Exception:
            pass  # Continue to API call if cache fails

        # Layer 3: Sela API (slowest, reduced from 20 to 10 posts)
        response = await self.client.get_twitter_profile(username, post_count=10)

        if response.success and response.profile:
            features = extract_profile_features(response.profile)
            self._profile_cache[username] = features

            # Save to Supabase cache (async, don't wait)
            try:
                asyncio.create_task(
                    self.cache.set_profile_cache(username, features.__dict__)
                )
            except Exception:
                pass

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

    async def _generate_algorithm_tips(
        self,
        content: str,
        scores: PentagonScores,
        features: PostFeatures,
        post_type: str = "original",
        target_content: Optional[str] = None,
        target_language: Optional[str] = None,
    ) -> list[QuickTip]:
        """Generate X Algorithm-based improvement tips using Claude AI."""
        try:
            # Language priority: 1) explicit target_language, 2) target_content, 3) user content
            if target_language:
                language = target_language
            elif target_content:
                language = detect_language(target_content)
            else:
                language = detect_language(content)

            result = await self.advisor.analyze_and_suggest(
                content=content,
                current_scores=scores,
                post_features=features,
                post_type=post_type,
                target_post_content=target_content,
                language=language,
            )

            tips = []
            for i, suggestion in enumerate(result.get("suggestions", [])[:5]):
                # Determine if tip is auto-applicable
                action = suggestion.get("action", "")
                selectable = self._is_tip_selectable(action)

                tips.append(QuickTip(
                    tip_id=f"algo_tip_{i}",
                    description=f"{action} ({suggestion.get('reason', '')})",
                    impact=suggestion.get("improvement", "+0%"),
                    target_score=suggestion.get("target_score", "engagement"),
                    selectable=selectable,
                ))

            # Store optimized content for later use
            self._last_optimized_content = result.get("optimized_content", content)
            self._last_score_predictions = result.get("score_predictions", {})

            return tips if tips else self._generate_fallback_tips(features, scores, language)

        except Exception as e:
            print(f"Algorithm tips generation error: {e}")
            # Detect language for fallback
            if target_content:
                language = detect_language(target_content)
            else:
                language = detect_language(content)
            return self._generate_fallback_tips(features, scores, language)

    def _is_tip_selectable(self, action: str) -> bool:
        """Determine if a tip can be auto-applied."""
        # Tips that require user input or external action
        non_selectable_keywords = [
            "이미지", "영상", "미디어", "사진", "동영상",
            "image", "video", "media", "photo",
        ]
        return not any(keyword in action.lower() for keyword in non_selectable_keywords)

    def _generate_fallback_tips(
        self,
        features: PostFeatures,
        scores: PentagonScores,
        language: str = "ko",
    ) -> list[QuickTip]:
        """Generate fallback tips when AI is unavailable."""
        tips = []

        # Multilingual tip messages
        messages = {
            "ko": {
                "add_emoji": "이모지를 추가하면 engagement +8% 예상 (p_favorite 확률 상승)",
                "add_question": "질문 형태로 바꾸면 reply율 +15% 예상 (p_reply 확률 상승)",
                "add_media": "이미지를 추가하면 reach +20% 예상 (photo_expand 확률 상승)",
                "expand_content": "내용을 더 추가하면 dwell time 증가 예상 (p_dwell 확률 상승)",
                "shorten_content": "내용을 간결하게 줄이면 완독률 상승 (p_not_interested 감소)",
                "add_hashtag": "관련 해시태그 1-2개 추가 (p_click 확률 상승)",
                "add_cta": "CTA를 추가하면 참여도 +10% 예상 (p_reply, p_repost 상승)",
            },
            "en": {
                "add_emoji": "Add emojis for +8% engagement (increases p_favorite)",
                "add_question": "Add a question for +15% reply rate (increases p_reply)",
                "add_media": "Add an image for +20% reach (increases photo_expand)",
                "expand_content": "Add more content to increase dwell time (increases p_dwell)",
                "shorten_content": "Make it more concise to increase completion rate (decreases p_not_interested)",
                "add_hashtag": "Add 1-2 relevant hashtags (increases p_click)",
                "add_cta": "Add a CTA for +10% engagement (increases p_reply, p_repost)",
            },
            "ja": {
                "add_emoji": "絵文字を追加すると+8%エンゲージメント向上 (p_favorite上昇)",
                "add_question": "質問形式に変えると+15%リプライ率向上 (p_reply上昇)",
                "add_media": "画像を追加すると+20%リーチ向上 (photo_expand上昇)",
                "expand_content": "内容を追加するとdwell time増加 (p_dwell上昇)",
                "shorten_content": "簡潔にすると完読率向上 (p_not_interested減少)",
                "add_hashtag": "関連ハッシュタグを1-2個追加 (p_click上昇)",
                "add_cta": "CTAを追加すると+10%エンゲージメント向上 (p_reply, p_repost上昇)",
            },
            "zh": {
                "add_emoji": "添加表情符号可提升8%互动率 (提高p_favorite)",
                "add_question": "添加问题可提升15%回复率 (提高p_reply)",
                "add_media": "添加图片可提升20%触达率 (提高photo_expand)",
                "expand_content": "增加内容可提升停留时间 (提高p_dwell)",
                "shorten_content": "简洁表达可提升完读率 (降低p_not_interested)",
                "add_hashtag": "添加1-2个相关标签 (提高p_click)",
                "add_cta": "添加行动号召可提升10%互动率 (提高p_reply, p_repost)",
            },
        }

        # Use English as fallback if language not found
        msg = messages.get(language, messages["en"])

        if not features.has_emoji:
            tips.append(QuickTip(
                tip_id="add_emoji",
                description=msg["add_emoji"],
                impact="+8%",
                target_score="engagement",
            ))

        if not features.has_question:
            tips.append(QuickTip(
                tip_id="add_question",
                description=msg["add_question"],
                impact="+15%",
                target_score="engagement",
            ))

        if not features.has_media:
            tips.append(QuickTip(
                tip_id="add_media_hint",
                description=msg["add_media"],
                impact="+20%",
                target_score="reach",
                selectable=False,
            ))

        if features.char_count < 50:
            tips.append(QuickTip(
                tip_id="expand_content",
                description=msg["expand_content"],
                impact="+10%",
                target_score="longevity",
                selectable=False,
            ))
        elif features.char_count > 250:
            tips.append(QuickTip(
                tip_id="shorten_content",
                description=msg["shorten_content"],
                impact="+5%",
                target_score="quality",
                selectable=False,
            ))

        if features.hashtag_count == 0:
            tips.append(QuickTip(
                tip_id="add_hashtag",
                description=msg["add_hashtag"],
                impact="+5%",
                target_score="reach",
            ))

        if not features.has_cta:
            tips.append(QuickTip(
                tip_id="add_cta",
                description=msg["add_cta"],
                impact="+10%",
                target_score="engagement",
            ))

        return tips[:5]
