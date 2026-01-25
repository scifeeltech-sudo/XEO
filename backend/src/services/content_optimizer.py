"""Content optimization service for posts."""

import re
import random
from datetime import datetime, timezone
from typing import Literal, Optional

from src.services.sela_api_client import SelaAPIClient


# Tip application templates
TIP_TEMPLATES = {
    "add_emoji": {
        "description": "이모지 추가",
        "impact": "+8% 참여도",
        "transform": lambda content: _add_emoji(content),
    },
    "add_question": {
        "description": "질문 형태로 변환",
        "impact": "+15% 참여도",
        "transform": lambda content: _add_question(content),
    },
    "add_hashtag": {
        "description": "해시태그 추가",
        "impact": "+5% 도달률",
        "transform": lambda content: _add_hashtag(content),
    },
    "add_cta": {
        "description": "CTA 추가",
        "impact": "+10% 참여도",
        "transform": lambda content: _add_cta(content),
    },
}

# Korean emojis by category
EMOJIS = {
    "positive": ["😊", "🙂", "👍", "✨", "💯", "🎉", "❤️", "🔥"],
    "thinking": ["🤔", "💭", "🧐", "💡"],
    "weather": ["☀️", "🌤️", "🌈", "🌸"],
    "general": ["✅", "📌", "💪", "🚀", "⭐"],
}

# Common Korean hashtags
HASHTAGS = {
    "일상": ["#일상", "#데일리", "#daily"],
    "생각": ["#생각", "#thoughts", "#인사이트"],
    "tech": ["#테크", "#기술", "#AI", "#개발"],
    "default": ["#일상", "#오늘"],
}

# Question suffixes
QUESTION_SUFFIXES = [
    " 여러분은 어떻게 생각하세요?",
    " 여러분의 의견은요?",
    " 어떻게 생각하시나요?",
    " 공감하시나요?",
]

# CTA phrases
CTA_PHRASES = [
    " 의견 남겨주세요! 💬",
    " 공감하시면 좋아요 부탁드려요 ❤️",
    " 생각 공유해주세요!",
    " 댓글로 알려주세요 👇",
]


def _add_emoji(content: str) -> str:
    """Add relevant emoji to content."""
    # Check if already has emoji
    if re.search(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", content):
        return content

    # Select emoji based on content
    if any(word in content.lower() for word in ["좋", "행복", "기쁘"]):
        emoji = random.choice(EMOJIS["positive"])
    elif any(word in content.lower() for word in ["생각", "궁금", "왜"]):
        emoji = random.choice(EMOJIS["thinking"])
    elif any(word in content.lower() for word in ["날씨", "햇살", "비"]):
        emoji = random.choice(EMOJIS["weather"])
    else:
        emoji = random.choice(EMOJIS["general"])

    # Add emoji at the end of first sentence or content
    if "." in content:
        parts = content.split(".", 1)
        return f"{parts[0]} {emoji}.{parts[1]}" if parts[1] else f"{parts[0]} {emoji}"
    return f"{content} {emoji}"


def _add_question(content: str) -> str:
    """Transform content into question form."""
    # Check if already has question
    if "?" in content:
        return content

    # Remove trailing punctuation
    content = content.rstrip(".")

    # Add question suffix
    suffix = random.choice(QUESTION_SUFFIXES)
    return content + suffix


def _add_hashtag(content: str) -> str:
    """Add relevant hashtags to content."""
    # Check if already has hashtags
    if "#" in content:
        return content

    # Select hashtags based on content
    if any(word in content.lower() for word in ["ai", "개발", "코딩", "tech"]):
        tags = random.sample(HASHTAGS["tech"], min(2, len(HASHTAGS["tech"])))
    elif any(word in content.lower() for word in ["생각", "느낌", "마음"]):
        tags = random.sample(HASHTAGS["생각"], min(2, len(HASHTAGS["생각"])))
    else:
        tags = HASHTAGS["default"]

    return f"{content} {' '.join(tags)}"


def _add_cta(content: str) -> str:
    """Add call-to-action to content."""
    # Check if already has CTA-like phrases
    if any(cta_word in content for cta_word in ["남겨", "부탁", "공유", "댓글"]):
        return content

    cta = random.choice(CTA_PHRASES)
    return content + cta


class ContentOptimizer:
    """Service for optimizing post content."""

    def __init__(self):
        self.client = SelaAPIClient()

    async def apply_tips(
        self,
        username: str,
        original_content: str,
        selected_tips: list[str],
    ) -> dict:
        """Apply selected tips to generate optimized content."""

        # Limit to 3 tips
        selected_tips = selected_tips[:3]

        suggested_content = original_content
        applied_tips = []
        improvements = {}

        for tip_id in selected_tips:
            if tip_id in TIP_TEMPLATES:
                template = TIP_TEMPLATES[tip_id]
                suggested_content = template["transform"](suggested_content)
                applied_tips.append({
                    "tip_id": tip_id,
                    "description": template["description"],
                    "impact": template["impact"],
                })

                # Track improvements by score type
                if "참여도" in template["impact"]:
                    current = improvements.get("engagement", 0)
                    match = re.search(r"\+(\d+)%", template["impact"])
                    if match:
                        improvements["engagement"] = current + int(match.group(1))
                elif "도달률" in template["impact"]:
                    current = improvements.get("reach", 0)
                    match = re.search(r"\+(\d+)%", template["impact"])
                    if match:
                        improvements["reach"] = current + int(match.group(1))

        predicted_improvement = {
            k: f"+{v}%" for k, v in improvements.items()
        }

        return {
            "original_content": original_content,
            "suggested_content": suggested_content,
            "applied_tips": applied_tips,
            "predicted_improvement": predicted_improvement,
        }

    async def get_post_context(self, url: str) -> Optional[dict]:
        """Get context information for a target post."""

        tweet = await self.client.get_post_context(url)
        if not tweet:
            return None

        # Calculate age
        age_minutes = 0
        if tweet.posted_at:
            age_minutes = int(
                (datetime.now(timezone.utc) - tweet.posted_at).total_seconds() / 60
            )

        # Determine freshness
        if age_minutes < 30:
            freshness = "very_fresh"
        elif age_minutes < 60:
            freshness = "fresh"
        elif age_minutes < 360:
            freshness = "moderate"
        else:
            freshness = "old"

        # Determine virality status based on engagement rate
        engagement_rate = tweet.engagement_rate
        if engagement_rate > 0.05:
            virality_status = "trending"
        elif engagement_rate > 0.02:
            virality_status = "growing"
        elif engagement_rate > 0.01:
            virality_status = "stable"
        else:
            virality_status = "declining"

        # Determine reply saturation
        if tweet.replies_count < 100:
            reply_saturation = "low"
        elif tweet.replies_count < 500:
            reply_saturation = "medium"
        elif tweet.replies_count < 2000:
            reply_saturation = "high"
        else:
            reply_saturation = "very_high"

        # Calculate opportunity score
        account_reach = min(100, int(tweet.views_count / 100000))
        timing = 100 if freshness == "very_fresh" else (80 if freshness == "fresh" else 50)
        competition = 100 - min(80, int(tweet.replies_count / 50))
        topic_engagement = int(tweet.engagement_rate * 2000)

        overall = int((account_reach + timing + competition + topic_engagement) / 4)

        # Generate tips
        tips = []
        if freshness in ("very_fresh", "fresh"):
            tips.append(f"🕐 포스트가 {age_minutes}분 전에 작성되어 답글 달기 최적의 타이밍입니다")
        if virality_status == "trending":
            tips.append("🔥 현재 트렌딩 중인 포스트입니다 - 노출 기회가 높습니다")
        if reply_saturation in ("high", "very_high"):
            tips.append(f"💬 이미 {tweet.replies_count:,} 답글이 있어 차별화된 관점이 필요합니다")
        if tweet.views_count > 1000000:
            tips.append("🎯 대형 계정의 포스트로 높은 노출이 예상됩니다")

        return {
            "post_id": tweet.tweet_id,
            "post_url": tweet.full_url,
            "author": {
                "username": tweet.username,
                "display_name": None,
                "followers_count": 0,  # Not available from tweet data
                "verified": False,
            },
            "content": {
                "text": tweet.content,
                "media": [{"type": "image", "url": img} for img in tweet.images],
                "hashtags": re.findall(r"#(\w+)", tweet.content),
            },
            "metrics": {
                "likes": tweet.likes_count,
                "reposts": tweet.retweets_count,
                "replies": tweet.replies_count,
                "quotes": 0,
                "views": tweet.views_count,
            },
            "created_at": tweet.posted_at.isoformat() if tweet.posted_at else None,
            "analysis": {
                "age_minutes": age_minutes,
                "freshness": freshness,
                "virality_status": virality_status,
                "reply_saturation": reply_saturation,
            },
            "opportunity_score": {
                "overall": overall,
                "factors": {
                    "account_reach": account_reach,
                    "timing": timing,
                    "competition": competition,
                    "topic_engagement": topic_engagement,
                },
            },
            "tips": tips,
        }

    async def optimize(
        self,
        username: str,
        content: str,
        target_score: Literal["reach", "engagement", "virality", "quality", "longevity"],
        style: Literal["conservative", "balanced", "aggressive"] = "balanced",
    ) -> dict:
        """Generate optimized versions of content."""

        versions = []

        # Conservative version - minimal changes
        conservative_content = content
        conservative_changes = []

        if target_score == "engagement":
            if "?" not in content:
                conservative_content = _add_question(content)
                conservative_changes.append({"type": "added_question", "impact": "+12% engagement"})
        elif target_score == "reach":
            if "#" not in content:
                conservative_content = _add_hashtag(content)
                conservative_changes.append({"type": "added_hashtag", "impact": "+5% reach"})

        versions.append({
            "content": conservative_content,
            "style": "conservative",
            "predicted_scores": {
                "reach": 65.0,
                "engagement": 70.0 if target_score == "engagement" else 55.0,
                "virality": 40.0,
                "quality": 75.0,
                "longevity": 50.0,
            },
            "changes": conservative_changes,
        })

        # Aggressive version - multiple changes
        aggressive_content = content
        aggressive_changes = []

        # Apply multiple transformations
        aggressive_content = _add_emoji(aggressive_content)
        aggressive_changes.append({"type": "added_emoji", "impact": "+8% engagement"})

        if target_score in ("engagement", "virality"):
            aggressive_content = _add_question(aggressive_content)
            aggressive_changes.append({"type": "added_question", "impact": "+15% engagement"})

        aggressive_content = _add_cta(aggressive_content)
        aggressive_changes.append({"type": "added_cta", "impact": "+10% engagement"})

        if "#" not in content:
            aggressive_content = _add_hashtag(aggressive_content)
            aggressive_changes.append({"type": "added_hashtag", "impact": "+5% reach"})

        versions.append({
            "content": aggressive_content,
            "style": "aggressive",
            "predicted_scores": {
                "reach": 75.0,
                "engagement": 85.0 if target_score == "engagement" else 70.0,
                "virality": 55.0,
                "quality": 70.0,  # Slightly lower quality due to more additions
                "longevity": 55.0,
            },
            "changes": aggressive_changes,
        })

        return {
            "original_content": content,
            "optimized_versions": versions,
        }
