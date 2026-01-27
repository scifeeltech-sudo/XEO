"""Content optimization service for posts."""

import re
import random
from datetime import datetime, timezone
from typing import Literal, Optional

import anthropic

from src.config import get_settings
from src.services.sela_api_client import SelaAPIClient
from src.services.x_algorithm_advisor import X_ALGORITHM_KNOWLEDGE


# Tip application templates (transform functions accept content and optional language)
TIP_TEMPLATES = {
    "add_emoji": {
        "description": "Add emoji",
        "impact": "+8% engagement",
        "transform": lambda content, lang="en": _add_emoji(content),
    },
    "add_question": {
        "description": "Convert to question format",
        "impact": "+15% engagement",
        "transform": lambda content, lang="en": _add_question(content, lang),
    },
    "add_hashtag": {
        "description": "Add hashtags",
        "impact": "+5% reach",
        "transform": lambda content, lang="en": _add_hashtag(content),
    },
    "add_cta": {
        "description": "Add CTA",
        "impact": "+10% engagement",
        "transform": lambda content, lang="en": _add_cta(content, lang),
    },
}

# Korean emojis by category
EMOJIS = {
    "positive": ["😊", "🙂", "👍", "✨", "💯", "🎉", "❤️", "🔥"],
    "thinking": ["🤔", "💭", "🧐", "💡"],
    "weather": ["☀️", "🌤️", "🌈", "🌸"],
    "general": ["✅", "📌", "💪", "🚀", "⭐"],
}

# Common hashtags
HASHTAGS = {
    "daily": ["#daily", "#life", "#today"],
    "thoughts": ["#thoughts", "#opinion", "#insights"],
    "tech": ["#tech", "#technology", "#AI", "#coding"],
    "default": ["#thoughts", "#daily"],
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
    if any(word in content.lower() for word in ["ai", "code", "coding", "tech", "dev"]):
        tags = random.sample(HASHTAGS["tech"], min(2, len(HASHTAGS["tech"])))
    elif any(word in content.lower() for word in ["think", "thought", "feel", "opinion"]):
        tags = random.sample(HASHTAGS["thoughts"], min(2, len(HASHTAGS["thoughts"])))
    else:
        tags = HASHTAGS["default"]

    return f"{content} {' '.join(tags)}"


def _add_cta(content: str, language: str = "en") -> str:
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
        selected_tips: list[dict],
        language: str = "en",
    ) -> dict:
        """Apply selected tips to generate optimized content using Claude AI.

        Args:
            username: User's username
            original_content: Original post content
            selected_tips: List of dicts with tip_id and description
            language: Target language for suggestions (ko, en, ja, zh)
        """
        # Limit to 3 tips
        selected_tips = selected_tips[:3]

        # If Claude is available, use AI-powered optimization
        if self.anthropic_client and selected_tips:
            result = await self._apply_tips_with_ai(
                original_content, selected_tips, language
            )
            if result:
                return result

        # Fallback to rule-based transformation
        return self._apply_tips_fallback(original_content, selected_tips, language)

    async def _apply_tips_with_ai(
        self,
        content: str,
        tips: list[dict],
        language: str,
    ) -> Optional[dict]:
        """Apply tips using Claude AI with X algorithm knowledge."""
        lang_names = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target_lang = lang_names.get(language, "Korean")

        # Build tip descriptions from the dict format
        tip_descriptions = []
        for tip in tips:
            tip_id = tip.get("tip_id", "")
            description = tip.get("description", "")
            if tip_id in TIP_TEMPLATES:
                tip_descriptions.append(TIP_TEMPLATES[tip_id]["description"])
            elif description:
                # Use the actual description from the tip
                tip_descriptions.append(description)
            else:
                tip_descriptions.append(tip_id)

        system_prompt = f"""{X_ALGORITHM_KNOWLEDGE}

You are an X (Twitter) content optimization expert. Your task is to rewrite content to maximize engagement based on the X algorithm while applying the requested improvements.

RULES:
1. Output MUST be in {target_lang}
2. Keep the original message intent intact
3. Apply all requested improvements naturally
4. Make the content feel authentic, not robotic
5. Optimize for the X algorithm factors mentioned in the knowledge base
6. Return ONLY the optimized content, no explanations"""

        user_prompt = f"""Rewrite this content applying these improvements:

**Original Content:**
{content}

**Improvements to Apply:**
{chr(10).join(f"- {tip}" for tip in tip_descriptions)}

**Target Language:** {target_lang}

Return ONLY the optimized content:"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            suggested_content = message.content[0].text.strip()

            # Build applied tips response
            applied_tips = []
            improvements = {}

            for tip in tips:
                tip_id = tip.get("tip_id", "")
                description = tip.get("description", "")

                if tip_id in TIP_TEMPLATES:
                    template = TIP_TEMPLATES[tip_id]
                    applied_tips.append({
                        "tip_id": tip_id,
                        "description": template["description"],
                        "impact": template["impact"],
                    })
                    # Track improvements
                    if "engagement" in template["impact"]:
                        match = re.search(r"\+(\d+)%", template["impact"])
                        if match:
                            improvements["engagement"] = improvements.get("engagement", 0) + int(match.group(1))
                    elif "reach" in template["impact"]:
                        match = re.search(r"\+(\d+)%", template["impact"])
                        if match:
                            improvements["reach"] = improvements.get("reach", 0) + int(match.group(1))
                else:
                    # Algorithm-generated tip - use the actual description
                    applied_tips.append({
                        "tip_id": tip_id,
                        "description": description or "X algorithm-based optimization",
                        "impact": "+10% (AI estimated)",
                    })
                    improvements["engagement"] = improvements.get("engagement", 0) + 10

            return {
                "original_content": content,
                "suggested_content": suggested_content,
                "applied_tips": applied_tips,
                "predicted_improvement": {k: f"+{v}%" for k, v in improvements.items()},
            }

        except Exception as e:
            print(f"Claude API error in apply_tips: {e}")
            return None

    def _apply_tips_fallback(
        self,
        content: str,
        tips: list[dict],
        language: str,
    ) -> dict:
        """Fallback rule-based tip application."""
        suggested_content = content
        applied_tips = []
        improvements = {}

        for tip in tips:
            tip_id = tip.get("tip_id", "")
            description = tip.get("description", "")

            if tip_id in TIP_TEMPLATES:
                template = TIP_TEMPLATES[tip_id]
                suggested_content = template["transform"](suggested_content, language)
                applied_tips.append({
                    "tip_id": tip_id,
                    "description": template["description"],
                    "impact": template["impact"],
                })

                if "engagement" in template["impact"]:
                    match = re.search(r"\+(\d+)%", template["impact"])
                    if match:
                        improvements["engagement"] = improvements.get("engagement", 0) + int(match.group(1))
                elif "reach" in template["impact"]:
                    match = re.search(r"\+(\d+)%", template["impact"])
                    if match:
                        improvements["reach"] = improvements.get("reach", 0) + int(match.group(1))
            else:
                # Algorithm-generated tip - just record it (no rule-based transform available)
                applied_tips.append({
                    "tip_id": tip_id,
                    "description": description or "Applied optimization",
                    "impact": "+10% (estimated)",
                })
                improvements["engagement"] = improvements.get("engagement", 0) + 10

        return {
            "original_content": content,
            "suggested_content": suggested_content,
            "applied_tips": applied_tips,
            "predicted_improvement": {k: f"+{v}%" for k, v in improvements.items()},
        }

    async def get_post_context(self, url: str) -> Optional[dict]:
        """Get context information for a target post."""

        tweet = await self.client.get_post_context(url)
        if not tweet:
            return None

        # Estimate followers from tweet views (no extra API call)
        followers_count = int(tweet.views_count / 10) if tweet.views_count > 0 else 0

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
            tips.append(f"🕐 Post was created {age_minutes} minutes ago - perfect timing for a reply")
        if virality_status == "trending":
            tips.append("🔥 This post is currently trending - high exposure opportunity")
        if reply_saturation in ("high", "very_high"):
            tips.append(f"💬 Already {tweet.replies_count:,} replies - bring a unique perspective to stand out")
        if tweet.views_count > 1000000:
            tips.append("🎯 Large account post - high exposure expected")

        return {
            "post_id": tweet.tweet_id,
            "post_url": tweet.full_url,
            "author": {
                "username": tweet.username,
                "display_name": None,
                "followers_count": followers_count,
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
        polish_type: Literal["grammar", "twitter", "280char", "translate_en", "translate_ko", "translate_zh"],
        language: Optional[str] = None,
        target_post_content: Optional[str] = None,
    ) -> dict:
        """Polish text using Claude API.

        Args:
            content: Original content to polish
            polish_type: Type of polish to apply
                - grammar: Match target post tone while fixing grammar
                - twitter: Convert to casual, impactful Twitter style
                - 280char: Compress to 280 characters while keeping message
                - translate_en: Translate to English
                - translate_ko: Translate to Korean
                - translate_zh: Translate to Chinese
            language: Target language code (ko, en, ja, zh)
            target_post_content: Content of target post (for tone matching)
        """
        # Detect language if not provided
        detected_language = language or self._detect_language(content)

        # Language names for prompts
        lang_names = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese"
        }
        target_lang_name = lang_names.get(detected_language, "English")

        if not self.anthropic_client:
            # Fallback without API: minimal transformations
            return self._polish_fallback(content, polish_type, detected_language)

        # Build prompt based on polish type
        if polish_type == "grammar":
            system_prompt = f"""You are a social media content editor. Your job is to:
1. Fix grammar, spelling, and punctuation errors
2. Make the text sound natural and intelligent (not awkward or dumb)
3. Maintain a similar tone to the reference post if provided
4. Output MUST be in {target_lang_name}
5. Keep the core message intact
6. Make it readable and understandable by humans"""

            target_context = ""
            if target_post_content:
                target_context = f"\nReference post tone to match:\n\"{target_post_content[:200]}\"\n"

            user_prompt = f"""Polish this text to sound natural and proper. Fix any grammar issues and make it sound intelligent.
{target_context}
Text to polish: {content}

IMPORTANT: Output must be in {target_lang_name}. Return ONLY the polished text, nothing else."""

        elif polish_type == "twitter":
            system_prompt = f"""You are a Twitter/X viral content creator. Your job is to:
1. Transform text into engaging, casual Twitter-style content
2. Make it short, punchy, and impactful
3. Add appropriate emojis (1-3 max, not excessive)
4. Use conversational, friendly tone
5. Output MUST be in {target_lang_name}
6. Keep it human-readable and understandable
7. Make people want to engage (like, reply, retweet)"""

            user_prompt = f"""Transform this into viral Twitter-style content. Make it casual, engaging, and impactful.

Text: {content}

IMPORTANT:
- Output must be in {target_lang_name}
- Keep under 280 characters if possible
- Make it sound like a real person, not a bot
Return ONLY the transformed text, nothing else."""

        elif polish_type == "280char":
            system_prompt = f"""You are a concise writer. Your job is to:
1. Compress text to fit within 280 characters
2. Preserve the core message and meaning
3. Remove unnecessary words but keep it natural
4. Output MUST be in {target_lang_name}
5. Keep it readable and understandable"""

            user_prompt = f"""Compress this text to 280 characters or less while keeping the core message.

Text: {content}
Current length: {len(content)} characters

IMPORTANT: Output must be in {target_lang_name}. Return ONLY the compressed text, nothing else."""

        elif polish_type == "translate_en":
            system_prompt = """You are a professional translator specializing in social media content.
Your job is to translate text to natural, fluent English while:
1. Preserving the original tone and style
2. Keeping it suitable for Twitter/X
3. Maintaining any emojis or formatting
4. Making it sound natural to native English speakers"""

            user_prompt = f"""Translate this social media post to English. Keep the same tone and style.

Text: {content}

Return ONLY the English translation, nothing else."""

        elif polish_type == "translate_ko":
            system_prompt = """You are a professional translator specializing in social media content.
Your job is to translate text to natural, fluent Korean while:
1. Preserving the original tone and style
2. Keeping it suitable for Twitter/X
3. Maintaining any emojis or formatting
4. Making it sound natural to native Korean speakers"""

            user_prompt = f"""Translate this social media post to Korean (한국어). Keep the same tone and style.

Text: {content}

Return ONLY the Korean translation, nothing else."""

        elif polish_type == "translate_zh":
            system_prompt = """You are a professional translator specializing in social media content.
Your job is to translate text to natural, fluent Simplified Chinese while:
1. Preserving the original tone and style
2. Keeping it suitable for Twitter/X (微博 style)
3. Maintaining any emojis or formatting
4. Making it sound natural to native Chinese speakers"""

            user_prompt = f"""Translate this social media post to Simplified Chinese (简体中文). Keep the same tone and style.

Text: {content}

Return ONLY the Chinese translation, nothing else."""

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
            return self._polish_fallback(content, polish_type, detected_language)

    def _polish_fallback(
        self,
        content: str,
        polish_type: Literal["grammar", "twitter", "280char"],
        language: str = "ko",
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
            "language_detected": language,
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

    async def generate_personalized_post(
        self,
        username: str,
        target_post_content: str,
        target_author: str,
        post_type: Literal["reply", "quote"],
        language: str = "en",
    ) -> Optional[dict]:
        """Generate a personalized post based on user's profile and style.

        Analyzes the user's recent posts to understand their:
        - Writing style and tone
        - Interests and topics
        - Emoji and hashtag usage patterns
        - Typical post length and structure

        If user profile is not available, generates a generic engaging post
        based only on the target post content.

        Args:
            username: User's X username to analyze
            target_post_content: Content of the target post being replied/quoted
            target_author: Author of the target post
            post_type: Type of post (reply or quote)
            language: Target language for the generated post

        Returns:
            dict with generated_content, user_style_analysis, and confidence score
        """
        if not self.anthropic_client:
            return None

        # Try to fetch user's profile and recent posts
        recent_posts = []
        has_profile = False

        try:
            response = await self.client.get_twitter_profile(username, post_count=10)
            if response.success and response.profile:
                recent_posts = [t.content for t in response.profile.original_tweets[:10] if t.content]
                has_profile = bool(recent_posts)
        except Exception:
            pass  # Continue without profile

        lang_names = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target_lang = lang_names.get(language, "English")

        if has_profile:
            # With profile: analyze style and generate personalized post
            system_prompt = f"""{X_ALGORITHM_KNOWLEDGE}

You are an expert at analyzing writing styles and generating personalized content.

Your task:
1. Analyze the user's writing style from their recent posts
2. Generate a {post_type} that perfectly matches their style
3. Make it engaging and optimized for the X algorithm

Style Analysis Guidelines:
- Tone: formal vs casual, serious vs humorous
- Emoji usage: frequency, types, positions
- Hashtag patterns: frequency, topics
- Sentence structure: short vs long, simple vs complex
- Common phrases or expressions
- Topics they engage with"""

            user_prompt = f"""Analyze this user's writing style and generate a personalized {post_type}.

**User's Recent Posts ({username}):**
{chr(10).join(f'{i+1}. "{post[:200]}"' for i, post in enumerate(recent_posts[:7]))}

**Target Post by @{target_author}:**
"{target_post_content[:300]}"

**Task:** Generate a {post_type} that:
1. Perfectly matches {username}'s writing style
2. Is a natural response to the target post
3. Is optimized for X algorithm engagement
4. Is written in {target_lang}

Respond in this exact JSON format:
{{
  "generated_content": "The generated {post_type} text in {target_lang}",
  "style_analysis": {{
    "tone": "description of user's tone",
    "emoji_style": "how they use emojis",
    "topics": ["list", "of", "interests"],
    "writing_pattern": "description of their writing pattern"
  }},
  "confidence": 0.85,
  "reasoning": "Brief explanation of why this matches their style"
}}"""
        else:
            # Without profile: generate generic engaging post
            system_prompt = f"""{X_ALGORITHM_KNOWLEDGE}

You are an expert at generating engaging X/Twitter content.

Your task:
1. Generate an engaging {post_type} to the target post
2. Make it optimized for the X algorithm
3. Keep it natural and conversational"""

            user_prompt = f"""Generate an engaging {post_type} to this post.

**Target Post by @{target_author}:**
"{target_post_content[:300]}"

**Task:** Generate a {post_type} that:
1. Is a natural, engaging response to the target post
2. Is optimized for X algorithm engagement
3. Is written in {target_lang}
4. Uses appropriate tone for the context

Respond in this exact JSON format:
{{
  "generated_content": "The generated {post_type} text in {target_lang}",
  "style_analysis": {{
    "tone": "conversational and engaging",
    "emoji_style": "moderate, context-appropriate",
    "topics": ["topics", "from", "target post"],
    "writing_pattern": "natural and engaging"
  }},
  "confidence": 0.6,
  "reasoning": "Generated based on target post context (user profile not available)"
}}"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = message.content[0].text

            # Parse JSON response
            result = self._parse_json_response(response_text)
            if result:
                return {
                    "username": username,
                    "generated_content": result.get("generated_content", ""),
                    "style_analysis": result.get("style_analysis", {}),
                    "confidence": result.get("confidence", 0.6 if not has_profile else 0.85),
                    "reasoning": result.get("reasoning", ""),
                    "post_type": post_type,
                    "target_author": target_author,
                }

            return None

        except Exception as e:
            print(f"Claude API error in generate_personalized_post: {e}")
            return None

    def _parse_json_response(self, text: str) -> Optional[dict]:
        """Parse JSON from Claude's response."""
        import json

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None
