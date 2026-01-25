# XEO (X Score Optimizer) Full Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** X 포스트 스코어 예측 및 최적화 서비스 구축 (인증 없이 무료 사용)

**Architecture:** Python FastAPI 백엔드 + Next.js 프론트엔드 + Supabase 캐싱. X 알고리즘 기반 5각형 스코어 예측 엔진으로 포스트 분석 및 AI 최적화 제안 제공.

**Tech Stack:** Python 3.11+ (uv), FastAPI, Next.js 14, Supabase, Tailwind CSS, Recharts, OpenAI API

---

## 현재 완료 상태

| 항목 | 상태 | 파일 |
|------|------|------|
| PRD 문서 | ✅ 완료 | `PRD.md` |
| Sela API 클라이언트 | ✅ 완료 | `backend/src/services/sela_api_client.py` |
| GitHub 저장소 | ✅ 완료 | `scifeeltech-sudo/XEO` |

---

## Phase 1: Backend Core (스코어 엔진)

### Task 1.1: Feature Extractor 구현

포스트/프로필 데이터에서 스코어 계산에 필요한 피처를 추출하는 모듈

**Files:**
- Create: `backend/src/engine/__init__.py`
- Create: `backend/src/engine/feature_extractor.py`
- Create: `backend/tests/test_feature_extractor.py`

**Step 1: 테스트 파일 작성**

```python
# backend/tests/test_feature_extractor.py
import pytest
from src.engine.feature_extractor import PostFeatures, ProfileFeatures, extract_post_features, extract_profile_features

def test_extract_post_features_basic():
    """기본 포스트 피처 추출 테스트"""
    content = "Hello world! 🌍 What do you think? #tech"
    features = extract_post_features(content)

    assert features.char_count == len(content)
    assert features.word_count == 7
    assert features.has_emoji is True
    assert features.has_question is True
    assert features.hashtag_count == 1
    assert features.has_media is False

def test_extract_post_features_with_media():
    """미디어 포함 포스트 피처"""
    features = extract_post_features("Check this out!", media_type="image")
    assert features.has_media is True
    assert features.media_type == "image"

def test_extract_profile_features():
    """프로필 피처 추출 테스트"""
    from src.services.sela_api_client import ProfileData, TweetData

    tweets = [
        TweetData(
            tweet_id="1", username="test", content="Hello",
            tweet_url="/test/1", likes_count=100, retweets_count=10,
            replies_count=5, views_count=1000
        ),
        TweetData(
            tweet_id="2", username="test", content="World 🌍",
            tweet_url="/test/2", likes_count=200, retweets_count=20,
            replies_count=10, views_count=2000, is_retweet=True
        ),
    ]
    profile = ProfileData(username="test", tweets=tweets)
    features = extract_profile_features(profile)

    assert features.avg_engagement_rate > 0
    assert features.avg_likes == 150
    assert features.retweet_ratio == 0.5
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
cd backend && uv run pytest tests/test_feature_extractor.py -v
# Expected: FAIL - module not found
```

**Step 3: Feature Extractor 구현**

```python
# backend/src/engine/__init__.py
from .feature_extractor import (
    PostFeatures,
    ProfileFeatures,
    extract_post_features,
    extract_profile_features,
)

__all__ = [
    "PostFeatures",
    "ProfileFeatures",
    "extract_post_features",
    "extract_profile_features",
]
```

```python
# backend/src/engine/feature_extractor.py
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
CTA_PATTERNS = [
    r"\bcheck\s+(this\s+)?out\b",
    r"\blet\s+me\s+know\b",
    r"\bwhat\s+do\s+you\s+think\b",
    r"\bshare\s+your\b",
    r"\btell\s+me\b",
    r"\bdrop\s+a\b",
    r"\bcomment\b",
    r"\breply\b",
    r"\bfollow\b",
    r"\brt\s+if\b",
    r"\blike\s+if\b",
]
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
    has_cta = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in CTA_PATTERNS
    )

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
```

**Step 4: 테스트 실행 (성공 확인)**

```bash
cd backend && uv run pytest tests/test_feature_extractor.py -v
# Expected: PASS
```

**Step 5: 커밋**

```bash
git add backend/src/engine/ backend/tests/test_feature_extractor.py
git commit -m "feat(engine): add feature extractor for posts and profiles"
```

---

### Task 1.2: Weighted Scorer 구현

X 알고리즘 기반 5각형 스코어 계산기

**Files:**
- Create: `backend/src/engine/weighted_scorer.py`
- Create: `backend/tests/test_weighted_scorer.py`

**Step 1: 테스트 작성**

```python
# backend/tests/test_weighted_scorer.py
import pytest
from src.engine.weighted_scorer import (
    WeightedScorer,
    PentagonScores,
    ActionProbabilities,
)

def test_calculate_pentagon_scores():
    """5각형 스코어 계산 테스트"""
    scorer = WeightedScorer()

    probs = ActionProbabilities(
        p_favorite=0.15,
        p_reply=0.08,
        p_repost=0.05,
        p_quote=0.02,
        p_click=0.25,
        p_profile_click=0.12,
        p_share=0.03,
        p_dwell=0.45,
        p_video_view=0.0,
        p_follow_author=0.01,
        p_not_interested=0.05,
        p_block_author=0.001,
        p_mute_author=0.002,
        p_report=0.0001,
    )

    scores = scorer.calculate_scores(probs)

    assert isinstance(scores, PentagonScores)
    assert 0 <= scores.reach <= 100
    assert 0 <= scores.engagement <= 100
    assert 0 <= scores.virality <= 100
    assert 0 <= scores.quality <= 100
    assert 0 <= scores.longevity <= 100

def test_estimate_probabilities_from_features():
    """피처 기반 확률 추정 테스트"""
    from src.engine.feature_extractor import PostFeatures, ProfileFeatures

    scorer = WeightedScorer()

    post_features = PostFeatures(
        char_count=120,
        word_count=20,
        sentence_count=2,
        has_question=True,
        has_cta=True,
        has_emoji=True,
        emoji_count=2,
        has_media=True,
        media_type="image",
        hashtag_count=1,
        mention_count=0,
        has_url=False,
        is_thread_starter=False,
        is_quote=False,
    )

    profile_features = ProfileFeatures(
        username="test",
        tweet_count=100,
        avg_engagement_rate=0.03,
        avg_likes=500,
        avg_retweets=50,
        avg_replies=30,
        avg_views=10000,
        retweet_ratio=0.2,
        quote_ratio=0.1,
        media_ratio=0.6,
        engagement_consistency=0.8,
    )

    probs = scorer.estimate_probabilities(post_features, profile_features)

    assert isinstance(probs, ActionProbabilities)
    assert probs.p_favorite > 0
    # 질문 + CTA + 이모지 + 미디어 = 높은 참여 확률
    assert probs.p_reply > 0.05
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
cd backend && uv run pytest tests/test_weighted_scorer.py -v
```

**Step 3: Weighted Scorer 구현**

```python
# backend/src/engine/weighted_scorer.py
"""
Weighted Scorer based on X's open-source algorithm.

Calculates 5-dimension scores (pentagon chart):
- Reach: How many people will see this
- Engagement: How many interactions will occur
- Virality: How far will this spread
- Quality: Content quality (inverse of negative signals)
- Longevity: How long will this stay relevant
"""

from dataclasses import dataclass
from typing import Optional

from .feature_extractor import PostFeatures, ProfileFeatures


@dataclass
class ActionProbabilities:
    """Predicted probabilities for each action type."""

    # Positive actions
    p_favorite: float = 0.0
    p_reply: float = 0.0
    p_repost: float = 0.0
    p_quote: float = 0.0
    p_click: float = 0.0
    p_profile_click: float = 0.0
    p_share: float = 0.0
    p_dwell: float = 0.0  # Time spent viewing
    p_video_view: float = 0.0
    p_follow_author: float = 0.0

    # Negative actions
    p_not_interested: float = 0.0
    p_block_author: float = 0.0
    p_mute_author: float = 0.0
    p_report: float = 0.0


@dataclass
class PentagonScores:
    """5-dimension scores for the pentagon chart."""

    reach: float  # 도달률
    engagement: float  # 참여도
    virality: float  # 바이럴성
    quality: float  # 품질
    longevity: float  # 지속성

    def to_dict(self) -> dict[str, float]:
        return {
            "reach": round(self.reach, 1),
            "engagement": round(self.engagement, 1),
            "virality": round(self.virality, 1),
            "quality": round(self.quality, 1),
            "longevity": round(self.longevity, 1),
        }

    @property
    def overall(self) -> float:
        """Calculate overall score (weighted average)."""
        weights = {
            "reach": 0.25,
            "engagement": 0.25,
            "virality": 0.20,
            "quality": 0.15,
            "longevity": 0.15,
        }
        return (
            self.reach * weights["reach"] +
            self.engagement * weights["engagement"] +
            self.virality * weights["virality"] +
            self.quality * weights["quality"] +
            self.longevity * weights["longevity"]
        )


# Score weights from X algorithm (PRD appendix)
SCORE_WEIGHTS = {
    "reach": {
        "p_click": 0.4,
        "p_profile_click": 0.3,
        "p_dwell": 0.3,
    },
    "engagement": {
        "p_favorite": 0.35,
        "p_reply": 0.35,
        "p_quote": 0.15,
        "p_not_interested": -0.15,
    },
    "virality": {
        "p_repost": 0.4,
        "p_quote": 0.3,
        "p_share": 0.3,
    },
    "quality": {
        "p_favorite": 0.25,
        "p_dwell": 0.25,
        "p_not_interested": -0.2,
        "p_block_author": -0.15,
        "p_mute_author": -0.1,
        "p_report": -0.3,
    },
    "longevity": {
        "p_dwell": 0.3,
        "p_video_view": 0.25,
        "p_follow_author": 0.25,
        "p_favorite": 0.2,
    },
}

# Feature impact modifiers
FEATURE_IMPACTS = {
    "has_question": {"p_reply": 0.15, "p_favorite": 0.05},
    "has_cta": {"p_reply": 0.10, "p_click": 0.08},
    "has_emoji": {"p_favorite": 0.05, "p_dwell": 0.03},
    "has_media": {"p_click": 0.20, "p_dwell": 0.15, "p_repost": 0.10},
    "has_video": {"p_video_view": 0.50, "p_dwell": 0.25},
    "optimal_length": {"p_dwell": 0.10, "p_favorite": 0.05},
    "has_hashtag": {"p_click": 0.03},
    "is_quote": {"p_quote": -0.10, "p_repost": 0.05},  # Quotes get fewer quotes but more reposts
}


class WeightedScorer:
    """Calculate weighted scores based on X algorithm."""

    def __init__(self):
        self.weights = SCORE_WEIGHTS
        self.feature_impacts = FEATURE_IMPACTS

    def calculate_scores(self, probs: ActionProbabilities) -> PentagonScores:
        """Calculate pentagon scores from action probabilities."""

        def calc_dimension(dimension: str) -> float:
            weights = self.weights[dimension]
            score = 0.0
            for action, weight in weights.items():
                prob = getattr(probs, action, 0.0)
                score += prob * weight
            # Normalize to 0-100 scale
            # Assuming max possible raw score is ~0.5 for positive dimensions
            normalized = min(100, max(0, score * 200))
            return normalized

        return PentagonScores(
            reach=calc_dimension("reach"),
            engagement=calc_dimension("engagement"),
            virality=calc_dimension("virality"),
            quality=calc_dimension("quality") + 50,  # Quality baseline is 50
            longevity=calc_dimension("longevity"),
        )

    def estimate_probabilities(
        self,
        post_features: PostFeatures,
        profile_features: ProfileFeatures,
        context_boost: Optional[dict[str, float]] = None,
    ) -> ActionProbabilities:
        """
        Estimate action probabilities from features.

        This is a simplified model based on feature heuristics.
        In production, this would be replaced by ML model inference.
        """

        # Base probabilities from profile history
        base_engagement = profile_features.avg_engagement_rate

        probs = ActionProbabilities(
            p_favorite=base_engagement * 0.6,
            p_reply=base_engagement * 0.15,
            p_repost=base_engagement * 0.15,
            p_quote=base_engagement * 0.05,
            p_click=0.20,
            p_profile_click=0.10,
            p_share=base_engagement * 0.05,
            p_dwell=0.30,
            p_video_view=0.0,
            p_follow_author=0.005,
            p_not_interested=0.05,
            p_block_author=0.001,
            p_mute_author=0.002,
            p_report=0.0001,
        )

        # Apply feature impacts
        if post_features.has_question:
            for action, boost in self.feature_impacts["has_question"].items():
                current = getattr(probs, action)
                setattr(probs, action, current + boost)

        if post_features.has_cta:
            for action, boost in self.feature_impacts["has_cta"].items():
                current = getattr(probs, action)
                setattr(probs, action, current + boost)

        if post_features.has_emoji:
            for action, boost in self.feature_impacts["has_emoji"].items():
                current = getattr(probs, action)
                setattr(probs, action, current + boost)

        if post_features.has_media:
            for action, boost in self.feature_impacts["has_media"].items():
                current = getattr(probs, action)
                setattr(probs, action, current + boost)
            if post_features.media_type == "video":
                probs.p_video_view = 0.50
                probs.p_dwell += 0.25

        # Optimal length bonus
        length_score = post_features.optimal_length
        probs.p_dwell += 0.10 * length_score
        probs.p_favorite += 0.05 * length_score

        if post_features.hashtag_count > 0:
            probs.p_click += 0.03 * min(post_features.hashtag_count, 3)

        if post_features.is_quote:
            probs.p_quote -= 0.10  # Less likely to quote a quote
            probs.p_repost += 0.05

        # Apply context boost (for reply/quote to popular posts)
        if context_boost:
            for action, boost in context_boost.items():
                if hasattr(probs, action):
                    current = getattr(probs, action)
                    setattr(probs, action, current * (1 + boost))

        # Clamp all probabilities to [0, 1]
        for field in probs.__dataclass_fields__:
            value = getattr(probs, field)
            setattr(probs, field, max(0.0, min(1.0, value)))

        return probs

    def analyze_post(
        self,
        post_features: PostFeatures,
        profile_features: ProfileFeatures,
        context_boost: Optional[dict[str, float]] = None,
    ) -> tuple[PentagonScores, ActionProbabilities]:
        """Full analysis: estimate probabilities and calculate scores."""
        probs = self.estimate_probabilities(
            post_features, profile_features, context_boost
        )
        scores = self.calculate_scores(probs)
        return scores, probs
```

**Step 4: engine __init__.py 업데이트**

```python
# backend/src/engine/__init__.py
from .feature_extractor import (
    PostFeatures,
    ProfileFeatures,
    extract_post_features,
    extract_profile_features,
)
from .weighted_scorer import (
    WeightedScorer,
    PentagonScores,
    ActionProbabilities,
)

__all__ = [
    "PostFeatures",
    "ProfileFeatures",
    "extract_post_features",
    "extract_profile_features",
    "WeightedScorer",
    "PentagonScores",
    "ActionProbabilities",
]
```

**Step 5: 테스트 실행**

```bash
cd backend && uv run pytest tests/test_weighted_scorer.py -v
```

**Step 6: 커밋**

```bash
git add backend/src/engine/ backend/tests/test_weighted_scorer.py
git commit -m "feat(engine): add weighted scorer for pentagon scores"
```

---

### Task 1.3: Profile Analyzer Service 구현

프로필 분석 서비스

**Files:**
- Create: `backend/src/services/profile_analyzer.py`
- Create: `backend/tests/test_profile_analyzer.py`

**Step 1: 테스트 작성**

```python
# backend/tests/test_profile_analyzer.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.profile_analyzer import ProfileAnalyzer, ProfileAnalysisResult

@pytest.mark.asyncio
async def test_analyze_profile():
    """프로필 분석 테스트"""
    # Mock Sela API response
    mock_profile_data = {
        "username": "testuser",
        "tweets": [
            {
                "tweet_id": "1",
                "username": "testuser",
                "content": "Hello world!",
                "tweet_url": "/testuser/1",
                "likes_count": 100,
                "retweets_count": 10,
                "replies_count": 5,
                "views_count": 1000,
            }
        ],
    }

    with patch("src.services.profile_analyzer.SelaAPIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.profile = mock_profile_data
        mock_client.get_twitter_profile = AsyncMock(return_value=mock_response)

        analyzer = ProfileAnalyzer()
        analyzer.client = mock_client

        result = await analyzer.analyze("testuser")

        assert isinstance(result, ProfileAnalysisResult)
        assert result.username == "testuser"
        assert result.scores is not None
        assert len(result.insights) >= 0
```

**Step 2: Profile Analyzer 구현**

```python
# backend/src/services/profile_analyzer.py
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
                message="참여율이 평균보다 낮습니다. 더 상호작용을 유도하는 콘텐츠를 시도해보세요.",
                priority="high",
            ))
        elif features.avg_engagement_rate > 0.05:
            insights.append(Insight(
                category="engagement",
                message="참여율이 매우 높습니다! 현재 전략을 유지하세요.",
                priority="low",
            ))

        # Content mix insights
        if features.retweet_ratio > 0.5:
            insights.append(Insight(
                category="content",
                message="리트윗 비율이 높습니다. 오리지널 콘텐츠를 더 늘려보세요.",
                priority="medium",
            ))

        if features.media_ratio < 0.3:
            insights.append(Insight(
                category="media",
                message="미디어 사용이 적습니다. 이미지/비디오는 참여율을 높입니다.",
                priority="medium",
            ))

        # Consistency insights
        if features.engagement_consistency < 0.5:
            insights.append(Insight(
                category="consistency",
                message="참여율 변동이 큽니다. 일관된 품질의 콘텐츠를 유지해보세요.",
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
                description="포스팅 빈도를 늘려 더 많은 노출 기회를 만드세요.",
            ))
        elif weakest == "engagement":
            recommendations.append(Recommendation(
                action="add_questions",
                expected_impact="+15% engagement",
                description="포스트에 질문을 추가하여 답글을 유도하세요.",
            ))
        elif weakest == "virality":
            recommendations.append(Recommendation(
                action="create_shareable_content",
                expected_impact="+25% virality",
                description="공유하고 싶은 유용한 정보나 인사이트를 제공하세요.",
            ))
        elif weakest == "quality":
            recommendations.append(Recommendation(
                action="focus_on_original_content",
                expected_impact="+20% quality",
                description="리트윗보다 오리지널 콘텐츠에 집중하세요.",
            ))
        elif weakest == "longevity":
            recommendations.append(Recommendation(
                action="add_media",
                expected_impact="+30% longevity",
                description="이미지나 비디오를 추가하여 체류 시간을 늘리세요.",
            ))

        # Media recommendation if low
        if features.media_ratio < 0.4:
            recommendations.append(Recommendation(
                action="increase_media_usage",
                expected_impact="+15% overall",
                description="포스트의 40% 이상에 미디어를 포함시키세요.",
            ))

        return recommendations
```

**Step 3: 테스트 실행**

```bash
cd backend && uv add pytest-asyncio
cd backend && uv run pytest tests/test_profile_analyzer.py -v
```

**Step 4: 커밋**

```bash
git add backend/src/services/profile_analyzer.py backend/tests/test_profile_analyzer.py
git commit -m "feat(services): add profile analyzer service"
```

---

### Task 1.4: Score Predictor Service 구현

포스트 스코어 예측 서비스

**Files:**
- Create: `backend/src/services/score_predictor.py`
- Create: `backend/tests/test_score_predictor.py`

**Step 1: 테스트 작성**

```python
# backend/tests/test_score_predictor.py
import pytest
from src.services.score_predictor import ScorePredictor, PostAnalysisResult

@pytest.mark.asyncio
async def test_predict_original_post():
    """원본 포스트 스코어 예측"""
    predictor = ScorePredictor()

    # Note: This requires mocking the Sela API client
    # For now, test with pre-loaded profile data
    result = await predictor.predict(
        username="testuser",
        content="This is a test post with a question? 🤔",
        post_type="original",
    )

    assert isinstance(result, PostAnalysisResult)
    assert result.scores.reach >= 0
    assert result.scores.engagement >= 0
    assert len(result.quick_tips) >= 0

@pytest.mark.asyncio
async def test_predict_reply():
    """답글 스코어 예측 (컨텍스트 포함)"""
    predictor = ScorePredictor()

    result = await predictor.predict(
        username="testuser",
        content="Great point! I agree.",
        post_type="reply",
        target_post_url="https://x.com/elonmusk/status/123456",
    )

    assert result.context is not None
    # Reply to popular account should have reach boost
```

**Step 2: Score Predictor 구현**

```python
# backend/src/services/score_predictor.py
"""Score prediction service for posts."""

from dataclasses import dataclass
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
    quick_tips: list[str]
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
    ) -> list[str]:
        """Generate quick improvement tips."""
        tips = []

        if not features.has_emoji:
            tips.append("이모지를 추가하면 engagement +5% 예상")

        if not features.has_question:
            tips.append("질문 형태로 바꾸면 reply율 +15% 예상")

        if not features.has_media:
            tips.append("이미지를 추가하면 reach +20% 예상")

        if features.char_count < 50:
            tips.append("내용을 조금 더 추가하면 dwell time 증가 예상")
        elif features.char_count > 250:
            tips.append("내용을 간결하게 줄이면 완독률 상승 예상")

        if features.hashtag_count == 0:
            tips.append("관련 해시태그 1-2개를 추가해보세요")
        elif features.hashtag_count > 3:
            tips.append("해시태그를 3개 이하로 줄이면 품질 점수 상승")

        return tips[:5]  # Return max 5 tips
```

**Step 3: 테스트 실행**

```bash
cd backend && uv run pytest tests/test_score_predictor.py -v
```

**Step 4: 커밋**

```bash
git add backend/src/services/score_predictor.py backend/tests/test_score_predictor.py
git commit -m "feat(services): add score predictor service"
```

---

### Task 1.5: FastAPI Application 설정

FastAPI 서버 설정 및 라우트 구현

**Files:**
- Create: `backend/src/config.py`
- Modify: `backend/src/main.py`
- Create: `backend/src/api/__init__.py`
- Create: `backend/src/api/routes/__init__.py`
- Create: `backend/src/api/routes/profile.py`
- Create: `backend/src/api/routes/post.py`

**Step 1: 의존성 추가**

```bash
cd backend && uv add fastapi uvicorn[standard]
```

**Step 2: Config 파일 생성**

```python
# backend/src/config.py
"""Application configuration."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_env: str = "development"
    app_debug: bool = True

    # Sela API
    sela_api_base_url: str = ""
    sela_api_key: str = ""
    sela_principal_id: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 3: API Routes 구현**

```python
# backend/src/api/__init__.py
from fastapi import APIRouter
from .routes import profile, post

api_router = APIRouter()
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(post.router, prefix="/post", tags=["post"])
```

```python
# backend/src/api/routes/__init__.py
from . import profile, post
```

```python
# backend/src/api/routes/profile.py
"""Profile analysis API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.profile_analyzer import ProfileAnalyzer

router = APIRouter()
analyzer = ProfileAnalyzer()


class ProfileScores(BaseModel):
    reach: float
    engagement: float
    virality: float
    quality: float
    longevity: float


class InsightResponse(BaseModel):
    category: str
    message: str
    priority: str


class RecommendationResponse(BaseModel):
    action: str
    expected_impact: str
    description: str


class ProfileAnalysisResponse(BaseModel):
    username: str
    scores: ProfileScores
    insights: list[InsightResponse]
    recommendations: list[RecommendationResponse]


@router.get("/{username}/analyze", response_model=ProfileAnalysisResponse)
async def analyze_profile(username: str):
    """Analyze a user's X profile."""
    try:
        result = await analyzer.analyze(username)

        return ProfileAnalysisResponse(
            username=result.username,
            scores=ProfileScores(**result.scores.to_dict()),
            insights=[
                InsightResponse(
                    category=i.category,
                    message=i.message,
                    priority=i.priority,
                )
                for i in result.insights
            ],
            recommendations=[
                RecommendationResponse(
                    action=r.action,
                    expected_impact=r.expected_impact,
                    description=r.description,
                )
                for r in result.recommendations
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# backend/src/api/routes/post.py
"""Post analysis API routes."""

from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.score_predictor import ScorePredictor

router = APIRouter()
predictor = ScorePredictor()


class PostAnalyzeRequest(BaseModel):
    username: str
    content: str
    post_type: Literal["original", "reply", "quote", "thread"] = "original"
    target_post_url: Optional[str] = None
    media_type: Optional[Literal["image", "video", "gif"]] = None


class ScoresResponse(BaseModel):
    reach: float
    engagement: float
    virality: float
    quality: float
    longevity: float


class ProbabilitiesResponse(BaseModel):
    p_favorite: float
    p_reply: float
    p_repost: float
    p_quote: float
    p_click: float
    p_profile_click: float
    p_share: float
    p_dwell: float
    p_video_view: float
    p_follow_author: float
    p_not_interested: float
    p_block_author: float
    p_mute_author: float
    p_report: float


class ContextResponse(BaseModel):
    target_post_id: str
    target_post_content: str
    target_author: str
    context_adjustments: dict[str, str]
    recommendations: list[str]


class PostAnalysisResponse(BaseModel):
    scores: ScoresResponse
    breakdown: ProbabilitiesResponse
    quick_tips: list[str]
    context: Optional[ContextResponse] = None


@router.post("/analyze", response_model=PostAnalysisResponse)
async def analyze_post(request: PostAnalyzeRequest):
    """Analyze a post and predict scores."""
    try:
        result = await predictor.predict(
            username=request.username,
            content=request.content,
            post_type=request.post_type,
            target_post_url=request.target_post_url,
            media_type=request.media_type,
        )

        response = PostAnalysisResponse(
            scores=ScoresResponse(**result.scores.to_dict()),
            breakdown=ProbabilitiesResponse(
                p_favorite=result.probabilities.p_favorite,
                p_reply=result.probabilities.p_reply,
                p_repost=result.probabilities.p_repost,
                p_quote=result.probabilities.p_quote,
                p_click=result.probabilities.p_click,
                p_profile_click=result.probabilities.p_profile_click,
                p_share=result.probabilities.p_share,
                p_dwell=result.probabilities.p_dwell,
                p_video_view=result.probabilities.p_video_view,
                p_follow_author=result.probabilities.p_follow_author,
                p_not_interested=result.probabilities.p_not_interested,
                p_block_author=result.probabilities.p_block_author,
                p_mute_author=result.probabilities.p_mute_author,
                p_report=result.probabilities.p_report,
            ),
            quick_tips=result.quick_tips,
        )

        if result.context:
            response.context = ContextResponse(
                target_post_id=result.context.target_post.tweet_id,
                target_post_content=result.context.target_post.content,
                target_author=result.context.target_post.username,
                context_adjustments=result.context.context_adjustments,
                recommendations=result.context.recommendations,
            )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Main App 업데이트**

```python
# backend/src/main.py
"""XEO Backend API Server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.config import get_settings

settings = get_settings()

app = FastAPI(
    title="XEO API",
    description="X Score Optimizer - Post score prediction and optimization",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "XEO API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
```

**Step 5: pyproject.toml 업데이트**

```bash
cd backend && uv add pydantic-settings
```

**Step 6: 서버 실행 테스트**

```bash
cd backend && uv run python -m src.main
# 또는
cd backend && uv run uvicorn src.main:app --reload
```

**Step 7: API 테스트**

```bash
# Health check
curl http://localhost:8000/health

# Profile analysis
curl http://localhost:8000/api/v1/profile/elonmusk/analyze

# Post analysis
curl -X POST http://localhost:8000/api/v1/post/analyze \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "content": "Hello world! 🌍"}'
```

**Step 8: 커밋**

```bash
git add backend/src/
git commit -m "feat(api): add FastAPI server with profile and post routes"
```

---

## Phase 2: Frontend (Next.js)

### Task 2.1: Next.js 프로젝트 초기화

**Files:**
- Create: `frontend/` 디렉토리 전체

**Step 1: Next.js 프로젝트 생성**

```bash
cd /Users/aisteve/Documents/GitHub/XEO
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

**Step 2: 추가 의존성 설치**

```bash
cd frontend
npm install recharts @radix-ui/react-slot class-variance-authority clsx tailwind-merge lucide-react
```

**Step 3: 커밋**

```bash
git add frontend/
git commit -m "feat(frontend): initialize Next.js project with Tailwind"
```

---

### Task 2.2: API Client 및 Types 설정

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/types/api.ts`

**Step 1: Types 정의**

```typescript
// frontend/src/types/api.ts
export interface PentagonScores {
  reach: number;
  engagement: number;
  virality: number;
  quality: number;
  longevity: number;
}

export interface Insight {
  category: string;
  message: string;
  priority: "high" | "medium" | "low";
}

export interface Recommendation {
  action: string;
  expected_impact: string;
  description: string;
}

export interface ProfileAnalysis {
  username: string;
  scores: PentagonScores;
  insights: Insight[];
  recommendations: Recommendation[];
}

export interface PostContext {
  target_post_id: string;
  target_post_content: string;
  target_author: string;
  context_adjustments: Record<string, string>;
  recommendations: string[];
}

export interface PostAnalysis {
  scores: PentagonScores;
  breakdown: Record<string, number>;
  quick_tips: string[];
  context?: PostContext;
}

export interface AnalyzePostRequest {
  username: string;
  content: string;
  post_type: "original" | "reply" | "quote" | "thread";
  target_post_url?: string;
  media_type?: "image" | "video" | "gif";
}
```

**Step 2: API Client 구현**

```typescript
// frontend/src/lib/api.ts
import { ProfileAnalysis, PostAnalysis, AnalyzePostRequest } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async analyzeProfile(username: string): Promise<ProfileAnalysis> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/profile/${username}/analyze`
    );

    if (!response.ok) {
      throw new Error(`Failed to analyze profile: ${response.statusText}`);
    }

    return response.json();
  }

  async analyzePost(request: AnalyzePostRequest): Promise<PostAnalysis> {
    const response = await fetch(`${this.baseUrl}/api/v1/post/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze post: ${response.statusText}`);
    }

    return response.json();
  }
}

export const api = new APIClient();
```

**Step 3: 커밋**

```bash
git add frontend/src/lib/ frontend/src/types/
git commit -m "feat(frontend): add API client and types"
```

---

### Task 2.3: 레이더 차트 컴포넌트

**Files:**
- Create: `frontend/src/components/charts/RadarChart.tsx`

**Step 1: RadarChart 구현**

```tsx
// frontend/src/components/charts/RadarChart.tsx
"use client";

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { PentagonScores } from "@/types/api";

interface RadarChartProps {
  scores: PentagonScores;
  size?: number;
}

const LABELS = {
  reach: "도달률",
  engagement: "참여도",
  virality: "바이럴성",
  quality: "품질",
  longevity: "지속성",
};

export function RadarChart({ scores, size = 300 }: RadarChartProps) {
  const data = Object.entries(scores).map(([key, value]) => ({
    subject: LABELS[key as keyof typeof LABELS],
    value: value,
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={size}>
      <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: "#6b7280", fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "#9ca3af", fontSize: 10 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)}점`, "점수"]}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
```

**Step 2: 커밋**

```bash
git add frontend/src/components/
git commit -m "feat(frontend): add radar chart component"
```

---

### Task 2.4: 랜딩 페이지 구현

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/[username]/page.tsx`
- Create: `frontend/src/app/[username]/loading.tsx`

**Step 1: 랜딩 페이지**

```tsx
// frontend/src/app/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [username, setUsername] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      router.push(`/${username.replace("@", "")}`);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-gradient-to-b from-gray-900 to-black">
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-5xl font-bold text-white mb-4">
          X Score Optimizer
        </h1>
        <p className="text-xl text-gray-400 mb-12">
          X 알고리즘 기반으로 포스트 스코어를 예측하고 최적화하세요
        </p>

        <form onSubmit={handleSubmit} className="flex gap-4 justify-center">
          <div className="relative flex-1 max-w-md">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
              @
            </span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="유저네임을 입력하세요"
              className="w-full pl-10 pr-4 py-4 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
            />
          </div>
          <button
            type="submit"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors text-lg"
          >
            분석하기
          </button>
        </form>

        <p className="mt-8 text-gray-500 text-sm">
          가입 없이 무료로 바로 사용할 수 있습니다
        </p>
      </div>
    </main>
  );
}
```

**Step 2: 프로필 분석 페이지**

```tsx
// frontend/src/app/[username]/page.tsx
import { api } from "@/lib/api";
import { RadarChart } from "@/components/charts/RadarChart";
import Link from "next/link";

interface Props {
  params: { username: string };
}

export default async function ProfilePage({ params }: Props) {
  const { username } = params;

  let analysis;
  let error = null;

  try {
    analysis = await api.analyzeProfile(username);
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to analyze profile";
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto text-center py-20">
          <h1 className="text-2xl text-red-500 mb-4">분석 실패</h1>
          <p className="text-gray-400">{error}</p>
          <Link href="/" className="text-blue-500 hover:underline mt-4 inline-block">
            돌아가기
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">@{username}</h1>
            <p className="text-gray-400">프로필 분석 결과</p>
          </div>
          <Link
            href={`/${username}/compose`}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            포스트 작성
          </Link>
        </div>

        {/* Score Chart */}
        <div className="bg-gray-800 rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">스코어 차트</h2>
          <div className="flex justify-center">
            <RadarChart scores={analysis.scores} size={350} />
          </div>
          <div className="grid grid-cols-5 gap-4 mt-6">
            {Object.entries(analysis.scores).map(([key, value]) => (
              <div key={key} className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {value.toFixed(0)}
                </div>
                <div className="text-sm text-gray-400 capitalize">{key}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Insights */}
        <div className="bg-gray-800 rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">인사이트</h2>
          <div className="space-y-4">
            {analysis.insights.map((insight, i) => (
              <div
                key={i}
                className={`p-4 rounded-lg border-l-4 ${
                  insight.priority === "high"
                    ? "bg-red-900/20 border-red-500"
                    : insight.priority === "medium"
                    ? "bg-yellow-900/20 border-yellow-500"
                    : "bg-green-900/20 border-green-500"
                }`}
              >
                <div className="text-sm text-gray-400 mb-1">
                  {insight.category}
                </div>
                <div className="text-white">{insight.message}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-gray-800 rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">추천</h2>
          <div className="space-y-4">
            {analysis.recommendations.map((rec, i) => (
              <div key={i} className="p-4 bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-blue-400 font-medium">{rec.action}</span>
                  <span className="text-green-400 text-sm">
                    {rec.expected_impact}
                  </span>
                </div>
                <p className="text-gray-300">{rec.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
```

**Step 3: Loading 컴포넌트**

```tsx
// frontend/src/app/[username]/loading.tsx
export default function Loading() {
  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-700 rounded w-48 mb-4"></div>
          <div className="h-6 bg-gray-700 rounded w-32 mb-8"></div>

          <div className="bg-gray-800 rounded-2xl p-6 mb-8">
            <div className="h-[350px] bg-gray-700 rounded"></div>
          </div>

          <div className="bg-gray-800 rounded-2xl p-6">
            <div className="h-6 bg-gray-700 rounded w-24 mb-4"></div>
            <div className="space-y-4">
              <div className="h-20 bg-gray-700 rounded"></div>
              <div className="h-20 bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
```

**Step 4: 커밋**

```bash
git add frontend/src/app/
git commit -m "feat(frontend): add landing and profile pages"
```

---

### Task 2.5: 포스트 작성 페이지

**Files:**
- Create: `frontend/src/app/[username]/compose/page.tsx`
- Create: `frontend/src/components/editor/PostEditor.tsx`

**Step 1: PostEditor 컴포넌트**

```tsx
// frontend/src/components/editor/PostEditor.tsx
"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import { PostAnalysis, PentagonScores } from "@/types/api";
import { RadarChart } from "@/components/charts/RadarChart";
import { debounce } from "@/lib/utils";

interface PostEditorProps {
  username: string;
}

export function PostEditor({ username }: PostEditorProps) {
  const [content, setContent] = useState("");
  const [postType, setPostType] = useState<"original" | "reply" | "quote">("original");
  const [targetUrl, setTargetUrl] = useState("");
  const [mediaType, setMediaType] = useState<"image" | "video" | "gif" | undefined>();
  const [analysis, setAnalysis] = useState<PostAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  const analyzePost = useCallback(
    debounce(async (text: string) => {
      if (!text.trim()) {
        setAnalysis(null);
        return;
      }

      setLoading(true);
      try {
        const result = await api.analyzePost({
          username,
          content: text,
          post_type: postType,
          target_post_url: targetUrl || undefined,
          media_type: mediaType,
        });
        setAnalysis(result);
      } catch (error) {
        console.error("Analysis failed:", error);
      } finally {
        setLoading(false);
      }
    }, 500),
    [username, postType, targetUrl, mediaType]
  );

  useEffect(() => {
    analyzePost(content);
  }, [content, analyzePost]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    alert("클립보드에 복사되었습니다!");
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Editor */}
      <div className="space-y-6">
        {/* Post Type Selector */}
        <div className="flex gap-2">
          {(["original", "reply", "quote"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setPostType(type)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                postType === type
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {type === "original" ? "원본" : type === "reply" ? "답글" : "인용"}
            </button>
          ))}
        </div>

        {/* Target URL (for reply/quote) */}
        {postType !== "original" && (
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="대상 포스트 URL (https://x.com/...)"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        )}

        {/* Content Editor */}
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="포스트 내용을 입력하세요..."
            className="w-full h-48 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <div className="absolute bottom-3 right-3 text-gray-500 text-sm">
            {content.length}/280
          </div>
        </div>

        {/* Media Type */}
        <div className="flex gap-2">
          <span className="text-gray-400 py-2">미디어:</span>
          {[undefined, "image", "video", "gif"].map((type) => (
            <button
              key={type ?? "none"}
              onClick={() => setMediaType(type as any)}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                mediaType === type
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {type ?? "없음"}
            </button>
          ))}
        </div>

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          disabled={!content}
          className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-semibold rounded-lg transition-colors"
        >
          클립보드에 복사
        </button>
      </div>

      {/* Analysis Results */}
      <div className="space-y-6">
        {loading && (
          <div className="text-center py-8 text-gray-400">분석 중...</div>
        )}

        {analysis && !loading && (
          <>
            {/* Radar Chart */}
            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-4">
                예상 스코어
              </h3>
              <RadarChart scores={analysis.scores} size={280} />
              <div className="text-center mt-2">
                <span className="text-2xl font-bold text-blue-400">
                  {(
                    Object.values(analysis.scores).reduce((a, b) => a + b, 0) / 5
                  ).toFixed(0)}
                </span>
                <span className="text-gray-400 ml-2">/ 100</span>
              </div>
            </div>

            {/* Quick Tips */}
            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-4">
                빠른 팁
              </h3>
              <ul className="space-y-2">
                {analysis.quick_tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-300">
                    <span className="text-yellow-400">💡</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>

            {/* Context (for reply/quote) */}
            {analysis.context && (
              <div className="bg-gray-800 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  컨텍스트 분석
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-gray-700/50 rounded-lg">
                    <div className="text-sm text-gray-400">대상 포스트</div>
                    <div className="text-white">
                      @{analysis.context.target_author}
                    </div>
                    <div className="text-gray-300 text-sm mt-1">
                      {analysis.context.target_post_content.slice(0, 100)}...
                    </div>
                  </div>
                  {Object.entries(analysis.context.context_adjustments).map(
                    ([key, value]) => (
                      <div
                        key={key}
                        className="flex justify-between text-sm"
                      >
                        <span className="text-gray-400">{key}</span>
                        <span
                          className={
                            value.startsWith("+")
                              ? "text-green-400"
                              : "text-red-400"
                          }
                        >
                          {value}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Utils 함수 추가**

```typescript
// frontend/src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
```

**Step 3: Compose 페이지**

```tsx
// frontend/src/app/[username]/compose/page.tsx
import { PostEditor } from "@/components/editor/PostEditor";
import Link from "next/link";

interface Props {
  params: { username: string };
}

export default function ComposePage({ params }: Props) {
  const { username } = params;

  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href={`/${username}`}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← 프로필로 돌아가기
          </Link>
          <h1 className="text-2xl font-bold text-white">포스트 작성</h1>
          <span className="text-gray-500">@{username}</span>
        </div>

        <PostEditor username={username} />
      </div>
    </main>
  );
}
```

**Step 4: 커밋**

```bash
git add frontend/
git commit -m "feat(frontend): add post compose page with real-time analysis"
```

---

## Phase 3: Integration & Deployment

### Task 3.1: 환경 변수 설정

**Files:**
- Create: `frontend/.env.local.example`
- Update: `backend/.env.example`

```bash
# frontend/.env.local.example
NEXT_PUBLIC_API_URL=http://localhost:8000

# backend/.env.example (update)
# ... existing ...
OPENAI_API_KEY=your-openai-key  # For future optimization feature
```

### Task 3.2: Vercel 배포 설정

**Files:**
- Create: `frontend/vercel.json`

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-url.com/api/:path*"
    }
  ]
}
```

### Task 3.3: Backend Docker 설정 (Optional)

**Files:**
- Create: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 전체 태스크 요약

| Phase | Task | 설명 | 예상 시간 |
|-------|------|------|----------|
| 1.1 | Feature Extractor | 피처 추출 모듈 | - |
| 1.2 | Weighted Scorer | 5각형 스코어 계산기 | - |
| 1.3 | Profile Analyzer | 프로필 분석 서비스 | - |
| 1.4 | Score Predictor | 포스트 스코어 예측 | - |
| 1.5 | FastAPI App | API 서버 설정 | - |
| 2.1 | Next.js Init | 프론트엔드 초기화 | - |
| 2.2 | API Client | API 클라이언트 & Types | - |
| 2.3 | Radar Chart | 레이더 차트 컴포넌트 | - |
| 2.4 | Landing Page | 랜딩 & 프로필 페이지 | - |
| 2.5 | Compose Page | 포스트 작성 페이지 | - |
| 3.1 | Environment | 환경 변수 설정 | - |
| 3.2 | Vercel Deploy | Vercel 배포 | - |
| 3.3 | Docker | Backend Docker화 | - |

---

## 다음 단계 (Phase 4)

Phase 1-3 완료 후 추가 기능:

1. **콘텐츠 최적화 API** - OpenAI 기반 콘텐츠 리라이팅
2. **Supabase 캐싱** - API 응답 캐싱
3. **WebSocket 실시간 스코어** - 타이핑 중 실시간 업데이트
4. **히스토리 저장** - 분석 기록 저장 및 조회

---

*Plan created: 2025-01-25*
