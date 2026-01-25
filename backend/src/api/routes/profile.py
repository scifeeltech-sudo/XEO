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
