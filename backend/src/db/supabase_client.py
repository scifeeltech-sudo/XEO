"""Supabase client for caching and analytics."""

import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


@lru_cache
def get_supabase_client() -> Client:
    """Get singleton Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    return create_client(url, key)


class SupabaseCache:
    """Cache manager using Supabase."""

    def __init__(self):
        self.client = get_supabase_client()

    # ==================== Profile Cache ====================

    async def get_profile_cache(self, username: str) -> Optional[dict[str, Any]]:
        """Get cached profile data if not expired."""
        try:
            result = (
                self.client.table("profile_cache")
                .select("*")
                .eq("x_username", username)
                .gte("expires_at", datetime.now(timezone.utc).isoformat())
                .limit(1)
                .execute()
            )

            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None

    async def set_profile_cache(
        self,
        username: str,
        profile_data: dict[str, Any],
        ttl_hours: int = 1,
    ) -> bool:
        """Cache profile data with TTL."""
        try:
            # Upsert (insert or update)
            self.client.table("profile_cache").upsert(
                {
                    "x_username": username,
                    "profile_data": profile_data,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "expires_at": (
                        datetime.now(timezone.utc).replace(
                            hour=datetime.now(timezone.utc).hour + ttl_hours
                        )
                    ).isoformat(),
                },
                on_conflict="x_username",
            ).execute()
            return True
        except Exception:
            return False

    # ==================== Profile Analysis Cache ====================

    async def get_analysis_cache(self, username: str) -> Optional[dict[str, Any]]:
        """Get cached analysis result if not expired."""
        try:
            result = (
                self.client.table("profile_analyses")
                .select("*")
                .eq("x_username", username)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None

    async def save_analysis(
        self,
        username: str,
        scores: dict[str, float],
        analysis_data: dict[str, Any],
    ) -> bool:
        """Save analysis result."""
        try:
            self.client.table("profile_analyses").insert(
                {
                    "x_username": username,
                    "reach_score": scores.get("reach"),
                    "engagement_score": scores.get("engagement"),
                    "virality_score": scores.get("virality"),
                    "quality_score": scores.get("quality"),
                    "longevity_score": scores.get("longevity"),
                    "analysis_data": analysis_data,
                }
            ).execute()
            return True
        except Exception:
            return False

    # ==================== Analytics ====================

    async def log_analysis(
        self,
        username: Optional[str],
        analysis_type: str,
        session_id: Optional[str] = None,
    ) -> bool:
        """Log analysis event for statistics."""
        try:
            self.client.table("analysis_stats").insert(
                {
                    "x_username": username,
                    "analysis_type": analysis_type,
                    "session_id": session_id,
                }
            ).execute()
            return True
        except Exception:
            return False

    async def get_stats(self, days: int = 7) -> dict[str, Any]:
        """Get usage statistics for the last N days."""
        try:
            # Total analyses
            result = (
                self.client.table("analysis_stats")
                .select("analysis_type", count="exact")
                .execute()
            )

            return {
                "total_analyses": result.count or 0,
                "data": result.data,
            }
        except Exception:
            return {"total_analyses": 0, "data": []}
