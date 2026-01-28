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

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| Backend | FastAPI + Python | 0.128.0 / 3.11+ | REST API 서버, 알고리즘 분석 |
| Frontend | Next.js + React | 16.1.4 / 19.2.3 | 웹 애플리케이션 UI (App Router) |
| Styling | Tailwind CSS | v4 | 반응형 UI 스타일링 |
| Charts | Recharts | 3.7.0 | 5각형 레이더 차트 시각화 |
| Database | Supabase | - | 분석 결과 캐싱, 통계 저장 |
| Hosting | Vercel | - | 웹 애플리케이션 배포 |
| X Data | Sela API | - | X 데이터 접근 (프로필, 포스트, 메트릭스) |
| AI Engine | Claude API (Anthropic) | - | 글 다듬기, 콘텐츠 최적화, X 알고리즘 기반 팁 생성, 개인화 포스트 생성 |

### 2.1 다국어 지원

| 언어 | 코드 | 지원 범위 |
|------|------|----------|
| 한국어 | ko | 전체 기능 |
| 영어 | en | 전체 기능 |
| 일본어 | ja | 전체 기능 |
| 중국어 | zh | 전체 기능 |

> **인증 불필요**: 회원가입/로그인 없이 X 유저네임만 입력하면 바로 사용 가능

---

## 3. 핵심 기능

### 3.1 프로필 분석 (Profile Analyzer)

#### 기능 설명
사용자의 X 프로필을 분석하여 현재 상태 점수를 산출

#### 분석 항목
```
입력 데이터 (최근 10개 포스트 기반):
├── 팔로워/팔로잉 비율
├── 최근 포스트 참여율 (좋아요, 리포스트, 답글)
├── 포스트 빈도
├── 미디어 사용 빈도 (이미지, 비디오)
├── 평균 포스트 길이
├── 해시태그 사용 패턴
└── 활동 시간대
```

#### 스코어 계산 기준

| 스코어 | 계산 기준 | 베이스라인 |
|--------|----------|-----------|
| **Reach** | 평균 조회수 기반 | 10,000 views = 100점 |
| **Engagement** | 참여율 (좋아요+답글+리포스트/조회수) | 0.01~0.05 = 정상 범위 |
| **Virality** | 리포스트 비율 및 볼륨 | - |
| **Quality** | 일관성 및 오리지널 콘텐츠 비율 | - |
| **Longevity** | 미디어 사용률, 지속적 참여 | 미디어 비율 높을수록 + |

#### 스코어 최소 임계값 ✅ v1.10

스코어가 0으로 붕괴되는 것을 방지하기 위한 최소값 설정:

**포스트 스코어 (weighted_scorer.py):**
| 항목 | 최소값 | 설명 |
|------|--------|------|
| base_engagement | 3% | 기본 참여율 최소값 |
| p_favorite, p_reply | 0.01 | Engagement 팩터 최소값 |
| p_repost, p_quote, p_share | 0.005 | Virality 팩터 최소값 |

**프로필 스코어 (profile_analyzer.py):** ✅ v1.11
| 항목 | 최소값 | 설명 |
|------|--------|------|
| effective_engagement | 3% | 참여율 계산 최소값 |
| Reach 스코어 | 10점 | 도달률 최소 점수 |
| Engagement 스코어 | 5점 | 참여도 최소 점수 |
| Virality 스코어 | 5점 | 바이럴성 최소 점수 |

#### 프로필 요약 (Summary) ✅ v1.12

트윗 내용 분석을 통해 2줄 요약 자동 생성:

**첫 번째 줄**: 브랜드/회사 정보 또는 계정 특성
- 트윗에서 자주 언급되는 브랜드/회사명 추출 (@멘션, #해시태그, 대문자 단어)
- 브랜드 정규화 매핑 (예: sela → Sela Network, grok → Grok)
- 브랜드 미감지 시 Reach 점수 기반 설명

**두 번째 줄**: 강점 분석
- 5가지 점수 중 상위 2개 강점 표시
- 예: "Key strengths: viral potential and consistent quality content."

```python
BRAND_ALIASES = {
    "sela": "Sela Network",
    "openai": "OpenAI",
    "tesla": "Tesla",
    "grok": "Grok",
    # ... 주요 브랜드 매핑
}
```

#### 출력
- 5각형 레이더 차트로 시각화된 프로필 점수
- **2줄 프로필 요약** (브랜드/강점 기반)
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
│  [대상 포스트를 가져올 수 없는 경우]                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🌐 대상 포스트 언어 선택:                                        │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │    │
│  │  │ English │ │ 한국어   │ │ 日本語  │ │  中文   │               │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Sela API로 가져오는 컨텍스트 데이터

> **⚠️ 제한사항**: Sela API의 `TWITTER_POST` 스크래핑 타입이 현재 작동하지 않습니다 (빈 결과 반환).
> 대안으로 `TWITTER_PROFILE`을 사용하여 작성자의 최근 포스트 50개 내에서 대상 포스트를 검색합니다.
> 최근 포스트에 없는 경우, 사용자가 **대상 포스트 언어를 직접 선택**할 수 있는 UI를 제공합니다.

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

| 컨텍스트 요소 | 영향 | 임계값 | 설명 |
|--------------|------|--------|------|
| 원본 포스트 인기도 | 도달률 +25% | >100,000 views | 대형 계정 포스트에 답글 시 노출 증가 |
| 포스트 신선도 | 도달률 +15% | <60분 | 최신 포스트일수록 답글 노출 유리 |
| 기존 답글 수 | 경쟁도 -10% | >1,000 replies | 답글 많으면 내 답글 묻힐 가능성 |
| 대화 깊이 | 도달률 ↓ | - | 깊은 스레드일수록 노출 감소 |
| 토픽 관련성 | 품질 ↑ | - | 원본과 관련된 답글이 더 높은 품질 점수 |
| 상호 팔로우 여부 | 참여도 ↑ | - | 상호 팔로우 시 작성자 응답 가능성 증가 |

#### Freshness 분류 기준

| 상태 | 시간 범위 | 노출 영향 |
|------|----------|----------|
| very_fresh | 0~15분 | 최고 (신선도 보너스 최대) |
| fresh | 15~60분 | 높음 |
| moderate | 1~6시간 | 보통 |
| old | 6시간+ | 낮음 |

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
│       [🔍 분석하기]          │  │  ☐ CTA 추가 (+10% 참여도)       │
│                             │  │                                 │
│                             │  │         [✨ 반영하기]            │
└─────────────────────────────┘  └─────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────┐
│  ✨ 포스팅 제안                                                    │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │ 오늘 날씨 너무 좋네요 ☀️ 여러분은 이런 날 뭐하세요? #일상      ││
│  │                                                    (45/280)   ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                   │
│  글 다듬기 (Claude AI):                                           │
│  ┌─────────────┐ ┌─────────────────┐ ┌─────────────┐              │
│  │ ✍️ 어조 유지 │ │ 🐦 트위터 스타일 │ │ 📏 280자 조정│              │
│  └─────────────┘ └─────────────────┘ └─────────────┘              │
│                                                                   │
│  ┌──────────────────────┐  ┌────────────┐                         │
│  │  이 내용 사용하기     │  │  📋 복사   │                         │
│  └──────────────────────┘  └────────────┘                         │
└───────────────────────────────────────────────────────────────────┘
```

#### 기능 상세

| 항목 | 설명 |
|------|------|
| **빠른 팁 선택** | 체크박스로 원하는 팁 선택 (최대 3개) |
| **반영하기 버튼** | 선택한 팁들을 원본 포스팅에 적용하여 제안 생성 |
| **포스팅 제안 칸** | AI가 생성한 최적화된 포스팅 표시 |
| **글 다듬기 버튼** | 제안 생성 후 Claude AI로 추가 다듬기 (포스팅 제안 박스 내) |
| **이 내용 사용하기** | 제안된 포스팅을 에디터에 반영 |
| **복사하기** | 제안된 포스팅을 클립보드에 복사 |

#### 동작 플로우

```
[원본 모드]
1. 사용자가 포스팅 작성 칸에 원본 입력
2. 실시간으로 분석 결과 + 빠른 팁 표시 (자동)
3. 사용자가 원하는 팁 선택 (최대 3개)
4. [반영하기] 버튼 클릭
5. 포스팅 제안 생성 + 글 다듬기 버튼 표시
6. (선택) 글 다듬기 버튼 클릭 → 제안 내용 즉시 업데이트
7. [이 내용 사용하기] 또는 [복사하기]로 완료

[답글/인용 모드]
1. 대상 포스트 URL 입력
2. 포스팅 내용 작성
3. [🔍 분석하기] 버튼 클릭 (수동)
4. 분석 결과 + 빠른 팁 표시
5. 빠른 팁 선택 → [반영하기] → 포스팅 제안 생성
6. 대상 포스트 언어에 맞춰 제안 내용 출력
7. (선택) 글 다듬기 → 제안 내용 즉시 업데이트
```

#### 팁 반영 우선순위

여러 팁이 선택된 경우, 다음 순서로 적용:
1. 콘텐츠 구조 변경 (질문 형태, CTA 추가 등)
2. 요소 추가 (이모지, 해시태그 등)
3. 문체/톤 조정

---

### 3.2.3 글 다듬기 기능 (Post Polish)

포스팅 제안이 생성된 후, Claude AI를 사용하여 제안 내용을 추가로 다듬는 기능입니다.

> **위치 변경**: 글 다듬기 버튼은 포스팅 제안 박스 내부에 위치하며, 제안이 생성된 후에만 사용 가능합니다.

#### 글 다듬기 버튼 (Claude 엔진)

| 버튼 | 설명 | 동작 |
|------|------|------|
| **✍️ 어조 유지** | 원본 어조를 유지하면서 문법 교정 | 맞춤법, 문법 오류 수정. 자연스럽고 멍청해 보이지 않게 다듬기. 원본 톤/스타일 유지 |
| **🐦 트위터 스타일** | 트위터에 적합한 문체로 변환 | 짧고 임팩트 있는 문장. 이모지/해시태그 적절히 추가. 캐주얼하고 engaging한 톤 |
| **📏 280자 조정** | X의 글자 제한에 맞게 조정 | 280자 이내로 압축. 핵심 메시지 유지. 불필요한 부분 제거 |

#### 다국어 지원

대상 포스트 URL의 언어를 자동 감지하여 해당 언어로 제안을 생성합니다:

| 언어 | 자동 감지 | 질문/CTA 예시 |
|------|----------|--------------|
| 한국어 (ko) | ✅ 한글 문자 | "어떻게 생각하시나요?" / "의견 남겨주세요!" |
| 영어 (en) | ✅ 기본 | "What do you think?" / "Share your thoughts!" |
| 일본어 (ja) | ✅ 히라가나/가타카나 | "皆さんはどう思いますか？" / "コメントお待ちしています!" |
| 중국어 (zh) | ✅ 한자 | "大家怎么看？" / "欢迎留言!" |

#### 동작 플로우

```
1. 빠른 팁 선택 → [반영하기] → 포스팅 제안 생성
2. 포스팅 제안 박스 내 글 다듬기 버튼 표시
3. 글 다듬기 버튼 클릭
4. Claude API가 선택한 스타일로 제안 내용 수정
5. 수정된 내용이 제안 박스에 즉시 반영
6. 필요시 다른 다듬기 버튼으로 추가 수정 가능
```

---

### 3.2.4 X 알고리즘 기반 팁 생성 (X Algorithm Advisor)

빠른 팁과 포스팅 제안을 X의 공개 알고리즘 지식을 기반으로 Claude AI가 생성합니다.

#### X 알고리즘 19가지 참여 액션

X 알고리즘이 예측하는 사용자 행동:

**긍정적 액션 (콘텐츠 부스트):**
| 액션 | 설명 | 영향 |
|------|------|------|
| favorite (좋아요) | 주요 랭킹 지표 | 높음 |
| reply (답글) | 댓글/답글 | 높음 |
| repost (리포스트) | 리트윗/공유 | 높음 |
| quote (인용) | 인용 트윗 | 높음 |
| click | 콘텐츠/링크 클릭 | 중간 |
| profile_click | 프로필 방문 | 중간 |
| share | 외부 공유 | 중간 |
| dwell | 머무르기 시간 | 중간 |
| video_view | 비디오 시청 | 중간 |
| follow_author | 작성자 팔로우 | 높음 |

**부정적 액션 (콘텐츠 억제):**
| 액션 | 설명 | 영향 |
|------|------|------|
| not_interested | 관심없음 표시 | 높음 (부정) |
| block_author | 작성자 차단 | 매우 높음 (부정) |
| mute_author | 작성자 뮤트 | 높음 (부정) |
| report | 신고 | 매우 높음 (부정) |

#### Claude AI 팁 생성 프로세스

```
입력:
├── 포스트 내용
├── 현재 예측 점수 (5각형)
├── 포스트 타입 (원본/답글/인용)
├── 대상 포스트 내용 (답글/인용 시)
└── 언어 설정

처리:
├── X 알고리즘 지식 기반 분석
├── Claude AI로 구체적 개선 제안 생성
└── 예상 점수 향상 계산

출력:
├── 빠른 팁 목록 (선택 가능)
├── 예상 영향도
└── 적용 시 예상 점수 변화
```

---

### 3.2.5 AI 개인화 포스트 생성 (Personalized Post Generator)

답글/인용 작성 시 사용자의 기존 포스팅 스타일을 분석하고, 선택한 페르소나를 적용하여 개인화된 포스트를 자동 생성합니다.

#### 페르소나 시스템 (Persona System) ✅ 구현 완료

4가지 페르소나 중 선택하여 AI 응답 스타일을 결정합니다:

| 페르소나 | 아이콘 | 설명 | 리스크 | Pentagon 부스트 |
|---------|--------|------|--------|----------------|
| **Empathetic** | 😊 | 따뜻하고 지지적인 공감 반응 | Low | engagement +15, quality +10 |
| **Contrarian** | 🔥 | 토론을 유발하는 반대 의견 | Medium | virality +20, engagement +15 |
| **Expander** | 🌱 | 관련 인사이트로 주제 확장 | Low | reach +15, longevity +10 |
| **Expert** | 🎓 | 깊이 있는 전문가적 분석 | Low | quality +20, longevity +15 |

#### 대상 포스트 심층 분석 (Target Analysis)

AI가 대상 포스트를 분석하여 적절한 응답 생성:

| 분석 항목 | 설명 |
|----------|------|
| **main_topic** | 포스트가 다루는 핵심 주제 |
| **key_points** | 주요 주장이나 포인트 |
| **sentiment** | 감정 톤 (optimistic, critical, curious 등) |
| **what_to_address** | 응답에서 다뤄야 할 구체적 내용 |

#### AI 대상 포스트 해석 (Interpretation)

대상 포스트의 숨은 의미를 Claude가 1-2문장으로 요약:

```
┌───────────────────────────────────────────────────────────────────┐
│  💡 이 포스트의 의미:                                              │
│  "작성자는 AI 발전 속도에 대한 우려를 표현하면서도, 그 잠재력에     │
│   대한 기대감을 드러내고 있습니다."                                 │
└───────────────────────────────────────────────────────────────────┘
```

- 20자 이상의 포스트에만 적용
- 포스트 언어에 맞춰 해석 생성
- Claude API 실패 시 graceful degradation

#### UI 레이아웃

```
┌───────────────────────────────────────────────────────────────────┐
│  🤖 AI 개인화 포스트 (답글/인용 전용)                              │
│                                                                   │
│  페르소나: [😊 Empathetic ▼]                                       │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │ "This is a fascinating perspective! The implications for     ││
│  │  distributed systems are huge 🚀"                            ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                   │
│  📊 스타일 분석:                                                   │
│  ├── 톤: Professional, Enthusiastic                              │
│  ├── 이모지 사용: 자주 사용                                        │
│  ├── 주요 토픽: Tech, AI, Startups                               │
│  └── 작성 패턴: 짧고 임팩트 있는 문장                               │
│                                                                   │
│  신뢰도: 78%                                                       │
│  💡 이유: 사용자의 최근 포스트 10개를 분석하여 스타일 매칭           │
│                                                                   │
│              [✅ 사용하기]    [📋 복사하기]                         │
└───────────────────────────────────────────────────────────────────┘
```

#### 스타일 분석 항목

| 항목 | 설명 |
|------|------|
| **톤 분석** | 포멀/캐주얼, 진지함/유머러스함 등 |
| **이모지 패턴** | 사용 빈도, 선호하는 이모지 타입 |
| **주제 분석** | 자주 다루는 토픽 (기술, 일상, 비즈니스 등) |
| **작성 패턴** | 문장 길이, 구조, 질문 사용 빈도 |
| **언어 스타일** | 줄임말 사용, 해시태그 패턴 등 |

#### 생성 프로세스

```
1. 사용자 최근 포스트 10개 분석 (Sela API)
2. 스타일 특성 추출 (Claude AI)
3. 대상 포스트 심층 분석 (main_topic, key_points, sentiment)
4. 선택한 페르소나 스타일 적용
5. 사용자 스타일 + 페르소나로 답글/인용 생성
6. 신뢰도 점수 계산 (60-85%)
7. 생성 이유 및 페르소나 영향 설명 제공
```

#### 사용 조건

- 답글(Reply) 또는 인용(Quote) 포스트 타입 선택 시에만 활성화
- 대상 포스트 URL 입력 필수
- 사용자 프로필 분석 완료 상태에서만 사용 가능

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

### 3.4 SNS 공유 기능 (Social Sharing) ✅ v1.12

#### 기능 설명
프로필 분석 결과를 SNS에 쉽게 공유할 수 있는 기능

#### 구현 내용

**1. 링크 복사 버튼**
- 프로필 분석 페이지 헤더에 공유 버튼 추가
- 클릭 시 현재 URL을 클립보드에 복사
- "Copied!" 피드백 표시 (1초간)

**2. Open Graph (OG) 이미지 생성**
- `/api/og/[username]` 엔드포인트에서 동적 이미지 생성
- Edge Runtime 사용 (빠른 응답)
- 오각형 레이더 차트 SVG 렌더링 (꼭지점에 스코어 라벨)
- 점수 및 유저네임 표시
- Twitter Card 지원 (summary_large_image)

**성능 최적화 (v1.13):**
- API 타임아웃: 10초 (안정성 향상)
- 캐시 헤더: `Cache-Control: public, max-age=3600, stale-while-revalidate=86400`
- Vercel Edge 캐싱으로 반복 요청 즉시 응답

```
OG 이미지 레이아웃 (1200x630):
┌────────────────────────────────────────────────────┐
│           Reach                                    │
│  ┌──────────┐       @username                      │
│  │ Pentagon │       X Profile Analysis             │
│  │  Chart   │                                      │
│  │  (SVG)   │       ● Reach        85              │
│  └──────────┘       ● Engagement   72              │
│ Longevity  Engagement ● Virality   90              │
│                       ● Quality    78              │
│  Quality   Virality   ● Longevity  65              │
│                                                    │
│                       Average      78              │
└────────────────────────────────────────────────────┘
```

**3. 공유 링크 방문자 UI**
- 공유된 링크로 방문 시 "Check your X" 버튼 표시
- 다른 사용자가 자신의 프로필을 분석하도록 유도

**4. 모바일 반응형 레이아웃 (v1.13)**
- 프로필 페이지 헤더 모바일 최적화
- 작은 화면에서 버튼들이 두 번째 줄로 이동
- 폰트 크기 및 패딩 반응형 조정

```
모바일 헤더 레이아웃:
┌─────────────────────────┐
│ ← @username             │  ← 첫째 줄
│   Profile Analysis      │
├─────────────────────────┤
│ 🔄 📤 [Check your X]    │  ← 둘째 줄: 버튼들
└─────────────────────────┘

데스크탑 헤더 레이아웃:
┌────────────────────────────────────────────┐
│ ← @username              🔄 📤 [Check your X] │
│   Profile Analysis                          │
└────────────────────────────────────────────┘
```

#### 메타데이터 설정
```typescript
// layout.tsx
openGraph: {
  title: `@${username} - Profile Analysis`,
  description: `Check out @${username}'s X profile analysis`,
  images: [`${baseUrl}/api/og/${username}`],
  type: "website",
},
twitter: {
  card: "summary_large_image",
  title: `@${username} - Profile Analysis`,
  images: [`${baseUrl}/api/og/${username}`],
}
```

---

### 3.5 브랜딩 (Branding) ✅ v1.12

#### Powered by Sela Network
- 랜딩 페이지 하단에 "Powered by Sela Network" 표시
- Sela Network 로고 (GitHub 아바타 이미지)
- 클릭 시 selanetwork.io로 이동 (새 탭)

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
│  │  ┌─────────────────┐                                                  │  │
│  │  │ XAlgorithmAdvisor│  ← X 알고리즘 기반 Claude AI 팁 생성            │  │
│  │  │ Service         │                                                  │  │
│  │  └─────────────────┘                                                  │  │
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
│  │ Sela API        │  │ Claude API      │                                   │
│  │ - User data     │  │ - 글 다듬기      │                                   │
│  │ - Post metrics  │  │ - Content       │                                   │
│  │ - Profile info  │  │   optimization  │                                   │
│  └─────────────────┘  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 다층 캐싱 전략 (Multi-Layer Caching)

API 비용 절감과 응답 속도 향상을 위한 3단계 캐싱 시스템:

```
┌─────────────────────────────────────────────────────────────────┐
│                         요청 처리 흐름                           │
│                                                                 │
│  요청 → [1. 인메모리 캐시] → [2. Supabase 캐시] → [3. Sela API]  │
│              ↓ hit              ↓ hit              ↓ fetch      │
│           즉시 반환          즉시 반환         데이터 조회       │
│                                                    ↓            │
│                                              캐시 저장 (비동기)  │
└─────────────────────────────────────────────────────────────────┘
```

| 캐시 레이어 | TTL | 용도 | 특징 |
|------------|-----|------|------|
| **인메모리** | 세션 동안 | 같은 인스턴스 내 반복 요청 | 가장 빠름, 인스턴스 재시작 시 초기화 |
| **Supabase** | 1시간 (프로필) / 15분 (포스트) | 프로필/분석 결과 캐싱 | API 비용 절감, 서버 간 공유 |
| **Sela API** | - | 원본 데이터 소스 | Rate limit 관리 필요 |

#### 언어 감지 캐싱

| 항목 | 값 | 설명 |
|------|-----|------|
| 캐시 크기 | 최대 1,000개 | LRU 방식으로 오래된 항목 제거 |
| 키 | 콘텐츠 해시 | 동일 텍스트 재분석 방지 |
| 지원 언어 | ko, en, ja, zh | 정규식 기반 자동 감지 |

#### 비동기 캐시 업데이트

```
응답 먼저 반환 → 백그라운드에서 캐시 저장
(사용자 대기 시간 최소화)
```

#### asyncio.gather 병렬 처리

```
프로필 조회 + 컨텍스트 조회를 동시에 실행
→ 응답 시간 50% 단축
```

#### 병렬 Polish API 호출 ✅ 구현 완료

```
Promise.all([polishSuggestion(), polishPersonalized()])
→ 두 패널 동시 처리, 대기 시간 50% 단축
```

#### 프론트엔드 프로필 캐싱 ✅ 구현 완료

| 항목 | 값 | 설명 |
|------|-----|------|
| 저장소 | sessionStorage | 브라우저 세션 동안 유지 |
| 용도 | 프로필 분석 결과 캐싱 | compose 페이지에서 돌아올 때 즉시 로드 |
| 효과 | API 호출 제거 | 페이지 전환 시 즉각적인 응답 |
| 새로고침 | 🔄 버튼 | 캐시 무시하고 API에서 최신 데이터 가져오기 |

#### Lazy Loading (RadarChart)

```
- 동적 import로 차트 컴포넌트 분리
- 초기 번들 사이즈 ~500KB 감소
- 분석 실행 시에만 로드
```

---

### 5.2 UI/UX 개선사항 ✅ 구현 완료

#### PostEditor 3행 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│  ROW 1: 입력 + 분석 결과 (좌우 배치, 모바일에서는 상하)           │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ 포스트 타입 선택     │  │ 레이더 차트         │               │
│  │ 대상 URL 입력       │  │ (예상/개선 점수)    │               │
│  │ 콘텐츠 입력 (280자) │  │ 평균 점수 표시      │               │
│  │ [분석하기]          │  │                     │               │
│  └─────────────────────┘  └─────────────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  ROW 2: 빠른 팁 섹션                                             │
│  ☐ 팁1  ☐ 팁2  ☐ 팁3 (최대 3개 선택)  [반영하기]                │
├─────────────────────────────────────────────────────────────────┤
│  ROW 3: 제안 패널 + 컨트롤                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 페르소나 선택 [😊▼]  │  Polish [어조▼]  Translate [EN▼]     ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ 📝 포스팅 제안       │  │ 🤖 AI 개인화 포스트 │               │
│  │ (팁 적용 결과)      │  │ (페르소나 적용)     │               │
│  └─────────────────────┘  └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

#### 개선된 점수 시각화

| 상태 | 차트 제목 | 색상 | 설명 |
|------|----------|------|------|
| 분석 후 | "Predicted Score" | 기본 | 예상 점수 표시 |
| 팁 적용 후 | "✨ Improved Score" | 초록색 | 개선된 점수 (+15) 형식 |

- `predicted_improvement` 응답 파싱 ("+15%" → 15)
- 점수 범위 0-100 클램핑
- 분석/포스트 타입 변경 시 리셋

#### 모바일 최적화

| 기능 | 데스크톱 | 모바일 |
|------|---------|--------|
| 제안 패널 | 좌우 배치 | 탭 전환 (Suggestion / AI Post) |
| Polish/Translate | 버튼 나열 | 드롭다운 메뉴 |
| 대상 포스트 미리보기 | 200자 | 50자 |
| 페르소나 이름 | 표시 | 아이콘만 |
| 뒤로가기 | 텍스트 | 큰 화살표 (text-3xl) |

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

-- 인덱스 (단일 컬럼)
CREATE INDEX idx_profile_cache_username ON profile_cache(x_username);
CREATE INDEX idx_profile_cache_expires ON profile_cache(expires_at);
CREATE INDEX idx_profile_analyses_username ON profile_analyses(x_username);
CREATE INDEX idx_post_context_cache_post_id ON post_context_cache(post_id);
CREATE INDEX idx_post_context_cache_expires ON post_context_cache(expires_at);
CREATE INDEX idx_analysis_stats_created ON analysis_stats(created_at DESC);

-- 복합 인덱스 (자주 사용되는 쿼리 패턴 최적화)
CREATE INDEX idx_profile_cache_user_expires ON profile_cache(x_username, expires_at DESC);
CREATE INDEX idx_profile_analyses_user_created ON profile_analyses(x_username, created_at DESC);
CREATE INDEX idx_post_context_cache_id_expires ON post_context_cache(post_id, expires_at DESC);

-- 만료된 캐시 자동 정리 함수
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM profile_cache WHERE expires_at < NOW();
    DELETE FROM profile_analyses WHERE expires_at < NOW();
    DELETE FROM post_context_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- RLS (Row Level Security) - 공개 서비스이므로 모든 접근 허용
ALTER TABLE profile_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_context_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access" ON profile_cache FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON profile_analyses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON post_context_cache FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access" ON analysis_stats FOR ALL USING (true) WITH CHECK (true);
```

#### 📋 추가 예정 테이블

```sql
-- Claude 제안 캐시 (AI 응답 캐싱) - 코드에서 사용 중, 테이블 생성 필요
CREATE TABLE suggestion_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash TEXT UNIQUE NOT NULL,
    suggestion_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour')
);

-- 사용자 활동 로그 - 코드에서 사용 중, 테이블 생성 필요
CREATE TABLE user_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_handle TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_handle TEXT,
    target_url TEXT,
    post_content TEXT,
    scores JSONB,
    quick_tips JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
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
    "media_type": null,                 // "image" | "video" | "gif" | null
    "target_language": null             // [reply/quote 선택] "ko" | "en" | "ja" | "zh" | null
                                        // 대상 포스트를 가져올 수 없을 때 사용자가 직접 지정
}

// Reply 예시
{
    "username": "myusername",
    "content": "This is a great point!",
    "post_type": "reply",
    "target_post_url": "https://x.com/elonmusk/status/1234567890",
    "media_type": null,
    "target_language": "en"          // 대상 포스트 언어 (선택적)
}

// Quote 예시
{
    "username": "myusername",
    "content": "Interesting perspective on AI 🤔",
    "post_type": "quote",
    "target_post_url": "https://x.com/techcrunch/status/9876543210",
    "media_type": "image",
    "target_language": null          // null이면 자동 감지 시도
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

#### AI 개인화 포스트 생성
```
POST /api/v1/post/generate-personalized

Request:
{
    "username": "myusername",
    "target_post_url": "https://x.com/elonmusk/status/1234567890",
    "post_type": "reply"          // "reply" | "quote"
}

Response:
{
    "generated_content": "This is a fascinating perspective! The implications for distributed systems are huge 🚀",
    "style_analysis": {
        "tone": ["Professional", "Enthusiastic"],
        "emoji_usage": "frequent",
        "topics": ["Tech", "AI", "Startups"],
        "writing_pattern": "Short, impactful sentences"
    },
    "confidence_score": 78,
    "reasoning": "Based on analysis of your recent 10 posts, this reply matches your typical enthusiastic tone about tech topics with strategic emoji usage.",
    "target_post_summary": {
        "author": "elonmusk",
        "content_preview": "The future of AI is..."
    }
}

// 프로필 분석 불가 시 (graceful degradation)
Response:
{
    "generated_content": null,
    "error": "profile_not_available",
    "message": "사용자 프로필을 분석할 수 없습니다. 직접 작성해주세요."
}
```

#### 글 다듬기 (Claude 엔진)
```
POST /api/v1/post/polish

Request:
{
    "content": "This is really insightful! I think the future of AI will be amazing",
    "polish_type": "grammar",      // "grammar" | "twitter" | "280char" | "translate_en" | "translate_ko" | "translate_zh"
    "language": "en",              // 자동 감지 또는 명시적 지정
    "target_post_content": "..."   // (선택) 어조 매칭용 대상 포스트 내용
}

// polish_type 옵션:
// - "grammar": 대상 포스트 어조에 맞춰 문법 교정
// - "twitter": 트위터 스타일로 변환
// - "280char": 280자 이내로 압축
// - "translate_en": 영어로 번역
// - "translate_ko": 한국어로 번역
// - "translate_zh": 중국어로 번역

Response:
{
    "original_content": "This is really insightful! I think the future of AI will be amazing",
    "polished_content": "This is really insightful! I think the future of AI will be amazing 🚀",
    "polish_type": "grammar",
    "language_detected": "en",
    "changes": [
        {
            "type": "grammar_fix",
            "description": "No grammar issues found"
        },
        {
            "type": "enhancement",
            "description": "Added emoji for engagement"
        }
    ],
    "character_count": {
        "original": 71,
        "polished": 73
    }
}

// 280자 조정 예시
Request:
{
    "content": "I've been thinking about this for a long time and I really believe that the integration of artificial intelligence into our daily workflows will fundamentally transform how we approach problem-solving and creativity in ways we can't even imagine yet...",
    "polish_type": "280char",
    "language": "en"
}

Response:
{
    "original_content": "I've been thinking about this...",
    "polished_content": "AI integration will fundamentally transform how we approach problem-solving and creativity in ways we can't yet imagine 🤖✨",
    "polish_type": "280char",
    "language_detected": "en",
    "changes": [
        {
            "type": "compression",
            "description": "Condensed to 280 characters while preserving key message"
        }
    ],
    "character_count": {
        "original": 256,
        "polished": 124
    }
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

##### 키워드 기반 타겟 스코어 감지 ✅ v1.10

팁 설명에서 키워드를 분석하여 올바른 스코어 카테고리에 개선 효과를 매핑:

| 타겟 스코어 | 감지 키워드 |
|------------|------------|
| Virality | virality, viral, repost, quote, share |
| Reach | reach, hashtag, discover, visibility |
| Quality | quality, insight, value, depth |
| Longevity | longevity, dwell, evergreen, lasting |
| Engagement | (기본값) favorite, reply, engagement |

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

#### 실시간 스코어 (WebSocket) 📋 미구현
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

#### Admin API ✅ 구현 완료
```
POST /api/v1/admin/cleanup-cache

Description: 만료된 캐시 데이터 정리 (관리자 전용)

Response:
{
    "deleted": {
        "profile_cache": 15,
        "profile_analyses": 8,
        "post_context_cache": 42,
        "suggestion_cache": 23
    },
    "message": "Cache cleanup completed"
}
```

#### 헬스 체크
```
GET /health

Response:
{
    "status": "ok"
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
│   │   ├── x_algorithm_advisor.py  # X 알고리즘 기반 팁 생성 (Claude AI)
│   │   └── sela_api_client.py      # Sela API 클라이언트
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

### 8.2 Frontend (Next.js) ✅ 구현 완료

```
frontend/
├── package.json
├── next.config.ts
├── tailwind.config.js
├── .env.local.example
├── .env.local                  # 환경변수 (gitignore)
│
└── src/
    ├── app/
    │   ├── layout.tsx              # 루트 레이아웃
    │   ├── page.tsx                # 랜딩 페이지 (유저네임 입력)
    │   ├── globals.css
    │   │
    │   └── [username]/             # 동적 라우트: /elonmusk
    │       ├── page.tsx            # 프로필 분석 결과
    │       ├── loading.tsx         # 로딩 UI
    │       └── compose/
    │           └── page.tsx        # 포스트 작성 & 분석
    │
    ├── components/
    │   ├── charts/
    │   │   └── RadarChart.tsx      # Recharts 5각형 레이더 차트
    │   │
    │   └── editor/
    │       └── PostEditor.tsx      # 통합 포스트 에디터
    │                               # - 포스트 타입 선택
    │                               # - 대상 포스트 URL 입력 (debounced)
    │                               # - 실시간 스코어 표시
    │                               # - 빠른 팁 선택 (최대 3개)
    │                               # - 글 다듬기 버튼
    │                               # - AI 개인화 포스트 생성
    │
    ├── lib/
    │   ├── api.ts                  # API 클라이언트 (싱글톤)
    │   └── utils.ts                # 유틸리티 함수
    │
    └── types/
        └── api.ts                  # API 타입 정의
```

#### API 클라이언트 (`lib/api.ts`)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| `analyzeProfile(username)` | GET /api/v1/profile/{username}/analyze | 프로필 분석 |
| `analyzePost(request)` | POST /api/v1/post/analyze | 포스트 스코어 예측 |
| `applyTips(request)` | POST /api/v1/post/apply-tips | 팁 적용하여 제안 생성 |
| `polishPost(request)` | POST /api/v1/post/polish | 글 다듬기/번역 |
| `getPostContext(url)` | GET /api/v1/post/context | 대상 포스트 컨텍스트 |
| `generatePersonalizedPost(request)` | POST /api/v1/post/generate-personalized | AI 개인화 포스트 |
| `getPersonas()` | GET /api/v1/post/personas | 페르소나 목록 조회 |

---

## 9. 개발 단계

### Phase 1: 기반 구축 (MVP) ✅ 완료
| 태스크 | 설명 | 상태 |
|--------|------|------|
| 프로젝트 설정 | FastAPI + Next.js 프로젝트 초기화 | ✅ |
| Supabase 설정 | 데이터베이스 스키마 생성 (캐싱 테이블) | ✅ |
| Sela API 연동 | X 데이터 조회 기능 구현 | ✅ |
| 기본 UI | 랜딩 페이지, 유저네임 입력 폼 | ✅ |

### Phase 2: 핵심 기능 ✅ 완료
| 태스크 | 설명 | 상태 |
|--------|------|------|
| 프로필 분석 | Sela API로 프로필 데이터 수집 및 분석 | ✅ |
| 스코어 예측 엔진 | X 알고리즘 기반 14가지 행동 확률 예측 | ✅ |
| 레이더 차트 | Recharts 기반 5각형 스코어 시각화 | ✅ |
| 포스트 에디터 | 포스트 타입별 작성 및 분석 UI | ✅ |
| 대상 포스트 분석 | 답글/인용 대상 포스트 컨텍스트 분석 | ✅ |
| 기회 점수 | Opportunity Score 계산 및 표시 | ✅ |

### Phase 3: 최적화 기능 ✅ 완료
| 태스크 | 설명 | 상태 |
|--------|------|------|
| 빠른 팁 생성 | X Algorithm Advisor (Claude AI) | ✅ |
| 팁 선택 및 적용 | 최대 3개 팁 선택 → 포스팅 제안 생성 | ✅ |
| 글 다듬기 | 어조 유지/트위터 스타일/280자 조정 | ✅ |
| AI 개인화 포스트 | 사용자 스타일 분석 기반 자동 생성 | ✅ |
| 다층 캐싱 | 인메모리 → Supabase → API 캐싱 | ✅ |
| 다국어 지원 | 한국어/영어/일본어/중국어 | ✅ |

### Phase 4: 고도화 🔄 진행 예정
| 태스크 | 설명 | 상태 |
|--------|------|------|
| 실시간 스코어 | WebSocket 기반 타이핑 중 스코어 업데이트 | 📋 |
| 실제 성과 추적 | 포스팅 후 실제 metrics 수집 및 비교 | 📋 |
| 모델 개선 | 실제 데이터 기반 예측 정확도 개선 | 📋 |
| 사용자 인증 | 계정 기반 히스토리 관리 | 📋 |
| Rate Limiting | IP 기반 요청 제한 | 📋 |
| 스레드 분석 | 연속 포스트 시리즈 분석 | 📋 |
| 최적 시간대 추천 | 사용자별 포스팅 최적 시간 분석 | 📋 |

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

# Claude (for polish & content optimization)
ANTHROPIC_API_KEY=your-anthropic-api-key

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
- **TWITTER_POST 스크래핑 제한**: 개별 포스트 직접 스크래핑 불가 (빈 결과 반환)
  - 대안: TWITTER_PROFILE로 작성자의 최근 200개 포스트 내에서 검색
  - 최근 포스트에 없는 경우 사용자가 언어 직접 선택

#### 포스트 타입별 지원 현황 ✅ v1.12

| 포스트 타입 | 지원 여부 | 비고 |
|------------|----------|------|
| 일반 트윗 | ✅ 지원 | 텍스트 + 메트릭스 정상 작동 |
| 이미지/비디오 포함 | ✅ 지원 | 콘텐츠 + 미디어 URL 제공 |
| Reply (답글) | ⚠️ 부분 지원 | 답글 텍스트만 제공, 원본 트윗 정보 없음 |
| Quote (인용) | ⚠️ 부분 지원 | 인용 코멘트만 제공, `quoteContent` 필드 None 반환 |
| Retweet (리트윗) | ❌ 미지원 | `isRetweet` 필드 None, 콘텐츠 없이 반환 |
| X Article (긴글) | ❌ 미지원 | 콘텐츠 빈 문자열 반환 |

**API 필드 제한:**
```
isRetweet: None (항상)
isQuote: None (항상)
quoteContent: None (항상)
```

> **참고**: Sela API 자체의 제한사항으로, API 업데이트 시 개선 가능

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

*문서 버전: 1.13*
*최종 수정: 2026-01-28*
*변경사항:
- v1.2: 포스팅 제안 기능 추가 (빠른 팁 선택 → 최적화된 포스팅 자동 생성)
- v1.3: 답글/인용 분석 및 글 다듬기 기능 추가 (분석하기 버튼, Claude 기반 글 다듬기 3종)
- v1.4: 글 다듬기 버튼 위치를 포스팅 제안 박스 내부로 이동, 다국어 자동 감지 및 지원 (한/영/일/중)
- v1.5: X 알고리즘 기반 팁 생성 (XAlgorithmAdvisor), Sela API TWITTER_POST 제한사항 문서화, 대상 포스트 언어 수동 선택 UI 추가
- v1.6: 현재 구현 상태 반영 - 기술 스택 버전 명시, AI 개인화 포스트 생성 기능 추가, 다층 캐싱 전략 문서화, 개발 단계 완료 상태 업데이트
- v1.7: 실제 구현 상태 동기화 - 프론트엔드 구조(src/ 디렉토리), 번역 기능(translate_en/ko/zh), DB 스키마 업데이트, API 클라이언트 메서드 목록
- v1.8: 코드베이스 완전 동기화 - 프로필 분석 10개 포스트로 변경, 스코어 계산 기준 상세화, 컨텍스트 부스트 임계값(100K views, 60분, 1000 replies), Freshness 분류 기준, Admin API 문서화, 언어 감지 캐싱, asyncio.gather 병렬 처리, DB 스키마 실제 구현 상태 반영
- v1.9: UI/UX 고도화 - 페르소나 시스템(4종), AI 대상 포스트 해석, 개선된 점수 시각화(초록색), PostEditor 3행 레이아웃, 병렬 Polish API, 프로필 캐싱(sessionStorage), /personas API 엔드포인트 추가
- v1.10: 스코어 안정성 개선 - 스코어 최소 임계값 설정(engagement 3%, virality 0.5%), 키워드 기반 팁 타겟 스코어 감지(virality/reach/quality/longevity 키워드 매핑)
- v1.11: 프로필 분석 개선 - 프로필 스코어 최소값(Reach 10, Engagement/Virality 5), 새로고침 버튼(캐시 무시하고 최신 데이터 가져오기)
- v1.12: SNS 공유 및 브랜딩 - 프로필 요약 기능(브랜드 감지 및 강점 분석), OG 이미지 동적 생성(오각형 레이더 차트), 링크 복사 버튼, 공유 링크 방문자 UI, Powered by Sela Network 브랜딩, 백엔드 인메모리 캐싱(1시간 TTL)
- v1.13: 성능 및 UX 개선 - OG 이미지 캐싱(1시간 브라우저/CDN, 24시간 stale-while-revalidate), API 타임아웃 증가(5초→10초), 모바일 반응형 헤더 레이아웃, OG 이미지 레이아웃 개선(꼭지점 라벨, 세로 스코어 리스트, Average 표시)*
