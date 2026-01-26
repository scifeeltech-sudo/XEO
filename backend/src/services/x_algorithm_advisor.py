"""X Algorithm-based content advisor using Claude AI."""

import asyncio
import hashlib
import json
from typing import Optional, Literal
import anthropic

from src.config import get_settings
from src.engine import PostFeatures, PentagonScores
from src.db.supabase_client import SupabaseCache

# X Algorithm Knowledge Base - Key factors that affect scoring
X_ALGORITHM_KNOWLEDGE = """
# X (Twitter) Algorithm Knowledge Base

## 19 Engagement Actions Predicted by X Algorithm

### Positive Actions (Boost Content):
1. **favorite (like)** - Primary ranking metric
2. **reply** - Comments/replies
3. **repost** - Retweets/shares
4. **quote** - Quote tweets with commentary
5. **click** - General content clicks
6. **profile_click** - Author profile visits
7. **photo_expand** - Image viewing
8. **video_view** - Video watch time
9. **share** - Direct content sharing
10. **share_via_dm** - DM sharing
11. **share_via_copy_link** - Link copying
12. **dwell** - Time spent viewing content
13. **follow_author** - Following the author

### Negative Actions (Penalize Content):
14. **not_interested** - User disengagement
15. **block_author** - User blocks
16. **mute_author** - User mutes
17. **report** - Reported as inappropriate

## Pentagon Score Mapping

### Reach
- Affected by: click, profile_click, share, share_via_dm, share_via_copy_link
- Boost factors: Trending hashtags, media content, shareable insights

### Engagement
- Affected by: favorite, reply, repost, quote
- Boost factors: Questions, controversial takes, emotional content, CTAs

### Virality
- Affected by: repost, quote, share, share_via_dm
- Boost factors: Shareable format, meme-worthy content, relatable insights

### Quality
- Affected by: dwell, follow_author, NOT(not_interested, block, mute, report)
- Boost factors: Well-written content, valuable insights, proper formatting

### Longevity
- Affected by: dwell (time spent), bookmark, sustained engagement over time
- Boost factors: Evergreen content, reference-worthy info, thread format

## Content Optimization Principles

1. **Questions increase reply rate by 15-20%** - End with engaging questions
2. **Images increase reach by 20-30%** - Visual content gets more exposure
3. **Emojis increase engagement by 8-12%** - But don't overuse (1-3 max)
4. **Optimal length is 100-200 characters** - Short enough to read, long enough to provide value
5. **1-2 relevant hashtags** - More than 3 can hurt quality score
6. **First 50 characters are crucial** - Hook readers immediately
7. **Controversial/opinion content** - Increases reply and quote, but risks negative signals
8. **Thread format** - Increases dwell time and follow probability
"""

# Structured output format for suggestions
SUGGESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "target_score": {
                        "type": "string",
                        "enum": ["reach", "engagement", "virality", "quality", "longevity"]
                    },
                    "improvement": {
                        "type": "string",
                        "description": "Expected improvement like '+15%'"
                    },
                    "action": {
                        "type": "string",
                        "description": "Specific action to take in Korean"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why this helps, referencing X algorithm"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    }
                },
                "required": ["target_score", "improvement", "action", "reason", "priority"]
            }
        },
        "optimized_content": {
            "type": "string",
            "description": "Suggested optimized version of the content"
        },
        "score_predictions": {
            "type": "object",
            "properties": {
                "reach": {"type": "string"},
                "engagement": {"type": "string"},
                "virality": {"type": "string"},
                "quality": {"type": "string"},
                "longevity": {"type": "string"}
            }
        }
    },
    "required": ["suggestions", "optimized_content", "score_predictions"]
}


class XAlgorithmAdvisor:
    """Advisor that uses Claude AI with X algorithm knowledge."""

    def __init__(self):
        settings = get_settings()
        self.client = (
            anthropic.Anthropic(api_key=settings.anthropic_api_key)
            if settings.anthropic_api_key
            else None
        )
        self.cache = SupabaseCache()
        self._memory_cache: dict[str, dict] = {}  # In-memory cache

    def _get_cache_key(
        self,
        content: str,
        scores: PentagonScores,
        language: str,
    ) -> str:
        """Generate cache key from content and context."""
        cache_data = f"{content[:100]}|{scores.reach:.0f}|{scores.engagement:.0f}|{language}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    async def analyze_and_suggest(
        self,
        content: str,
        current_scores: PentagonScores,
        post_features: PostFeatures,
        post_type: Literal["original", "reply", "quote"] = "original",
        target_post_content: Optional[str] = None,
        language: str = "ko",
    ) -> dict:
        """
        Analyze content and provide X algorithm-based suggestions.

        Returns:
            dict with suggestions, optimized_content, and score_predictions
        """
        if not self.client:
            return self._fallback_suggestions(content, current_scores, post_features, language)

        # Check cache first
        cache_key = self._get_cache_key(content, current_scores, language)

        # Layer 1: In-memory cache
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Layer 2: Supabase cache
        try:
            cached = await self.cache.get_suggestion_cache(cache_key)
            if cached:
                self._memory_cache[cache_key] = cached
                return cached
        except Exception:
            pass

        # Build context about the post
        context_info = self._build_context(post_features, post_type, target_post_content)

        # Language mapping
        lang_names = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target_lang = lang_names.get(language, "Korean")

        system_prompt = f"""{X_ALGORITHM_KNOWLEDGE}

You are an X (Twitter) content optimization expert. Analyze the given content and provide specific, actionable suggestions to improve pentagon scores based on X algorithm knowledge.

IMPORTANT RULES:
1. All suggestions and optimized content MUST be in {target_lang}
2. Provide 3-5 specific suggestions with expected score improvements
3. Each suggestion must reference which X algorithm factor it targets
4. Be specific - don't give generic advice
5. The optimized_content should implement the top suggestions
6. Keep the original message intent intact
"""

        user_prompt = f"""Analyze this content and provide optimization suggestions:

**Original Content:**
{content}

**Current Analysis:**
- Characters: {post_features.char_count}
- Has emoji: {post_features.has_emoji}
- Has question: {post_features.has_question}
- Has hashtag: {post_features.hashtag_count > 0}
- Has CTA: {post_features.has_cta}
- Has media: {post_features.has_media}

**Current Pentagon Scores:**
- Reach: {current_scores.reach:.1f}
- Engagement: {current_scores.engagement:.1f}
- Virality: {current_scores.virality:.1f}
- Quality: {current_scores.quality:.1f}
- Longevity: {current_scores.longevity:.1f}

**Post Type:** {post_type}
{context_info}

Provide suggestions in this JSON format:
{{
  "suggestions": [
    {{
      "target_score": "engagement",
      "improvement": "+15%",
      "action": "Specific action to take (in target language)",
      "reason": "Increases p_reply probability in X algorithm",
      "priority": "high"
    }}
  ],
  "optimized_content": "Improved content (in target language)",
  "score_predictions": {{
    "reach": "+5%",
    "engagement": "+15%",
    "virality": "+8%",
    "quality": "+0%",
    "longevity": "+3%"
  }}
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,  # Reduced from 1500 for faster response
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = message.content[0].text

            # Extract JSON from response
            result = self._parse_json_response(response_text)
            if result:
                # Save to cache (async, don't wait)
                self._memory_cache[cache_key] = result
                if len(self._memory_cache) > 500:  # Limit memory cache size
                    self._memory_cache.pop(next(iter(self._memory_cache)))
                try:
                    asyncio.create_task(
                        self.cache.set_suggestion_cache(cache_key, result, ttl_minutes=60)
                    )
                except Exception:
                    pass
                return result

            return self._fallback_suggestions(content, current_scores, post_features, language)

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_suggestions(content, current_scores, post_features, language)

    def _build_context(
        self,
        features: PostFeatures,
        post_type: str,
        target_content: Optional[str],
    ) -> str:
        """Build context string for the prompt."""
        context = ""

        if post_type == "reply" and target_content:
            context = f"\n**Target Post (replying to):**\n{target_content[:200]}"
        elif post_type == "quote" and target_content:
            context = f"\n**Target Post (quoting):**\n{target_content[:200]}"

        return context

    def _parse_json_response(self, text: str) -> Optional[dict]:
        """Parse JSON from Claude's response."""
        try:
            # Try direct JSON parse
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re
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

    def _fallback_suggestions(
        self,
        content: str,
        scores: PentagonScores,
        features: PostFeatures,
        language: str,
    ) -> dict:
        """Provide rule-based suggestions when API is unavailable."""
        suggestions = []
        optimized_content = content
        score_predictions = {
            "reach": "+0%",
            "engagement": "+0%",
            "virality": "+0%",
            "quality": "+0%",
            "longevity": "+0%",
        }

        # Multilingual action texts
        actions = {
            "add_question": {
                "ko": "마지막에 질문을 추가하세요",
                "en": "Add a question at the end",
                "ja": "最後に質問を追加してください",
                "zh": "在末尾添加一个问题",
            },
            "add_emoji": {
                "ko": "적절한 이모지 1-2개를 추가하세요",
                "en": "Add 1-2 relevant emojis",
                "ja": "関連する絵文字を1-2個追加してください",
                "zh": "添加1-2个相关表情符号",
            },
            "add_media": {
                "ko": "이미지나 영상을 추가하세요",
                "en": "Add an image or video",
                "ja": "画像や動画を追加してください",
                "zh": "添加图片或视频",
            },
            "add_hashtag": {
                "ko": "관련 해시태그 1-2개를 추가하세요",
                "en": "Add 1-2 relevant hashtags",
                "ja": "関連ハッシュタグを1-2個追加してください",
                "zh": "添加1-2个相关标签",
            },
            "add_cta": {
                "ko": "공유를 유도하는 CTA를 추가하세요",
                "en": "Add a share-encouraging CTA",
                "ja": "共有を促すCTAを追加してください",
                "zh": "添加鼓励分享的行动号召",
            },
            "add_details": {
                "ko": "내용을 조금 더 구체적으로 작성하세요",
                "en": "Add more specific details",
                "ja": "もう少し具体的に書いてください",
                "zh": "添加更多具体细节",
            },
            "make_concise": {
                "ko": "내용을 간결하게 줄이세요",
                "en": "Make it more concise",
                "ja": "より簡潔にしてください",
                "zh": "使其更简洁",
            },
            "add_insights": {
                "ko": "가치 있는 정보나 인사이트를 추가하세요",
                "en": "Add valuable insights",
                "ja": "価値ある情報やインサイトを追加してください",
                "zh": "添加有价值的见解",
            },
        }

        def get_action(key: str) -> str:
            return actions[key].get(language, actions[key]["en"])

        # Engagement suggestions
        if not features.has_question:
            suggestions.append({
                "target_score": "engagement",
                "improvement": "+15%",
                "action": get_action("add_question"),
                "reason": "Increases p_reply probability for higher engagement score",
                "priority": "high",
            })
            score_predictions["engagement"] = "+15%"

        if not features.has_emoji:
            suggestions.append({
                "target_score": "engagement",
                "improvement": "+8%",
                "action": get_action("add_emoji"),
                "reason": "Visual elements increase p_favorite probability",
                "priority": "medium",
            })

        # Reach suggestions
        if not features.has_media:
            suggestions.append({
                "target_score": "reach",
                "improvement": "+20%",
                "action": get_action("add_media"),
                "reason": "Media content increases photo_expand and video_view probability",
                "priority": "high",
            })
            score_predictions["reach"] = "+20%"

        if features.hashtag_count == 0:
            suggestions.append({
                "target_score": "reach",
                "improvement": "+5%",
                "action": get_action("add_hashtag"),
                "reason": "Hashtags increase search visibility and p_click probability",
                "priority": "medium",
            })

        # Virality suggestions
        if not features.has_cta:
            suggestions.append({
                "target_score": "virality",
                "improvement": "+10%",
                "action": get_action("add_cta"),
                "reason": "CTAs increase p_repost and p_share probability for virality",
                "priority": "medium",
            })
            score_predictions["virality"] = "+10%"

        # Quality suggestions
        if features.char_count < 50:
            suggestions.append({
                "target_score": "quality",
                "improvement": "+10%",
                "action": get_action("add_details"),
                "reason": "Sufficient content increases dwell time for better quality score",
                "priority": "medium",
            })
            score_predictions["quality"] = "+10%"
        elif features.char_count > 250:
            suggestions.append({
                "target_score": "quality",
                "improvement": "+5%",
                "action": get_action("make_concise"),
                "reason": "Concise content improves completion rate and decreases p_not_interested",
                "priority": "low",
            })

        # Longevity suggestions
        if features.char_count > 0 and features.char_count < 100:
            suggestions.append({
                "target_score": "longevity",
                "improvement": "+8%",
                "action": get_action("add_insights"),
                "reason": "Valuable content increases p_bookmark for longevity",
                "priority": "medium",
            })
            score_predictions["longevity"] = "+8%"

        return {
            "suggestions": suggestions[:5],
            "optimized_content": optimized_content,
            "score_predictions": score_predictions,
        }


async def generate_algorithm_tips(
    content: str,
    scores: PentagonScores,
    features: PostFeatures,
    post_type: str = "original",
    target_content: Optional[str] = None,
    language: str = "ko",
) -> dict:
    """
    Convenience function to generate X algorithm-based tips.

    Returns dict with:
    - suggestions: list of improvement suggestions
    - optimized_content: suggested optimized content
    - score_predictions: expected score changes
    """
    advisor = XAlgorithmAdvisor()
    return await advisor.analyze_and_suggest(
        content=content,
        current_scores=scores,
        post_features=features,
        post_type=post_type,
        target_post_content=target_content,
        language=language,
    )
