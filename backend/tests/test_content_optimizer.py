# backend/tests/test_content_optimizer.py
import pytest
from src.services.content_optimizer import ContentOptimizer, _add_emoji, _add_question, _add_hashtag


def test_add_emoji():
    """이모지 추가 테스트"""
    content = "오늘 날씨 좋다"
    result = _add_emoji(content)
    # Should add emoji (various unicode ranges: emoticons, symbols, etc.)
    assert result != content  # Content should be modified
    # Check for common emoji unicode ranges
    import re
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F"  # emoticons
        r"\U0001F300-\U0001F5FF"   # symbols & pictographs
        r"\U0001F680-\U0001F6FF"   # transport & map symbols
        r"\U00002600-\U000027BF"   # misc symbols (includes ☀️, ✅, etc.)
        r"\U0001F900-\U0001F9FF"   # supplemental symbols
        r"]"
    )
    assert emoji_pattern.search(result) is not None


def test_add_question():
    """질문 추가 테스트"""
    content = "오늘 날씨 좋다"
    result = _add_question(content)
    assert "?" in result or "요?" in result


def test_add_hashtag():
    """해시태그 추가 테스트"""
    content = "오늘 날씨 좋다"
    result = _add_hashtag(content)
    assert "#" in result


@pytest.mark.asyncio
async def test_apply_tips():
    """팁 적용 테스트"""
    optimizer = ContentOptimizer()

    result = await optimizer.apply_tips(
        username="testuser",
        original_content="오늘 날씨 좋다",
        selected_tips=["add_emoji", "add_question"],
    )

    assert result["original_content"] == "오늘 날씨 좋다"
    assert result["suggested_content"] != "오늘 날씨 좋다"
    assert len(result["applied_tips"]) == 2


@pytest.mark.asyncio
async def test_optimize():
    """최적화 테스트"""
    optimizer = ContentOptimizer()

    result = await optimizer.optimize(
        username="testuser",
        content="오늘 날씨 좋다",
        target_score="engagement",
        style="balanced",
    )

    assert result["original_content"] == "오늘 날씨 좋다"
    assert len(result["optimized_versions"]) >= 1
