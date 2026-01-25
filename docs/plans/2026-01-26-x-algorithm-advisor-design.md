# X Algorithm-Based Content Advisor Design

**Date:** 2026-01-26
**Status:** Implemented

## Overview

Claude AI 기반의 X 알고리즘 최적화 제안 시스템. 콘텐츠 분석 시 X 알고리즘의 19가지 참여 지표를 기반으로 구체적인 개선점을 펜타곤 스코어별로 제안.

## Architecture

```
사용자 콘텐츠
    ↓
ScorePredictor.predict()
    ↓
XAlgorithmAdvisor.analyze_and_suggest()
    ↓
Claude AI (X 알고리즘 지식 + 콘텐츠 분석)
    ↓
구체적 개선 팁 (펜타곤 스코어별)
```

## Key Components

### 1. XAlgorithmAdvisor (`x_algorithm_advisor.py`)

X 알고리즘 지식 베이스를 가진 Claude AI 기반 어드바이저:

- **X_ALGORITHM_KNOWLEDGE**: 19가지 참여 지표 및 최적화 원칙
- **analyze_and_suggest()**: 콘텐츠 분석 및 제안 생성
- **Fallback**: API 미사용 시 규칙 기반 제안

### 2. 19 Engagement Actions

**Positive (점수 상승):**
- favorite, reply, repost, quote, click
- profile_click, photo_expand, video_view
- share, dwell, follow_author

**Negative (점수 하락):**
- not_interested, block_author, mute_author, report

### 3. Pentagon Score Mapping

| Score | X Algorithm Factors |
|-------|---------------------|
| Reach | click, profile_click, share |
| Engagement | favorite, reply, repost, quote |
| Virality | repost, quote, share |
| Quality | dwell, follow_author, NOT(negative actions) |
| Longevity | dwell, bookmark, sustained engagement |

## Response Format

```json
{
  "suggestions": [
    {
      "target_score": "engagement",
      "improvement": "+15%",
      "action": "마지막에 질문 추가",
      "reason": "X 알고리즘의 p_reply 확률 상승",
      "priority": "high"
    }
  ],
  "optimized_content": "최적화된 콘텐츠",
  "score_predictions": {
    "reach": "+5%",
    "engagement": "+15%",
    ...
  }
}
```

## Integration

1. **ScorePredictor**: `_generate_algorithm_tips()` 에서 XAlgorithmAdvisor 호출
2. **ContentOptimizer**: `apply_tips()` 에서 Claude AI로 콘텐츠 재작성
3. **Frontend**: 기존 UI 그대로 사용 (팁 형식 호환)

## Files

- `backend/src/services/x_algorithm_advisor.py` - 핵심 어드바이저
- `backend/src/services/score_predictor.py` - 팁 생성 통합
- `backend/src/services/content_optimizer.py` - 팁 적용 통합
