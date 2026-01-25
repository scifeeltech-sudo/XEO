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
