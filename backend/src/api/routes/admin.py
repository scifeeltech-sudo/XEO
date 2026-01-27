"""Admin/maintenance API routes."""

from fastapi import APIRouter

from src.db.supabase_client import SupabaseCache

router = APIRouter()
cache = SupabaseCache()


@router.post("/cleanup-cache")
async def cleanup_expired_cache():
    """Clean up expired cache entries from all cache tables.

    This endpoint should be called periodically (e.g., hourly via cron)
    to prevent cache tables from growing indefinitely.

    Returns:
        dict with count of deleted rows per table
    """
    deleted_counts = await cache.cleanup_expired_cache()
    total_deleted = sum(deleted_counts.values())

    return {
        "status": "completed",
        "deleted": deleted_counts,
        "total_deleted": total_deleted,
    }
