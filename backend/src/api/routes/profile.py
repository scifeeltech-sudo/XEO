"""Profile analysis API routes."""

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.profile_analyzer import ProfileAnalyzer

router = APIRouter()
analyzer = ProfileAnalyzer()

# Simple in-memory cache with TTL
_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def get_cached(key: str) -> Any | None:
    """Get cached value if not expired."""
    if key in _cache:
        value, expires_at = _cache[key]
        if time.time() < expires_at:
            return value
        del _cache[key]
    return None


def set_cached(key: str, value: Any) -> None:
    """Set cache value with TTL."""
    _cache[key] = (value, time.time() + CACHE_TTL_SECONDS)


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
    summary: str
    scores: ProfileScores
    insights: list[InsightResponse]
    recommendations: list[RecommendationResponse]


@router.get("/{username}/analyze", response_model=ProfileAnalysisResponse)
async def analyze_profile(username: str, refresh: bool = False):
    """Analyze a user's X profile."""
    cache_key = f"profile:{username.lower()}"

    # Check cache first (unless refresh requested)
    if not refresh:
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    try:
        result = await analyzer.analyze(username)

        response = ProfileAnalysisResponse(
            username=result.username,
            summary=result.summary,
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

        # Cache the response
        set_cached(cache_key, response)

        return response
    except ValueError as e:
        error_msg = str(e)
        if "offline" in error_msg.lower() or "failed to fetch" in error_msg.lower():
            raise HTTPException(status_code=502, detail=error_msg)
        raise HTTPException(status_code=404, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
