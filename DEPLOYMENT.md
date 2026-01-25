# XEO 배포 가이드

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│    Backend      │────▶│   Supabase      │
│   (Vercel)      │     │   (Railway)     │     │   (Database)    │
│ xeo.vercel.app  │     │ xeo-api.up.railway.app  YOUR_PROJECT_ID │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Sela API     │
                        │ dev-api.sela... │
                        └─────────────────┘
```

## 1. Backend 배포 (Railway - 무료)

### 1.1 Railway 설정

1. [Railway](https://railway.app) 가입 (GitHub 연동)
2. "New Project" → "Deploy from GitHub repo"
3. `scifeeltech-sudo/XEO` 저장소 선택
4. Root Directory: `backend` 설정

### 1.2 환경 변수 설정

Railway 대시보드 → Variables 에서 추가:

```
SELA_API_BASE_URL=http://dev-api.selanetwork.io:8083
SELA_API_KEY=REDACTED_API_KEY
SELA_PRINCIPAL_ID=7h2qg-u2cey-fwwkw-vyf6b-jljk4-qiirx-3ypdu-r7tml-fg2qz-eveqw-gae
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
CORS_ORIGINS=https://xeo.vercel.app,https://xeo-*.vercel.app
APP_ENV=production
APP_DEBUG=false
```

### 1.3 배포 확인

Railway가 자동으로 `railway.json` 설정을 읽어 배포합니다.

배포 후 URL 예시: `https://xeo-api-production.up.railway.app`

헬스체크: `curl https://your-railway-url/health`

---

## 2. Frontend 배포 (Vercel - 무료)

### 2.1 Vercel 설정

1. [Vercel](https://vercel.com) 가입 (GitHub 연동)
2. "Add New Project" → `scifeeltech-sudo/XEO` 선택
3. Framework Preset: Next.js
4. Root Directory: `frontend`

### 2.2 환경 변수 설정

Vercel 대시보드 → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://xeo-api-production.up.railway.app
```

### 2.3 배포

Push to main branch → 자동 배포

URL 예시: `https://xeo.vercel.app` 또는 `https://xeo-scifeeltech-sudo.vercel.app`

---

## 3. 빠른 배포 명령어

### Backend (Railway CLI)

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
cd backend
railway link

# 배포
railway up
```

### Frontend (Vercel CLI)

```bash
# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login

# 배포 (frontend 폴더에서)
cd frontend
vercel --prod
```

---

## 4. 환경별 설정 요약

### Development (로컬)

```bash
# Backend
cd backend
cp .env.example .env
# .env 수정
uv run uvicorn src.main:app --reload

# Frontend
cd frontend
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Production

| 서비스 | 환경변수 위치 |
|--------|--------------|
| Backend (Railway) | Railway Dashboard → Variables |
| Frontend (Vercel) | Vercel Dashboard → Environment Variables |
| Database (Supabase) | 이미 설정됨 |

---

## 5. 도메인 없이 사용

Vercel과 Railway 모두 무료 서브도메인을 제공합니다:

- Frontend: `https://xeo-[random].vercel.app`
- Backend: `https://xeo-api-[random].up.railway.app`

나중에 커스텀 도메인 연결도 간단합니다:
- Vercel: Settings → Domains → Add
- Railway: Settings → Domains → Add Custom Domain

---

## 6. 비용

| 서비스 | 무료 한도 |
|--------|----------|
| Vercel | 100GB 대역폭/월 |
| Railway | $5 크레딧/월 (약 500시간) |
| Supabase | 500MB DB, 1GB 스토리지 |

XEO 서비스는 가벼워서 무료 한도 내에서 충분히 운영 가능합니다.
