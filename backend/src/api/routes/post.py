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
