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

    reach: float
    engagement: float
    virality: float
    quality: float
    longevity: float

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
        # Ensure minimum engagement rate to prevent scores from collapsing to 0
        base_engagement = max(profile_features.avg_engagement_rate, 0.03)

        probs = ActionProbabilities(
            p_favorite=max(base_engagement * 0.6, 0.02),
            p_reply=max(base_engagement * 0.15, 0.01),
            p_repost=max(base_engagement * 0.15, 0.01),  # Minimum for virality
            p_quote=max(base_engagement * 0.05, 0.005),  # Minimum for virality
            p_click=0.20,
            p_profile_click=0.10,
            p_share=max(base_engagement * 0.05, 0.005),  # Minimum for virality
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
