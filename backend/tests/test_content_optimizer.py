# backend/tests/test_content_optimizer.py
import pytest
from src.services.content_optimizer import ContentOptimizer, _add_emoji, _add_question, _add_hashtag


def test_add_emoji():
    """이모지 추가 테스트"""
    content = "오늘 날씨 좋다"
    result = _add_emoji(content)
    # Should add emoji
    assert any(ord(c) > 0x1F300 for c in result)


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
