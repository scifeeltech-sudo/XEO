# backend/tests/test_score_predictor.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.score_predictor import ScorePredictor, PostAnalysisResult
from src.services.sela_api_client import ProfileData, TweetData

@pytest.mark.asyncio
async def test_predict_original_post():
    """원본 포스트 스코어 예측"""
    # Create mock profile data
    tweets = [
        TweetData(
            tweet_id="1",
            username="testuser",
            content="Hello world!",
            tweet_url="/testuser/1",
            likes_count=100,
            retweets_count=10,
            replies_count=5,
            views_count=1000,
        )
    ]
    mock_profile = ProfileData(username="testuser", tweets=tweets)

    with patch("src.services.score_predictor.SelaAPIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.profile = mock_profile
        mock_client.get_twitter_profile = AsyncMock(return_value=mock_response)

        predictor = ScorePredictor()
        predictor.client = mock_client

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
    # Create mock profile data
    tweets = [
        TweetData(
            tweet_id="1",
            username="testuser",
            content="Hello world!",
            tweet_url="/testuser/1",
            likes_count=100,
            retweets_count=10,
            replies_count=5,
            views_count=1000,
        )
    ]
    mock_profile = ProfileData(username="testuser", tweets=tweets)

    # Create mock target tweet
    target_tweet = TweetData(
        tweet_id="123456",
        username="elonmusk",
        content="This is a viral tweet",
        tweet_url="/elonmusk/status/123456",
        likes_count=100000,
        retweets_count=10000,
        replies_count=5000,
        views_count=10000000,
    )

    with patch("src.services.score_predictor.SelaAPIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.profile = mock_profile
        mock_client.get_twitter_profile = AsyncMock(return_value=mock_response)
        mock_client.get_post_context = AsyncMock(return_value=target_tweet)

        predictor = ScorePredictor()
        predictor.client = mock_client

        result = await predictor.predict(
            username="testuser",
            content="Great point! I agree.",
            post_type="reply",
            target_post_url="https://x.com/elonmusk/status/123456",
        )

        assert result.context is not None
        # Reply to popular account should have context adjustments
        assert len(result.context.context_adjustments) > 0
