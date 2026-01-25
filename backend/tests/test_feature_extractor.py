# backend/tests/test_feature_extractor.py
import pytest
from src.engine.feature_extractor import PostFeatures, ProfileFeatures, extract_post_features, extract_profile_features

def test_extract_post_features_basic():
    """기본 포스트 피처 추출 테스트"""
    content = "Hello world! 🌍 What do you think? #tech"
    features = extract_post_features(content)

    assert features.char_count == len(content)
    assert features.word_count == 8  # includes emoji as separate word
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
