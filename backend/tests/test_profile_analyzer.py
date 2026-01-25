# backend/tests/test_profile_analyzer.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.profile_analyzer import ProfileAnalyzer, ProfileAnalysisResult
from src.services.sela_api_client import ProfileData, TweetData

@pytest.mark.asyncio
async def test_analyze_profile():
    """프로필 분석 테스트"""
    # Create proper ProfileData object
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

    with patch("src.services.profile_analyzer.SelaAPIClient") as MockClient:
        mock_client = MockClient.return_value
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.profile = mock_profile
        mock_client.get_twitter_profile = AsyncMock(return_value=mock_response)

        analyzer = ProfileAnalyzer()
        analyzer.client = mock_client

        result = await analyzer.analyze("testuser")

        assert isinstance(result, ProfileAnalysisResult)
        assert result.username == "testuser"
        assert result.scores is not None
        assert len(result.insights) >= 0
