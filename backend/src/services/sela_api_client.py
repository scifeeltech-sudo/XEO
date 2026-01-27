"""
Sela API Client for X/Twitter data scraping.

Supports:
- TWITTER_PROFILE: Scrape Twitter user profiles with recent posts
- TWITTER_POST: Scrape Twitter posts (currently limited)
"""

import os
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, PrivateAttr

load_dotenv()


class ScrapeType(str, Enum):
    TWITTER_PROFILE = "TWITTER_PROFILE"
    TWITTER_POST = "TWITTER_POST"
    HTML = "HTML"
    GOOGLE_SEARCH = "GOOGLE_SEARCH"


class TweetData(BaseModel):
    """Parsed tweet data from Sela API."""

    tweet_id: str
    username: str
    content: str
    quote_content: str | None = None
    images: list[str] = Field(default_factory=list)
    videos: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    tweet_url: str
    is_retweet: bool = False
    is_quote: bool = False
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    views_count: int = 0

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TweetData":
        """Parse tweet data from Sela API response."""
        posted_at = None
        if data.get("postedAt"):
            try:
                posted_at = datetime.fromisoformat(
                    data["postedAt"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Handle image field - can be string, list, or None
        images_raw = data.get("image", [])
        if isinstance(images_raw, str):
            images = [images_raw] if images_raw else []
        elif isinstance(images_raw, list):
            images = images_raw
        else:
            images = []

        # Handle video field - can be string, list, or None
        videos_raw = data.get("video", [])
        if isinstance(videos_raw, str):
            videos = [videos_raw] if videos_raw else []
        elif isinstance(videos_raw, list):
            videos = videos_raw
        else:
            videos = []

        return cls(
            tweet_id=str(data.get("tweetId", "")),
            username=data.get("username", ""),
            content=data.get("content", ""),
            quote_content=data.get("quoteContent"),
            images=images,
            videos=videos,
            posted_at=posted_at,
            tweet_url=data.get("tweetUrl", ""),
            is_retweet=bool(data.get("isRetweet", False)),
            is_quote=bool(data.get("isQuote", False)),
            likes_count=int(data.get("likesCount", 0) or 0),
            retweets_count=int(data.get("retweetsCount", 0) or 0),
            replies_count=int(data.get("repliesCount", 0) or 0),
            views_count=int(data.get("viewsCount", 0) or 0),
        )

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (interactions / views)."""
        if self.views_count == 0:
            return 0.0
        total_engagement = (
            self.likes_count + self.retweets_count + self.replies_count
        )
        return total_engagement / self.views_count

    @property
    def has_media(self) -> bool:
        """Check if tweet has media attachments."""
        return bool(self.images or self.videos)

    @property
    def full_url(self) -> str:
        """Get full tweet URL."""
        if self.tweet_url.startswith("http"):
            return self.tweet_url
        return f"https://x.com{self.tweet_url}"


class ProfileData(BaseModel):
    """Parsed profile data from Sela API."""

    username: str
    tweets: list[TweetData] = Field(default_factory=list)
    job_id: str | None = None

    # Cached aggregates (computed in single pass) - Pydantic V2 PrivateAttr
    _aggregates: dict[str, float] | None = PrivateAttr(default=None)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ProfileData":
        """Parse profile data from Sela API response."""
        inner_data = data.get("data", {})
        result = inner_data.get("result", [])

        tweets = [TweetData.from_api_response(t) for t in result]

        # Extract username from first tweet or URL
        username = ""
        if tweets:
            username = tweets[0].username
        elif inner_data.get("url"):
            # Parse from URL: https://x.com/username
            url = inner_data["url"]
            parts = url.rstrip("/").split("/")
            if parts:
                username = parts[-1]

        return cls(
            username=username,
            tweets=tweets,
            job_id=inner_data.get("jobId"),
        )

    def _compute_aggregates(self) -> dict[str, float]:
        """Compute all aggregates in a single pass over tweets.

        This optimizes from O(n*9) to O(n) when multiple properties are accessed.
        """
        if self._aggregates is not None:
            return self._aggregates

        if not self.tweets:
            self._aggregates = {
                "total_engagement_rate": 0.0,
                "total_likes": 0.0,
                "total_retweets": 0.0,
                "total_replies": 0.0,
                "total_views": 0.0,
                "retweet_count": 0.0,
                "quote_count": 0.0,
                "media_count": 0.0,
                "tweet_count": 0.0,
            }
            return self._aggregates

        # Single pass aggregation
        total_engagement_rate = 0.0
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        total_views = 0
        retweet_count = 0
        quote_count = 0
        media_count = 0

        for t in self.tweets:
            total_engagement_rate += t.engagement_rate
            total_likes += t.likes_count
            total_retweets += t.retweets_count
            total_replies += t.replies_count
            total_views += t.views_count
            if t.is_retweet:
                retweet_count += 1
            if t.is_quote:
                quote_count += 1
            if t.has_media:
                media_count += 1

        tweet_count = len(self.tweets)
        self._aggregates = {
            "total_engagement_rate": total_engagement_rate,
            "total_likes": float(total_likes),
            "total_retweets": float(total_retweets),
            "total_replies": float(total_replies),
            "total_views": float(total_views),
            "retweet_count": float(retweet_count),
            "quote_count": float(quote_count),
            "media_count": float(media_count),
            "tweet_count": float(tweet_count),
        }
        return self._aggregates

    @property
    def avg_engagement_rate(self) -> float:
        """Calculate average engagement rate across all tweets."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["total_engagement_rate"] / agg["tweet_count"]

    @property
    def avg_likes(self) -> float:
        """Calculate average likes per tweet."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["total_likes"] / agg["tweet_count"]

    @property
    def avg_retweets(self) -> float:
        """Calculate average retweets per tweet."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["total_retweets"] / agg["tweet_count"]

    @property
    def avg_replies(self) -> float:
        """Calculate average replies per tweet."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["total_replies"] / agg["tweet_count"]

    @property
    def avg_views(self) -> float:
        """Calculate average views per tweet."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["total_views"] / agg["tweet_count"]

    @property
    def original_tweets(self) -> list[TweetData]:
        """Get only original tweets (not retweets)."""
        # This still needs iteration as it returns filtered list
        return [t for t in self.tweets if not t.is_retweet]

    @property
    def retweet_ratio(self) -> float:
        """Calculate ratio of retweets to total tweets."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["retweet_count"] / agg["tweet_count"]

    @property
    def quote_ratio(self) -> float:
        """Calculate ratio of quote tweets to total tweets."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["quote_count"] / agg["tweet_count"]

    @property
    def media_ratio(self) -> float:
        """Calculate ratio of tweets with media."""
        agg = self._compute_aggregates()
        if agg["tweet_count"] == 0:
            return 0.0
        return agg["media_count"] / agg["tweet_count"]


class ScrapeResponse(BaseModel):
    """Response from Sela API scrape request."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    profile: ProfileData | None = None

    def parse_profile(self) -> ProfileData | None:
        """Parse profile data from response."""
        if self.success and self.data:
            return ProfileData.from_api_response(self.data)
        return None


class SelaAPIClient:
    """Client for Sela Network scraping API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        principal_id: str | None = None,
    ):
        self.base_url = base_url or os.getenv("SELA_API_BASE_URL")
        self.api_key = api_key or os.getenv("SELA_API_KEY")
        self.principal_id = principal_id or os.getenv("SELA_PRINCIPAL_ID")

        if not self.base_url or not self.api_key:
            raise ValueError("SELA_API_BASE_URL and SELA_API_KEY must be set")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _scrape(
        self,
        url: str,
        scrape_type: ScrapeType,
        post_count: int | None = None,
        reply_count: int | None = None,
        timeout_ms: int = 60000,
    ) -> ScrapeResponse:
        """Execute a scrape request via /api/rpc/scrapeUrl endpoint."""
        payload = {
            "url": url,
            "scrapeType": scrape_type.value,
            "timeoutMs": timeout_ms,
        }

        if self.principal_id:
            payload["principalId"] = self.principal_id

        if post_count is not None:
            payload["postCount"] = post_count

        if reply_count is not None:
            payload["replyCount"] = reply_count

        async with httpx.AsyncClient(
            timeout=max(timeout_ms / 1000 + 30, 90)
        ) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/rpc/scrapeUrl",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return ScrapeResponse(success=True, data=data)
            except httpx.HTTPStatusError as e:
                return ScrapeResponse(
                    success=False,
                    error=f"HTTP {e.response.status_code}: {e.response.text}",
                )
            except httpx.RequestError as e:
                return ScrapeResponse(success=False, error=str(e))

    async def get_twitter_profile(
        self,
        username: str,
        post_count: int = 20,
    ) -> ScrapeResponse:
        """
        Scrape a Twitter user profile with recent posts.

        Args:
            username: Twitter username (without @)
            post_count: Number of recent posts to retrieve (default: 20)

        Returns:
            ScrapeResponse with profile data including recent posts
        """
        # Remove @ if present
        username = username.lstrip("@")
        url = f"https://x.com/{username}"
        response = await self._scrape(
            url,
            ScrapeType.TWITTER_PROFILE,
            post_count=post_count,
        )

        # Parse profile data
        if response.success:
            response.profile = response.parse_profile()

        return response

    async def get_twitter_post(
        self,
        post_url: str,
        reply_count: int = 10,
    ) -> ScrapeResponse:
        """
        Scrape a Twitter post.

        Note: This endpoint currently returns empty results.
        Use get_twitter_profile to get post data instead.

        Args:
            post_url: Full URL of the Twitter post
            reply_count: Number of replies to retrieve (default: 10)

        Returns:
            ScrapeResponse with post data and replies
        """
        return await self._scrape(
            post_url,
            ScrapeType.TWITTER_POST,
            reply_count=reply_count,
        )

    async def get_post_context(self, post_url: str) -> TweetData | None:
        """
        Get context for a specific post.

        Searches through user's recent posts (up to 200) to find the target tweet.

        Args:
            post_url: Full URL of the Twitter post
                      e.g., https://x.com/elonmusk/status/1234567890

        Returns:
            TweetData if found, None otherwise
        """
        # Parse username and tweet_id from URL
        # Format: https://x.com/username/status/tweet_id
        try:
            parts = post_url.rstrip("/").split("/")
            if "status" in parts:
                status_idx = parts.index("status")
                username = parts[status_idx - 1]
                tweet_id = parts[status_idx + 1]
            else:
                return None
        except (ValueError, IndexError):
            return None

        # Search through profile tweets incrementally (50 -> 100 -> 150 -> 200)
        for post_count in [50, 100, 150, 200]:
            response = await self.get_twitter_profile(username, post_count=post_count)
            if response.profile:
                for tweet in response.profile.tweets:
                    if tweet.tweet_id == tweet_id:
                        return tweet

        # Tweet not found in recent 200 posts
        return None


# Convenience functions for testing
async def test_profile(username: str = "elonmusk") -> ProfileData | None:
    """Test profile fetching."""
    client = SelaAPIClient()
    result = await client.get_twitter_profile(username, post_count=10)
    return result.profile


async def test_post_context(post_url: str) -> TweetData | None:
    """Test post context fetching."""
    client = SelaAPIClient()
    return await client.get_post_context(post_url)


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=== Sela API Client Test ===\n")

        # Test profile
        print("1. Testing profile fetch...")
        profile = await test_profile("elonmusk")
        if profile:
            print(f"   Username: {profile.username}")
            print(f"   Tweets: {len(profile.tweets)}")
            print(f"   Avg Engagement Rate: {profile.avg_engagement_rate:.4f}")
            print(f"   Avg Likes: {profile.avg_likes:,.0f}")
            print(f"   Retweet Ratio: {profile.retweet_ratio:.2%}")
            print(f"   Media Ratio: {profile.media_ratio:.2%}")

        # Test post context
        print("\n2. Testing post context fetch...")
        if profile and profile.tweets:
            test_url = profile.tweets[0].full_url
            print(f"   URL: {test_url}")
            tweet = await test_post_context(test_url)
            if tweet:
                print(f"   Found: {tweet.content[:50]}...")
                print(f"   Likes: {tweet.likes_count:,}")

    asyncio.run(main())
