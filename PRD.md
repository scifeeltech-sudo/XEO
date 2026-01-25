# PRD: X Score Optimizer

## 1. 개요

### 1.1 제품명
**X Score Optimizer (XSO)**

### 1.2 목적
X(구 Twitter)의 공개된 추천 알고리즘을 기반으로 사용자의 포스팅이 받을 예상 점수를 분석하고, 더 높은 도달률을 위한 콘텐츠 최적화 추천을 제공하는 서비스

### 1.3 목표 사용자
- X 크리에이터 및 인플루언서
- 마케팅 담당자
- 개인 브랜딩에 관심 있는 일반 사용자
- **누구나 가입 없이 바로 무료로 사용 가능**

---

## 2. 기술 스택

| 구분 | 기술 | 용도 |
|------|------|------|
| Backend | Python (uv 환경) | 알고리즘 분석, ML 추론, API 서버 |
| Frontend | Next.js (Node.js) | 웹 애플리케이션 UI |
| Database | Supabase | 분석 결과 캐싱, 통계 저장 |
| Hosting | Vercel | 웹 애플리케이션 배포 |
| X Data | Sela API | X 데이터 접근 (프로필, 포스트, 메트릭스) |

> **인증 불필요**: 회원가입/로그인 없이 X 유저네임만 입력하면 바로 사용 가능

---

## 3. 핵심 기능

### 3.1 프로필 분석 (Profile Analyzer)

#### 기능 설명
사용자의 X 프로필을 분석하여 현재 상태 점수를 산출

#### 분석 항목
```
입력 데이터:
├── 팔로워/팔로잉 비율
├── 최근 포스트 참여율 (좋아요, 리포스트, 답글)
├── 포스트 빈도
├── 미디어 사용 빈도 (이미지, 비디오)
├── 평균 포스트 길이
├── 해시태그 사용 패턴
└── 활동 시간대
```

#### 출력
- 5각형 레이더 차트로 시각화된 프로필 점수
- 각 영역별 상세 분석 리포트

---

### 3.2 포스트 스코어 예측 (Post Score Predictor)

> **포스팅 제안 기능 포함**: 빠른 팁을 선택하여 최적화된 포스팅을 자동 생성

#### 기능 설명
작성 중인 포스트의 예상 점수를 실시간으로 계산

#### 스코어 카테고리 (5각형 차트)

```
                    도달률 (Reach)
                         ▲
                        /|\
                       / | \
                      /  |  \
     참여도          /   |   \        바이럴성
   (Engagement) ◄───────┼───────► (Virality)
                  \     |     /
                   \    |    /
                    \   |   /
                     \  |  /
                      \ | /
           품질        ▼        지속성
        (Quality)           (Longevity)
```

| 스코어 | 설명 | 기반 예측값 |
|--------|------|-------------|
| **도달률 (Reach)** | 얼마나 많은 사람에게 노출될지 | P(click), P(profile_click) |
| **참여도 (Engagement)** | 얼마나 많은 상호작용이 발생할지 | P(favorite), P(reply) |
| **바이럴성 (Virality)** | 얼마나 널리 퍼질지 | P(repost), P(quote), P(share) |
| **품질 (Quality)** | 콘텐츠 품질 점수 | 1 - P(not_interested), 1 - P(report) |
| **지속성 (Longevity)** | 얼마나 오래 노출될지 | P(dwell), P(video_view), P(follow_author) |

#### 포스트 타입별 분석

| 타입 | 설명 | 필수 입력 | 컨텍스트 분석 |
|------|------|----------|---------------|
| 원본 포스트 (Original) | 자신의 타임라인에 새 글 작성 | 포스트 내용 | 사용자 프로필 기반 |
| 답글 (Reply) | 다른 사용자 글에 댓글 | 포스트 내용 + **대상 포스트 URL** | 원본 포스트 + 대화 스레드 |
| 인용 (Quote) | 다른 글을 인용하여 포스트 | 포스트 내용 + **인용할 포스트 URL** | 인용 대상 포스트 |
| 스레드 (Thread) | 연속된 포스트 시리즈 | 각 포스트 내용 (배열) | 스레드 전체 흐름 |

---

### 3.2.1 컨텍스트 기반 분석 (Context-Aware Analysis)

답글/인용 시 정확한 스코어 예측을 위해 **대상 포스트의 컨텍스트**를 분석합니다.

#### 사용자 입력 방식
```
┌─────────────────────────────────────────────────────────────────────────┐
│  포스트 타입 선택                                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                        │
│  │ Original│ │  Reply  │ │  Quote  │ │ Thread  │                        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Reply/Quote 선택 시]                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🔗 대상 포스트 URL을 붙여넣으세요:                               │    │
│  │  https://x.com/elonmusk/status/1234567890___________________     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              [URL 분석하기]                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  📄 원본 포스트 미리보기:                                         │    │
│  │  ┌─────────────────────────────────────────────────────────┐     │    │
│  │  │ @elonmusk                                                │     │    │
│  │  │ "The future of AI is..."                                 │     │    │
│  │  │ ❤️ 125K  🔁 32K  💬 8.2K                                 │     │    │
│  │  └─────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Sela API로 가져오는 컨텍스트 데이터

**Reply (답글) 분석 시:**
```
대상 포스트 컨텍스트:
├── 원본 포스트
│   ├── 작성자 정보 (팔로워 수, 인증 여부)
│   ├── 포스트 내용 (텍스트, 미디어)
│   ├── 현재 engagement (좋아요, 리포스트, 답글 수)
│   ├── 포스트 작성 시간 (신선도)
│   └── 토픽/키워드
│
├── 대화 스레드 (선택적)
│   ├── 상위 답글들 (인기 답글)
│   ├── 대화 깊이 (몇 번째 답글인지)
│   └── 스레드 참여자 수
│
└── 관계 분석
    ├── 내가 원본 작성자를 팔로우하는지
    ├── 원본 작성자가 나를 팔로우하는지
    └── 상호작용 이력 (과거 답글/좋아요)
```

**Quote (인용) 분석 시:**
```
인용 대상 컨텍스트:
├── 인용할 포스트
│   ├── 작성자 정보
│   ├── 포스트 내용
│   ├── 현재 engagement
│   └── 바이럴 상태 (트렌딩 여부)
│
└── 인용 분석
    ├── 기존 인용 수
    ├── 인용의 감정 분석 (긍정/부정/중립)
    └── 인용 트렌드 (증가/감소)
```

#### 컨텍스트가 스코어에 미치는 영향

| 컨텍스트 요소 | 영향 | 설명 |
|--------------|------|------|
| 원본 포스트 인기도 | 도달률 ↑ | 인기 포스트에 답글 달면 노출 증가 |
| 원본 작성자 팔로워 수 | 도달률 ↑ | 대형 계정 포스트는 더 많은 노출 |
| 포스트 신선도 | 도달률 ↑ | 최신 포스트일수록 답글 노출 유리 |
| 대화 깊이 | 도달률 ↓ | 깊은 스레드일수록 노출 감소 |
| 기존 답글 수 | 경쟁도 ↑ | 답글 많으면 내 답글 묻힐 가능성 |
| 토픽 관련성 | 품질 ↑ | 원본과 관련된 답글이 더 높은 품질 점수 |
| 상호 팔로우 여부 | 참여도 ↑ | 상호 팔로우 시 작성자 응답 가능성 증가 |

#### 컨텍스트 기반 추천 예시

```
[상황] @techcrunch의 AI 관련 포스트에 답글 작성

원본 포스트 분석:
- 팔로워: 12M (대형 계정)
- 작성 시간: 15분 전 (신선함)
- 현재 답글: 127개 (경쟁 중간)
- 토픽: AI, Technology

📊 컨텍스트 기반 스코어 조정:
- 도달률: +25% (대형 계정 효과)
- 도달률: +15% (신선도 보너스)
- 도달률: -10% (답글 경쟁)

💡 최적화 추천:
1. "AI 관련 전문 용어를 포함하면 토픽 관련성 +12%"
2. "질문 형태로 작성하면 원본 작성자 응답 가능성 +20%"
3. "15분 내에 작성하면 신선도 보너스 유지"
```

---

### 3.2.2 포스팅 제안 기능 (Post Suggestion)

실시간 분석에서 제공되는 빠른 팁을 선택하여 최적화된 포스팅을 자동 생성하는 기능입니다.

#### UI 레이아웃

```
┌─────────────────────────────┐  ┌─────────────────────────────────┐
│  📝 포스팅 작성              │  │  📊 분석 결과                    │
│  ┌─────────────────────────┐│  │                                 │
│  │ 오늘 날씨 좋다           ││  │  스코어: 도달률 45, 참여도 38... │
│  │                         ││  │                                 │
│  │                         ││  │  💡 빠른 팁 (최대 3개 선택):     │
│  │                         ││  │  ☐ 이모지 추가 (+8% 참여도)     │
│  └─────────────────────────┘│  │  ☐ 질문 형태로 변환 (+12% 참여) │
│                             │  │  ☐ 해시태그 추가 (+5% 도달률)   │
│                             │  │  ☐ CTA 추가 (+10% 참여도)       │
│                             │  │                                 │
│                             │  │         [✨ 반영하기]            │
└─────────────────────────────┘  └─────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────┐
│  ✨ 포스팅 제안                                                    │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │ 오늘 날씨 너무 좋네요 ☀️ 여러분은 이런 날 뭐하세요? #일상      ││
│  │                                                               ││
│  │ (직접 수정 가능)                                               ││
│  └───────────────────────────────────────────────────────────────┘│
│                                              [📋 복사하기]         │
└───────────────────────────────────────────────────────────────────┘
```

#### 기능 상세

| 항목 | 설명 |
|------|------|
| **빠른 팁 선택** | 체크박스로 원하는 팁 선택 (최대 3개) |
| **반영하기 버튼** | 선택한 팁들을 원본 포스팅에 적용하여 제안 생성 |
| **포스팅 제안 칸** | AI가 생성한 최적화된 포스팅 표시, 직접 수정 가능 |
| **복사하기** | 제안된 포스팅을 클립보드에 복사 |

#### 동작 플로우

```
1. 사용자가 포스팅 작성 칸에 원본 입력
2. 실시간으로 분석 결과 + 빠른 팁 표시
3. 사용자가 원하는 팁 선택 (최대 3개)
4. [반영하기] 버튼 클릭
5. AI가 원본 + 선택한 팁을 조합하여 최적화된 포스팅 생성
6. 포스팅 제안 칸에 결과 표시
7. 사용자가 필요시 직접 수정
8. [복사하기]로 X에 포스팅
```

#### 팁 반영 우선순위

여러 팁이 선택된 경우, 다음 순서로 적용:
1. 콘텐츠 구조 변경 (질문 형태, CTA 추가 등)
2. 요소 추가 (이모지, 해시태그 등)
3. 문체/톤 조정

---

### 3.3 최적화 추천 (Optimization Recommender)

#### 기능 설명
선택한 스코어를 높이기 위한 콘텐츠 수정 제안

#### 추천 유형

**1. 콘텐츠 수정 제안**
```
원본: "오늘 날씨 좋다"

[도달률 최적화 추천]
→ "오늘 날씨 좋다 ☀️ 여러분은 뭐하고 계세요?"
   - 이모지 추가 (+5% 예상)
   - 질문 형태로 변환 (+12% 예상)
   - 해시태그 추가 권장: #일상 #날씨

[참여도 최적화 추천]
→ "오늘 같은 날씨에 뭐하면 좋을까요? 🤔 추천 부탁드려요!"
   - CTA(Call to Action) 추가
   - 의견 요청 형태
```

**2. 포스팅 전략 제안**
- 최적 포스팅 시간대
- 추천 미디어 타입 (이미지/비디오/GIF)
- 스레드 vs 단일 포스트 추천
- 답글 vs 원본 포스트 추천

**3. AI 기반 콘텐츠 리라이팅**
- 선택한 스코어에 최적화된 문구로 자동 변환
- 여러 버전 제안 (보수적/적극적/실험적)

---

## 4. 사용자 플로우

```
┌─────────────────────────────────────────────────────────────────────┐
│                         사용자 플로우                                │
│                    (가입 불필요 - 즉시 사용 가능)                     │
└─────────────────────────────────────────────────────────────────────┘

[1. 시작]
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│                        랜딩 페이지                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │     🔍 X 유저네임을 입력하세요: [@____________] [분석하기]    │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
[2. 프로필 분석]        ┌─────────────────────┐
                        │  Sela API로         │
                        │  프로필 데이터 조회  │
                        └─────────────────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │  프로필 스코어      │
                        │  (5각형 차트)       │
                        │  + 개선 권장사항    │
                        └─────────────────────┘
                                │
                                ▼
[3. 포스트 작성]        ┌─────────────────────┐
                        │  포스트 에디터      │
                        │  + 실시간 스코어    │
                        │  + 타입 선택        │
                        └─────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
       ┌───────────┐     ┌───────────┐     ┌───────────┐
       │  원본     │     │  답글     │     │  인용     │
       │  포스트   │     │           │     │           │
       └───────────┘     └───────────┘     └───────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
[4. 스코어 분석]        ┌─────────────────────┐
                        │  예상 스코어        │
                        │  (5각형 차트)       │
                        └─────────────────────┘
                                │
                                ▼
[5. 최적화]             ┌─────────────────────┐
                        │  목표 스코어 선택   │
                        │  (도달률/참여도/등) │
                        └─────────────────────┘
                                │
                                ▼
                        ┌─────────────────────┐
                        │  AI 추천 적용       │
                        │  + 수정된 콘텐츠    │
                        └─────────────────────┘
                                │
                                ▼
[6. 완료]               ┌─────────────────────┐
                        │  클립보드 복사      │
                        │  → X에서 직접 포스트│
                        └─────────────────────┘
```

---

## 5. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Vercel)                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Next.js Application                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │ Dashboard   │  │ Post Editor │  │ Score Chart │  │ Recommender │   │  │
│  │  │ Page        │  │ Component   │  │ (Radar)     │  │ Panel       │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ REST API / WebSocket
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (Python + uv)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         FastAPI Application                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│  │  │ /api/profile    │  │ /api/analyze    │  │ /api/optimize   │        │  │
│  │  │ - GET profile   │  │ - POST score    │  │ - POST suggest  │        │  │
│  │  │ - GET score     │  │ - WS realtime   │  │ - POST rewrite  │        │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                        │                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Core Services                                 │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│  │  │ ProfileAnalyzer │  │ ScorePredictor  │  │ ContentOptimizer│        │  │
│  │  │ Service         │  │ Service         │  │ Service         │        │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                        │                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      X Algorithm Engine                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│  │  │ Phoenix Model   │  │ Weighted Scorer │  │ Feature         │        │  │
│  │  │ (Simplified)    │  │                 │  │ Extractor       │        │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE (Supabase)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ users           │  │ analyses        │  │ posts_history   │              │
│  │ - id            │  │ - id            │  │ - id            │              │
│  │ - x_user_id     │  │ - user_id       │  │ - user_id       │              │
│  │ - access_token  │  │ - profile_score │  │ - content       │              │
│  │ - profile_data  │  │ - created_at    │  │ - predicted     │              │
│  │ - created_at    │  │                 │  │ - actual_score  │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                 │
│  ┌─────────────────┐  ┌─────────────────┐                                   │
│  │ Sela API        │  │ OpenAI API      │                                   │
│  │ - User data     │  │ - Content       │                                   │
│  │ - Post metrics  │  │   rewriting     │                                   │
│  │ - Profile info  │  │                 │                                   │
│  └─────────────────┘  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 데이터 모델

### 6.1 Supabase 스키마

> **참고**: 인증 없이 운영되므로 세션 기반으로 데이터 관리. 프로필 분석 결과는 캐싱하여 API 비용 절감.

```sql
-- 프로필 캐시 (Sela API 호출 결과 캐싱)
CREATE TABLE profile_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    x_username TEXT UNIQUE NOT NULL,    -- X 유저네임 (조회 키)
    x_user_id TEXT,
    x_display_name TEXT,
    x_profile_image_url TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    profile_data JSONB,                 -- Sela API 원본 데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour')
);

-- 프로필 분석 결과 캐시
CREATE TABLE profile_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    x_username TEXT NOT NULL,
    reach_score DECIMAL(5,2),
    engagement_score DECIMAL(5,2),
    virality_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    longevity_score DECIMAL(5,2),
    analysis_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour')
);

-- 포스트 컨텍스트 캐시 (Reply/Quote 대상 포스트)
CREATE TABLE post_context_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT UNIQUE NOT NULL,       -- X 포스트 ID
    post_url TEXT NOT NULL,
    author_username TEXT NOT NULL,
    author_data JSONB,                  -- 작성자 정보
    content_data JSONB,                 -- 포스트 내용
    metrics_data JSONB,                 -- 참여 지표
    analysis_data JSONB,                -- 분석 결과
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '15 minutes')
);

-- 분석 통계 (서비스 사용량 추적)
CREATE TABLE analysis_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    x_username TEXT,                    -- 익명 처리 가능
    analysis_type TEXT NOT NULL,        -- 'profile', 'post', 'post_context', 'optimize'
    session_id TEXT,                    -- 브라우저 세션 ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_profile_cache_username ON profile_cache(x_username);
CREATE INDEX idx_profile_cache_expires ON profile_cache(expires_at);
CREATE INDEX idx_profile_analyses_username ON profile_analyses(x_username);
CREATE INDEX idx_post_context_cache_post_id ON post_context_cache(post_id);
CREATE INDEX idx_post_context_cache_expires ON post_context_cache(expires_at);
CREATE INDEX idx_analysis_stats_created ON analysis_stats(created_at DESC);
```

---

## 7. API 명세

### 7.1 Backend API (Python FastAPI)

#### 프로필 분석
```
GET /api/v1/profile/{username}/analyze

Response:
{
    "username": "elonmusk",
    "scores": {
        "reach": 72.5,
        "engagement": 65.0,
        "virality": 45.2,
        "quality": 88.0,
        "longevity": 55.8
    },
    "insights": [
        {
            "category": "engagement",
            "message": "답글 비율이 낮습니다. 다른 사용자와의 상호작용을 늘려보세요.",
            "priority": "high"
        }
    ],
    "recommendations": [
        {
            "action": "increase_reply_rate",
            "expected_impact": "+15% engagement",
            "description": "하루 3-5개의 관련 포스트에 답글을 달아보세요."
        }
    ]
}
```

#### 포스트 스코어 예측
```
POST /api/v1/post/analyze

Request:
{
    "username": "myusername",           // 작성자의 X 유저네임
    "content": "포스트 내용",
    "post_type": "original",            // "original" | "reply" | "quote" | "thread"
    "target_post_url": null,            // [reply/quote 필수] 대상 포스트 URL
    "thread_contents": null,            // [thread] 스레드 포스트 배열
    "media_type": null                  // "image" | "video" | "gif" | null
}

// Reply 예시
{
    "username": "myusername",
    "content": "This is a great point!",
    "post_type": "reply",
    "target_post_url": "https://x.com/elonmusk/status/1234567890",
    "media_type": null
}

// Quote 예시
{
    "username": "myusername",
    "content": "Interesting perspective on AI 🤔",
    "post_type": "quote",
    "target_post_url": "https://x.com/techcrunch/status/9876543210",
    "media_type": "image"
}

Response:
{
    "analysis_id": "uuid",
    "scores": {
        "reach": 65.0,
        "engagement": 72.5,
        "virality": 38.0,
        "quality": 82.0,
        "longevity": 45.0
    },
    "breakdown": {
        "p_favorite": 0.15,
        "p_reply": 0.08,
        "p_repost": 0.05,
        "p_quote": 0.02,
        "p_click": 0.25,
        "p_profile_click": 0.12,
        "p_share": 0.03,
        "p_dwell": 0.45,
        "p_follow_author": 0.01,
        "p_not_interested": 0.05,
        "p_block_author": 0.001,
        "p_mute_author": 0.002,
        "p_report": 0.0001
    },
    "quick_tips": [
        {
            "tip_id": "add_emoji",
            "description": "이모지를 추가하면 engagement +8% 예상",
            "impact": "+8%",
            "target_score": "engagement",
            "selectable": true
        },
        {
            "tip_id": "add_question",
            "description": "질문 형태로 바꾸면 reply율 +15% 예상",
            "impact": "+15%",
            "target_score": "engagement",
            "selectable": true
        }
    ],

    // [reply/quote인 경우 추가 필드]
    "context": {
        "target_post": {
            "id": "1234567890",
            "author": {
                "username": "elonmusk",
                "display_name": "Elon Musk",
                "followers_count": 170000000,
                "verified": true
            },
            "content": "The future of AI is...",
            "metrics": {
                "likes": 125000,
                "reposts": 32000,
                "replies": 8200,
                "quotes": 5100
            },
            "created_at": "2025-01-25T10:30:00Z",
            "age_minutes": 15
        },
        "context_adjustments": {
            "large_account_bonus": "+25%",
            "freshness_bonus": "+15%",
            "reply_competition": "-10%",
            "topic_relevance": "+8%"
        },
        "recommendations": [
            "원본 포스트가 15분 전에 작성되어 신선도 보너스가 적용됩니다",
            "대형 계정(170M 팔로워) 포스트로 높은 노출이 예상됩니다",
            "현재 답글 8.2K개로 경쟁이 있으니 차별화된 관점을 제시하세요"
        ]
    }
}
```

#### 대상 포스트 컨텍스트 조회 (Reply/Quote 전용)
```
GET /api/v1/post/context?url={post_url}

Request:
GET /api/v1/post/context?url=https://x.com/elonmusk/status/1234567890

Response:
{
    "post": {
        "id": "1234567890",
        "url": "https://x.com/elonmusk/status/1234567890",
        "author": {
            "username": "elonmusk",
            "display_name": "Elon Musk",
            "profile_image_url": "https://...",
            "followers_count": 170000000,
            "following_count": 500,
            "verified": true,
            "description": "..."
        },
        "content": {
            "text": "The future of AI is incredibly exciting...",
            "media": [
                {"type": "image", "url": "https://..."}
            ],
            "hashtags": ["AI", "Future"],
            "mentions": ["@OpenAI"]
        },
        "metrics": {
            "likes": 125000,
            "reposts": 32000,
            "replies": 8200,
            "quotes": 5100,
            "views": 15000000
        },
        "created_at": "2025-01-25T10:30:00Z",
        "language": "en"
    },
    "analysis": {
        "age_minutes": 15,
        "freshness": "very_fresh",       // "very_fresh" | "fresh" | "moderate" | "old"
        "virality_status": "trending",   // "trending" | "growing" | "stable" | "declining"
        "reply_saturation": "medium",    // "low" | "medium" | "high" | "very_high"
        "topics": ["AI", "Technology", "Future"],
        "sentiment": "positive"          // "positive" | "neutral" | "negative" | "controversial"
    },
    "opportunity_score": {
        "overall": 78,
        "factors": {
            "account_reach": 95,         // 대형 계정이라 높음
            "timing": 90,                // 신선해서 높음
            "competition": 60,           // 답글 많아서 중간
            "topic_engagement": 85       // AI 토픽 참여도 높음
        }
    },
    "tips": [
        "🕐 포스트가 15분 전에 작성되어 답글 달기 최적의 타이밍입니다",
        "🔥 현재 트렌딩 중인 포스트입니다 - 노출 기회가 높습니다",
        "💬 이미 8.2K 답글이 있어 차별화된 관점이 필요합니다",
        "🎯 AI 관련 전문 의견을 제시하면 품질 점수가 높아집니다"
    ]
}
```

#### 빠른 팁 반영 (포스팅 제안 생성)
```
POST /api/v1/post/apply-tips

Request:
{
    "username": "myusername",
    "original_content": "오늘 날씨 좋다",
    "selected_tips": [
        "add_emoji",
        "add_question",
        "add_hashtag"
    ]
}

Response:
{
    "original_content": "오늘 날씨 좋다",
    "suggested_content": "오늘 날씨 너무 좋네요 ☀️ 여러분은 이런 날 뭐하세요? #일상",
    "applied_tips": [
        {
            "tip_id": "add_emoji",
            "description": "이모지 추가",
            "impact": "+8% 참여도"
        },
        {
            "tip_id": "add_question",
            "description": "질문 형태로 변환",
            "impact": "+12% 참여도"
        },
        {
            "tip_id": "add_hashtag",
            "description": "해시태그 추가",
            "impact": "+5% 도달률"
        }
    ],
    "predicted_improvement": {
        "engagement": "+20%",
        "reach": "+5%"
    }
}
```

#### 콘텐츠 최적화
```
POST /api/v1/post/optimize

Request:
{
    "username": "elonmusk",
    "content": "원본 포스트 내용",
    "target_score": "engagement",   // "reach" | "engagement" | "virality" | "quality" | "longevity"
    "style": "balanced"             // "conservative" | "balanced" | "aggressive"
}

Response:
{
    "original_content": "오늘 날씨 좋다",
    "optimized_versions": [
        {
            "content": "오늘 날씨 너무 좋네요 ☀️ 여러분은 이런 날 뭐하세요?",
            "style": "conservative",
            "predicted_scores": {
                "reach": 68.0,
                "engagement": 85.0,
                "virality": 42.0,
                "quality": 80.0,
                "longevity": 48.0
            },
            "changes": [
                {"type": "added_emoji", "impact": "+5% engagement"},
                {"type": "added_question", "impact": "+12% engagement"}
            ]
        },
        {
            "content": "☀️ 완벽한 날씨! 이런 날 최고의 활동은?\n\n1️⃣ 공원 산책\n2️⃣ 카페 테라스\n3️⃣ 재택 낮잠\n\n투표해주세요! 👇",
            "style": "aggressive",
            "predicted_scores": {
                "reach": 75.0,
                "engagement": 92.0,
                "virality": 55.0,
                "quality": 78.0,
                "longevity": 52.0
            },
            "changes": [
                {"type": "added_poll_format", "impact": "+25% engagement"},
                {"type": "added_cta", "impact": "+10% engagement"}
            ]
        }
    ]
}
```

#### 실시간 스코어 (WebSocket)
```
WS /api/v1/post/realtime

Client -> Server:
{
    "type": "analyze",
    "content": "타이핑 중인 내용...",
    "post_type": "original"
}

Server -> Client:
{
    "type": "score_update",
    "scores": {
        "reach": 45.0,
        "engagement": 52.0,
        "virality": 28.0,
        "quality": 75.0,
        "longevity": 38.0
    },
    "typing_suggestions": [
        "문장 끝에 질문을 추가해보세요"
    ]
}
```

---

## 8. 프로젝트 구조

### 8.1 Backend (Python)

```
backend/
├── pyproject.toml              # uv 프로젝트 설정
├── uv.lock                     # 의존성 락 파일
├── .env.example                # 환경변수 예시
├── .env                        # 환경변수 (gitignore)
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 엔트리포인트
│   ├── config.py               # 설정 관리
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── profile.py      # 프로필 분석 API
│   │   │   ├── post.py         # 포스트 분석 API
│   │   │   └── optimize.py     # 최적화 API
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── realtime.py     # 실시간 스코어 WS
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── profile_analyzer.py
│   │   ├── score_predictor.py
│   │   ├── content_optimizer.py
│   │   └── sela_api_client.py  # Sela API 클라이언트
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── feature_extractor.py    # 피처 추출
│   │   ├── weighted_scorer.py      # 가중치 스코어러
│   │   ├── phoenix_simplified.py   # 단순화된 Phoenix 모델
│   │   └── score_aggregator.py     # 5각형 스코어 집계
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── analysis.py
│   │   └── post.py
│   │
│   └── db/
│       ├── __init__.py
│       └── supabase_client.py
│
└── tests/
    ├── __init__.py
    ├── test_profile_analyzer.py
    ├── test_score_predictor.py
    └── test_content_optimizer.py
```

### 8.2 Frontend (Next.js)

```
frontend/
├── package.json
├── next.config.js
├── tailwind.config.js
├── .env.local.example
├── .env.local                  # 환경변수 (gitignore)
│
├── app/
│   ├── layout.tsx
│   ├── page.tsx                # 랜딩 페이지 (유저네임 입력)
│   ├── globals.css
│   │
│   ├── [username]/             # 동적 라우트: /elonmusk
│   │   ├── page.tsx            # 프로필 분석 결과
│   │   ├── loading.tsx
│   │   └── compose/
│   │       └── page.tsx        # 포스트 작성 & 분석
│   │
│   └── api/
│       └── [...proxy]/
│           └── route.ts        # Backend API 프록시
│
├── components/
│   ├── ui/                     # 공통 UI 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Modal.tsx
│   │
│   ├── charts/
│   │   ├── RadarChart.tsx      # 5각형 레이더 차트
│   │   └── ScoreGauge.tsx
│   │
│   ├── editor/
│   │   ├── PostEditor.tsx      # 포스트 작성 에디터
│   │   ├── PostTypeSelector.tsx
│   │   ├── RealTimeScore.tsx   # 실시간 스코어 표시
│   │   ├── QuickTipSelector.tsx # 빠른 팁 체크박스 (최대 3개)
│   │   └── PostSuggestion.tsx  # 포스팅 제안 칸
│   │
│   ├── profile/
│   │   ├── ProfileCard.tsx
│   │   └── ProfileInsights.tsx
│   │
│   └── optimizer/
│       ├── ScoreSelector.tsx   # 목표 스코어 선택
│       ├── SuggestionCard.tsx
│       └── OptimizedVersions.tsx
│
├── hooks/
│   ├── useProfile.ts           # 프로필 분석 데이터
│   ├── usePostAnalysis.ts      # 포스트 스코어 예측
│   ├── useOptimize.ts          # 콘텐츠 최적화
│   ├── useApplyTips.ts         # 빠른 팁 반영 (포스팅 제안)
│   └── useWebSocket.ts         # 실시간 스코어
│
├── lib/
│   ├── api.ts                  # API 클라이언트
│   ├── supabase.ts             # Supabase 클라이언트
│   └── utils.ts
│
└── types/
    ├── user.ts
    ├── analysis.ts
    └── api.ts
```

---

## 9. 개발 단계

### Phase 1: 기반 구축 (MVP)
| 태스크 | 설명 |
|--------|------|
| 프로젝트 설정 | Python(uv) + Next.js 프로젝트 초기화 |
| Supabase 설정 | 데이터베이스 스키마 생성 (캐싱 테이블) |
| Sela API 연동 | X 데이터 조회 기능 구현 |
| 기본 UI | 랜딩 페이지, 유저네임 입력 폼 |

### Phase 2: 핵심 기능
| 태스크 | 설명 |
|--------|------|
| 프로필 분석 | Sela API로 프로필 데이터 수집 및 분석 |
| 스코어 예측 엔진 | X 알고리즘 기반 단순화된 스코어 계산 |
| 레이더 차트 | 5각형 스코어 시각화 컴포넌트 |
| 포스트 에디터 | 포스트 작성 및 실시간 분석 UI |

### Phase 3: 최적화 기능
| 태스크 | 설명 |
|--------|------|
| 콘텐츠 최적화 | AI 기반 콘텐츠 수정 제안 |
| 실시간 스코어 | WebSocket 기반 타이핑 중 스코어 업데이트 |
| 히스토리 | 분석 기록 저장 및 조회 |

### Phase 4: 고도화
| 태스크 | 설명 |
|--------|------|
| 실제 성과 추적 | 포스팅 후 실제 metrics 수집 및 비교 |
| 모델 개선 | 실제 데이터 기반 예측 정확도 개선 |
| 추가 기능 | 스레드 분석, 최적 시간대 추천 등 |

---

## 10. 환경 설정

### 10.1 Backend (.env)
```env
# App
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key

# Sela API (X 데이터 접근)
SELA_API_KEY=your-sela-api-key
SELA_API_BASE_URL=https://api.sela.so

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI (for content optimization)
OPENAI_API_KEY=your-openai-api-key

# Server
HOST=0.0.0.0
PORT=8000
```

### 10.2 Frontend (.env.local)
```env
# API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## 11. 성공 지표

| 지표 | 목표 |
|------|------|
| 예측 정확도 | 실제 engagement와 예측의 상관계수 > 0.7 |
| 일일 분석 수 | DAU (일일 분석 요청 수) |
| 재방문율 | 동일 IP/세션의 재방문 비율 > 30% |
| 응답 시간 | 프로필 분석 < 2s, 스코어 예측 < 500ms, 최적화 < 2s |
| 공유율 | 결과 공유 (SNS, 링크 복사) 비율 |

---

## 12. 제약 사항 및 고려 사항

### 12.1 Sela API 제한
- Sela API Rate Limit 준수 필요
- Sela API에서 제공하는 데이터 범위 내에서 분석
- API 키 보안 관리 필수

### 12.2 알고리즘 한계
- 공개된 알고리즘은 단순화된 버전
- 실제 X 알고리즘과 100% 일치하지 않음
- 지속적인 모델 업데이트 필요

### 12.3 법적 고려
- X 이용약관 준수
- 자동화 포스팅 제한 준수 (포스팅은 사용자가 직접 수행)

### 12.4 무료 서비스 고려사항
- Rate Limiting 적용 (IP 기반, 분당 요청 수 제한)
- 프로필 분석 결과 캐싱 (1시간)
- 악용 방지를 위한 기본적인 모니터링

---

## 13. 부록: 스코어 가중치 (초기값)

X 알고리즘의 Weighted Scorer 기반 초기 가중치:

```python
SCORE_WEIGHTS = {
    # 도달률 (Reach)
    "reach": {
        "p_click": 0.4,
        "p_profile_click": 0.3,
        "p_dwell": 0.3,
    },

    # 참여도 (Engagement)
    "engagement": {
        "p_favorite": 0.35,
        "p_reply": 0.35,
        "p_quote": 0.15,
        "p_not_interested": -0.15,
    },

    # 바이럴성 (Virality)
    "virality": {
        "p_repost": 0.4,
        "p_quote": 0.3,
        "p_share": 0.3,
    },

    # 품질 (Quality)
    "quality": {
        "p_favorite": 0.25,
        "p_dwell": 0.25,
        "p_not_interested": -0.2,
        "p_block_author": -0.15,
        "p_mute_author": -0.1,
        "p_report": -0.3,
    },

    # 지속성 (Longevity)
    "longevity": {
        "p_dwell": 0.3,
        "p_video_view": 0.25,
        "p_follow_author": 0.25,
        "p_favorite": 0.2,
    },
}
```

---

*문서 버전: 1.2*
*최종 수정: 2025-01-25*
*변경사항: 포스팅 제안 기능 추가 (빠른 팁 선택 → 최적화된 포스팅 자동 생성)*
