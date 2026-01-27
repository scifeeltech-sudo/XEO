"""Post analysis API routes."""

from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from src.services.score_predictor import ScorePredictor
from src.services.content_optimizer import ContentOptimizer
from src.db.supabase_client import SupabaseCache

router = APIRouter()
predictor = ScorePredictor()
optimizer = ContentOptimizer()
cache = SupabaseCache()


class PostAnalyzeRequest(BaseModel):
    username: str
    content: str
    post_type: Literal["original", "reply", "quote", "thread"] = "original"
    target_post_url: Optional[str] = None
    media_type: Optional[Literal["image", "video", "gif"]] = None
    target_language: Optional[Literal["ko", "en", "ja", "zh"]] = None  # Target post language for reply/quote


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


class QuickTipResponse(BaseModel):
    tip_id: str
    description: str
    impact: str
    target_score: str
    selectable: bool


class ContextResponse(BaseModel):
    target_post_id: str
    target_post_content: str
    target_author: str
    context_adjustments: dict[str, str]
    recommendations: list[str]


class PostAnalysisResponse(BaseModel):
    scores: ScoresResponse
    breakdown: ProbabilitiesResponse
    quick_tips: list[QuickTipResponse]
    context: Optional[ContextResponse] = None


@router.post("/analyze", response_model=PostAnalysisResponse)
async def analyze_post(request: PostAnalyzeRequest, background_tasks: BackgroundTasks):
    """Analyze a post and predict scores."""
    try:
        result = await predictor.predict(
            username=request.username,
            content=request.content,
            post_type=request.post_type,
            target_post_url=request.target_post_url,
            media_type=request.media_type,
            target_language=request.target_language,
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
            quick_tips=[
                QuickTipResponse(
                    tip_id=tip.tip_id,
                    description=tip.description,
                    impact=tip.impact,
                    target_score=tip.target_score,
                    selectable=tip.selectable,
                )
                for tip in result.quick_tips
            ],
        )

        if result.context:
            response.context = ContextResponse(
                target_post_id=result.context.target_post.tweet_id,
                target_post_content=result.context.target_post.content,
                target_author=result.context.target_post.username,
                context_adjustments=result.context.context_adjustments,
                recommendations=result.context.recommendations,
            )

        # Log user activity in background
        target_handle = result.context.target_post.username if result.context else None
        background_tasks.add_task(
            cache.log_user_activity,
            user_handle=request.username,
            action_type=request.post_type,
            target_handle=target_handle,
            target_url=request.target_post_url,
            post_content=request.content,
            scores=result.scores.to_dict(),
            quick_tips=[
                {"tip_id": t.tip_id, "description": t.description, "impact": t.impact}
                for t in result.quick_tips
            ],
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Apply Tips Endpoint ---

class ApplyTipsRequest(BaseModel):
    username: str
    original_content: str
    selected_tips: list[str]  # List of tip_ids
    language: str = "ko"  # Target language for suggestions


class AppliedTipResponse(BaseModel):
    tip_id: str
    description: str
    impact: str


class ApplyTipsResponse(BaseModel):
    original_content: str
    suggested_content: str
    applied_tips: list[AppliedTipResponse]
    predicted_improvement: dict[str, str]


@router.post("/apply-tips", response_model=ApplyTipsResponse)
async def apply_tips(request: ApplyTipsRequest):
    """Apply selected tips to generate optimized post suggestion."""
    try:
        result = await optimizer.apply_tips(
            username=request.username,
            original_content=request.original_content,
            selected_tips=request.selected_tips,
            language=request.language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Post Context Endpoint ---

class PostAuthorResponse(BaseModel):
    username: str
    display_name: Optional[str] = None
    followers_count: int
    verified: bool = False


class PostMetricsResponse(BaseModel):
    likes: int
    reposts: int
    replies: int
    quotes: int = 0
    views: int


class PostContentResponse(BaseModel):
    text: str
    media: list[dict] = []
    hashtags: list[str] = []


class PostContextAnalysis(BaseModel):
    age_minutes: int
    freshness: str
    virality_status: str
    reply_saturation: str


class OpportunityScore(BaseModel):
    overall: int
    factors: dict[str, int]


class PostContextResponse(BaseModel):
    post_id: str
    post_url: str
    author: PostAuthorResponse
    content: PostContentResponse
    metrics: PostMetricsResponse
    created_at: Optional[str] = None
    analysis: PostContextAnalysis
    opportunity_score: OpportunityScore
    tips: list[str]


@router.get("/context", response_model=PostContextResponse)
async def get_post_context(url: str = Query(..., description="Target post URL")):
    """Get context information for a target post (for reply/quote)."""
    try:
        result = await optimizer.get_post_context(url)
        if not result:
            raise HTTPException(status_code=404, detail="Post not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Optimize Endpoint ---

class OptimizeRequest(BaseModel):
    username: str
    content: str
    target_score: Literal["reach", "engagement", "virality", "quality", "longevity"]
    style: Literal["conservative", "balanced", "aggressive"] = "balanced"


class ChangeResponse(BaseModel):
    type: str
    impact: str


class OptimizedVersionResponse(BaseModel):
    content: str
    style: str
    predicted_scores: ScoresResponse
    changes: list[ChangeResponse]


class OptimizeResponse(BaseModel):
    original_content: str
    optimized_versions: list[OptimizedVersionResponse]


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_post(request: OptimizeRequest):
    """Generate AI-optimized versions of a post."""
    try:
        result = await optimizer.optimize(
            username=request.username,
            content=request.content,
            target_score=request.target_score,
            style=request.style,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Polish Endpoint (Claude) ---

class PolishRequest(BaseModel):
    content: str
    polish_type: Literal["grammar", "twitter", "280char", "translate_en", "translate_ko", "translate_zh"]
    language: Optional[str] = None
    target_post_content: Optional[str] = None  # For tone matching in grammar mode


class PolishChangeResponse(BaseModel):
    type: str
    description: str


class CharacterCountResponse(BaseModel):
    original: int
    polished: int


class PolishResponse(BaseModel):
    original_content: str
    polished_content: str
    polish_type: str
    language_detected: str
    changes: list[PolishChangeResponse]
    character_count: CharacterCountResponse


@router.post("/polish", response_model=PolishResponse)
async def polish_post(request: PolishRequest):
    """Polish text using Claude AI.

    Polish types:
    - grammar: Match target post tone while fixing grammar
    - twitter: Convert to casual, impactful Twitter style
    - 280char: Compress to fit 280 character limit
    """
    try:
        result = await optimizer.polish(
            content=request.content,
            polish_type=request.polish_type,
            language=request.language,
            target_post_content=request.target_post_content,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Generate Personalized Post Endpoint ---

class PersonalizedPostRequest(BaseModel):
    username: str
    target_post_content: str
    target_author: str
    post_type: Literal["reply", "quote"]
    language: str = "en"


class StyleAnalysisResponse(BaseModel):
    tone: str
    emoji_style: str
    topics: list[str]
    writing_pattern: str


class PersonalizedPostResponse(BaseModel):
    username: str
    generated_content: str
    style_analysis: StyleAnalysisResponse
    confidence: float
    reasoning: str
    post_type: str
    target_author: str


@router.post("/generate-personalized", response_model=Optional[PersonalizedPostResponse])
async def generate_personalized_post(request: PersonalizedPostRequest):
    """Generate a personalized post based on user's profile and writing style.

    Analyzes the user's recent 10 posts to understand their:
    - Writing style and tone
    - Interests and topics
    - Emoji and hashtag usage patterns

    Then generates a contextually appropriate reply/quote that matches their style.
    Returns null if profile not found or insufficient data.
    """
    try:
        result = await optimizer.generate_personalized_post(
            username=request.username,
            target_post_content=request.target_post_content,
            target_author=request.target_author,
            post_type=request.post_type,
            language=request.language,
        )

        # Return null instead of 404 if profile not found
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
