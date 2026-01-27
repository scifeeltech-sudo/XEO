"""Feature extraction for posts and profiles."""

import re
from dataclasses import dataclass
from typing import Literal

from src.services.sela_api_client import ProfileData


@dataclass
class PostFeatures:
    """Extracted features from a post."""

    # Content features
    char_count: int
    word_count: int
    sentence_count: int

    # Engagement signals
    has_question: bool
    has_cta: bool  # Call to action (e.g., "Check this out", "Let me know")
    has_emoji: bool
    emoji_count: int

    # Media
    has_media: bool
    media_type: Literal["image", "video", "gif", None]

    # Hashtags & Mentions
    hashtag_count: int
    mention_count: int
    has_url: bool

    # Language patterns
    is_thread_starter: bool  # Contains "🧵" or "(1/n)" pattern
    is_quote: bool

    @property
    def optimal_length(self) -> float:
        """Score for optimal length (70-200 chars is optimal)."""
        if 70 <= self.char_count <= 200:
            return 1.0
        elif self.char_count < 70:
            return self.char_count / 70
        else:  # > 200
            return max(0.5, 1.0 - (self.char_count - 200) / 280)


@dataclass
class ProfileFeatures:
    """Extracted features from a user profile."""

    username: str
    tweet_count: int

    # Engagement metrics
    avg_engagement_rate: float
    avg_likes: float
    avg_retweets: float
    avg_replies: float
    avg_views: float

    # Content patterns
    retweet_ratio: float
    quote_ratio: float
    media_ratio: float

    # Derived metrics
    engagement_consistency: float  # Std dev of engagement rates


# Regex patterns
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+"
)
HASHTAG_PATTERN = re.compile(r"#\w+")
MENTION_PATTERN = re.compile(r"@\w+")
URL_PATTERN = re.compile(r"https?://\S+")
QUESTION_PATTERN = re.compile(r"\?")
# Combined CTA pattern for faster matching (single regex instead of 11)
CTA_PATTERN = re.compile(
    r"\b(?:"
    r"check\s+(?:this\s+)?out|"
    r"let\s+me\s+know|"
    r"what\s+do\s+you\s+think|"
    r"share\s+your|"
    r"tell\s+me|"
    r"drop\s+a|"
    r"comment|"
    r"reply|"
    r"follow|"
    r"rt\s+if|"
    r"like\s+if"
    r")\b",
    re.IGNORECASE
)
THREAD_PATTERN = re.compile(r"🧵|\(\d+/\d+\)|^\d+\.|thread:", re.IGNORECASE)


def extract_post_features(
    content: str,
    media_type: Literal["image", "video", "gif", None] = None,
    is_quote: bool = False,
) -> PostFeatures:
    """Extract features from post content."""

    # Basic counts
    char_count = len(content)
    words = content.split()
    word_count = len(words)
    sentences = re.split(r"[.!?]+", content)
    sentence_count = len([s for s in sentences if s.strip()])

    # Emoji
    emojis = EMOJI_PATTERN.findall(content)
    emoji_count = len(emojis)

    # Hashtags & Mentions
    hashtags = HASHTAG_PATTERN.findall(content)
    mentions = MENTION_PATTERN.findall(content)
    urls = URL_PATTERN.findall(content)

    # Questions & CTA
    has_question = bool(QUESTION_PATTERN.search(content))
    has_cta = bool(CTA_PATTERN.search(content))

    # Thread detection
    is_thread_starter = bool(THREAD_PATTERN.search(content))

    return PostFeatures(
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
        has_question=has_question,
        has_cta=has_cta,
        has_emoji=emoji_count > 0,
        emoji_count=emoji_count,
        has_media=media_type is not None,
        media_type=media_type,
        hashtag_count=len(hashtags),
        mention_count=len(mentions),
        has_url=len(urls) > 0,
        is_thread_starter=is_thread_starter,
        is_quote=is_quote,
    )


def extract_profile_features(profile: ProfileData) -> ProfileFeatures:
    """Extract features from user profile data."""

    tweets = profile.tweets
    if not tweets:
        return ProfileFeatures(
            username=profile.username,
            tweet_count=0,
            avg_engagement_rate=0,
            avg_likes=0,
            avg_retweets=0,
            avg_replies=0,
            avg_views=0,
            retweet_ratio=0,
            quote_ratio=0,
            media_ratio=0,
            engagement_consistency=0,
        )

    # Calculate engagement rates
    engagement_rates = [t.engagement_rate for t in tweets]
    avg_engagement = sum(engagement_rates) / len(engagement_rates)

    # Engagement consistency (lower std dev = more consistent)
    if len(engagement_rates) > 1:
        mean = avg_engagement
        variance = sum((r - mean) ** 2 for r in engagement_rates) / len(engagement_rates)
        std_dev = variance ** 0.5
        consistency = 1 / (1 + std_dev)  # Normalize to 0-1
    else:
        consistency = 1.0

    return ProfileFeatures(
        username=profile.username,
        tweet_count=len(tweets),
        avg_engagement_rate=avg_engagement,
        avg_likes=profile.avg_likes,
        avg_retweets=profile.avg_retweets,
        avg_replies=profile.avg_replies,
        avg_views=profile.avg_views,
        retweet_ratio=profile.retweet_ratio,
        quote_ratio=profile.quote_ratio,
        media_ratio=profile.media_ratio,
        engagement_consistency=consistency,
    )
