"""Content optimization service for posts."""

import re
import random
from datetime import datetime, timezone
from typing import Literal, Optional

import anthropic

from src.config import get_settings
from src.services.sela_api_client import SelaAPIClient


# Tip application templates (transform functions accept content and optional language)
TIP_TEMPLATES = {
    "add_emoji": {
        "description": "이모지 추가",
        "impact": "+8% 참여도",
        "transform": lambda content, lang="ko": _add_emoji(content),
    },
    "add_question": {
        "description": "질문 형태로 변환",
        "impact": "+15% 참여도",
        "transform": lambda content, lang="ko": _add_question(content, lang),
    },
    "add_hashtag": {
        "description": "해시태그 추가",
        "impact": "+5% 도달률",
        "transform": lambda content, lang="ko": _add_hashtag(content),
    },
    "add_cta": {
        "description": "CTA 추가",
        "impact": "+10% 참여도",
        "transform": lambda content, lang="ko": _add_cta(content, lang),
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

# Question suffixes by language
QUESTION_SUFFIXES = {
    "ko": [
        " 여러분은 어떻게 생각하세요?",
        " 여러분의 의견은요?",
        " 어떻게 생각하시나요?",
        " 공감하시나요?",
    ],
    "en": [
        " What do you think?",
        " Any thoughts?",
        " Do you agree?",
        " What's your take?",
    ],
    "ja": [
        " 皆さんはどう思いますか？",
        " ご意見は？",
        " 共感できますか？",
    ],
    "zh": [
        " 大家怎么看？",
        " 你们觉得呢？",
        " 同意吗？",
    ],
}

# CTA phrases by language
CTA_PHRASES = {
    "ko": [
        " 의견 남겨주세요! 💬",
        " 공감하시면 좋아요 부탁드려요 ❤️",
        " 생각 공유해주세요!",
        " 댓글로 알려주세요 👇",
    ],
    "en": [
        " Share your thoughts! 💬",
        " Like if you agree! ❤️",
        " Let me know in the comments 👇",
        " Drop your opinion below!",
    ],
    "ja": [
        " コメントお待ちしています! 💬",
        " 共感したらいいねお願いします ❤️",
        " 意見を聞かせてください 👇",
    ],
    "zh": [
        " 欢迎留言! 💬",
        " 同意的话请点赞 ❤️",
        " 评论区见 👇",
    ],
}


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


def _add_question(content: str, language: str = "ko") -> str:
    """Transform content into question form."""
    # Check if already has question
    if "?" in content or "？" in content:
        return content

    # Remove trailing punctuation
    content = content.rstrip(".。")

    # Add question suffix based on language
    suffixes = QUESTION_SUFFIXES.get(language, QUESTION_SUFFIXES["en"])
    suffix = random.choice(suffixes)
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


def _add_cta(content: str, language: str = "ko") -> str:
    """Add call-to-action to content."""
    # Check if already has CTA-like phrases (multi-language)
    cta_indicators = ["남겨", "부탁", "공유", "댓글", "share", "comment", "let me know", "コメント", "留言"]
    if any(cta_word.lower() in content.lower() for cta_word in cta_indicators):
        return content

    phrases = CTA_PHRASES.get(language, CTA_PHRASES["en"])
    cta = random.choice(phrases)
    return content + cta


class ContentOptimizer:
    """Service for optimizing post content."""

    def __init__(self):
        self.client = SelaAPIClient()
        settings = get_settings()
        self.anthropic_client = (
            anthropic.Anthropic(api_key=settings.anthropic_api_key)
            if settings.anthropic_api_key
            else None
        )

    async def apply_tips(
        self,
        username: str,
        original_content: str,
        selected_tips: list[str],
        language: str = "ko",
    ) -> dict:
        """Apply selected tips to generate optimized content.

        Args:
            username: User's username
            original_content: Original post content
            selected_tips: List of tip IDs to apply
            language: Target language for suggestions (ko, en, ja, zh)
        """

        # Limit to 3 tips
        selected_tips = selected_tips[:3]

        suggested_content = original_content
        applied_tips = []
        improvements = {}

        for tip_id in selected_tips:
            if tip_id in TIP_TEMPLATES:
                template = TIP_TEMPLATES[tip_id]
                suggested_content = template["transform"](suggested_content, language)
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

    async def polish(
        self,
        content: str,
        polish_type: Literal["grammar", "twitter", "280char"],
        language: Optional[str] = None,
    ) -> dict:
        """Polish text using Claude API.

        Args:
            content: Original content to polish
            polish_type: Type of polish to apply
                - grammar: Fix grammar while maintaining tone
                - twitter: Convert to Twitter-style casual tone
                - 280char: Compress to 280 characters while keeping message
            language: Optional language code (auto-detected if not provided)
        """
        if not self.anthropic_client:
            # Fallback without API: minimal transformations
            return self._polish_fallback(content, polish_type)

        # Build prompt based on polish type
        if polish_type == "grammar":
            system_prompt = """You are a text editor. Fix grammar, spelling, and punctuation errors while maintaining the original tone and style. Do not change the meaning or add unnecessary content. Keep it natural and authentic."""
            user_prompt = f"""Polish this text by fixing grammar errors. Maintain the original tone and style. Only fix what's wrong:

Text: {content}

Return ONLY the polished text, nothing else."""

        elif polish_type == "twitter":
            system_prompt = """You are a Twitter/X content expert. Transform text into engaging Twitter-style content: short, impactful sentences with appropriate emojis and hashtags. Keep it casual and engaging."""
            user_prompt = f"""Transform this into Twitter-style content. Make it short, punchy, and engaging. Add emojis and hashtags where appropriate:

Text: {content}

Return ONLY the transformed text, nothing else."""

        elif polish_type == "280char":
            system_prompt = """You are a concise writer. Compress text to fit within 280 characters while preserving the core message. Remove unnecessary words but keep the meaning intact."""
            user_prompt = f"""Compress this text to 280 characters or less. Keep the core message intact:

Text: {content}
Current length: {len(content)} characters

Return ONLY the compressed text, nothing else."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                system=system_prompt,
            )

            polished_content = message.content[0].text.strip()

            # Detect language if not provided
            detected_language = language or self._detect_language(content)

            # Generate changes description
            changes = self._describe_changes(content, polished_content, polish_type)

            return {
                "original_content": content,
                "polished_content": polished_content,
                "polish_type": polish_type,
                "language_detected": detected_language,
                "changes": changes,
                "character_count": {
                    "original": len(content),
                    "polished": len(polished_content),
                },
            }

        except Exception as e:
            # Fallback on API error
            return self._polish_fallback(content, polish_type)

    def _polish_fallback(
        self, content: str, polish_type: Literal["grammar", "twitter", "280char"]
    ) -> dict:
        """Fallback polish without API."""
        polished_content = content

        if polish_type == "twitter":
            # Add emoji if not present
            polished_content = _add_emoji(content)
        elif polish_type == "280char":
            # Simple truncation
            if len(content) > 280:
                polished_content = content[:277] + "..."

        return {
            "original_content": content,
            "polished_content": polished_content,
            "polish_type": polish_type,
            "language_detected": self._detect_language(content),
            "changes": [
                {"type": "fallback", "description": "API not available, minimal changes applied"}
            ],
            "character_count": {
                "original": len(content),
                "polished": len(polished_content),
            },
        }

    def _detect_language(self, content: str) -> str:
        """Simple language detection based on character ranges."""
        # Check for Korean characters
        if re.search(r"[\uac00-\ud7af]", content):
            return "ko"
        # Check for Japanese
        if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", content):
            return "ja"
        # Check for Chinese
        if re.search(r"[\u4e00-\u9fff]", content):
            return "zh"
        # Default to English
        return "en"

    def _describe_changes(
        self, original: str, polished: str, polish_type: str
    ) -> list[dict]:
        """Describe what changes were made."""
        changes = []

        # Check character count difference
        len_diff = len(polished) - len(original)
        if abs(len_diff) > 5:
            if len_diff < 0:
                changes.append({
                    "type": "compression",
                    "description": f"Reduced by {abs(len_diff)} characters",
                })
            else:
                changes.append({
                    "type": "expansion",
                    "description": f"Added {len_diff} characters",
                })

        # Check for emoji additions
        orig_emoji = len(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", original))
        polished_emoji = len(re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", polished))
        if polished_emoji > orig_emoji:
            changes.append({
                "type": "added_emoji",
                "description": f"Added {polished_emoji - orig_emoji} emoji(s)",
            })

        # Check for hashtag additions
        orig_tags = len(re.findall(r"#\w+", original))
        polished_tags = len(re.findall(r"#\w+", polished))
        if polished_tags > orig_tags:
            changes.append({
                "type": "added_hashtags",
                "description": f"Added {polished_tags - orig_tags} hashtag(s)",
            })

        # Default description based on type
        if not changes:
            if polish_type == "grammar":
                changes.append({
                    "type": "grammar_fix",
                    "description": "Grammar and style improvements applied",
                })
            elif polish_type == "twitter":
                changes.append({
                    "type": "style_change",
                    "description": "Converted to Twitter-friendly style",
                })
            elif polish_type == "280char":
                changes.append({
                    "type": "compression",
                    "description": "Compressed to fit 280 character limit",
                })

        return changes
