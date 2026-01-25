from fastapi import APIRouter
from .routes import profile, post

api_router = APIRouter()
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(post.router, prefix="/post", tags=["post"])
