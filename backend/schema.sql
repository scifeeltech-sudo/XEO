-- XEO Database Schema for Supabase
-- Run this in Supabase SQL Editor

-- 프로필 캐시 (Sela API 호출 결과 캐싱)
CREATE TABLE IF NOT EXISTS profile_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    x_username TEXT UNIQUE NOT NULL,
    x_user_id TEXT,
    x_display_name TEXT,
    x_profile_image_url TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    profile_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 hour')
);

-- 프로필 분석 결과 캐시
CREATE TABLE IF NOT EXISTS profile_analyses (
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
CREATE TABLE IF NOT EXISTS post_context_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT UNIQUE NOT NULL,
    post_url TEXT NOT NULL,
    author_username TEXT NOT NULL,
    author_data JSONB,
    content_data JSONB,
    metrics_data JSONB,
    analysis_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '15 minutes')
);

-- 분석 통계 (서비스 사용량 추적)
CREATE TABLE IF NOT EXISTS analysis_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    x_username TEXT,
    analysis_type TEXT NOT NULL,
    session_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 (단일 컬럼)
CREATE INDEX IF NOT EXISTS idx_profile_cache_username ON profile_cache(x_username);
CREATE INDEX IF NOT EXISTS idx_profile_cache_expires ON profile_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_profile_analyses_username ON profile_analyses(x_username);
CREATE INDEX IF NOT EXISTS idx_post_context_cache_post_id ON post_context_cache(post_id);
CREATE INDEX IF NOT EXISTS idx_post_context_cache_expires ON post_context_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_analysis_stats_created ON analysis_stats(created_at DESC);

-- 복합 인덱스 (자주 사용되는 쿼리 패턴 최적화)
CREATE INDEX IF NOT EXISTS idx_profile_cache_user_expires ON profile_cache(x_username, expires_at DESC);
CREATE INDEX IF NOT EXISTS idx_profile_analyses_user_created ON profile_analyses(x_username, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_context_cache_id_expires ON post_context_cache(post_id, expires_at DESC);

-- 만료된 캐시 자동 정리 함수
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM profile_cache WHERE expires_at < NOW();
    DELETE FROM profile_analyses WHERE expires_at < NOW();
    DELETE FROM post_context_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Supabase pg_cron 확장 사용 시 자동 정리 스케줄 (선택사항)
-- 아래 명령어는 pg_cron 확장이 활성화되어 있을 때만 실행
-- SELECT cron.schedule('cleanup-expired-cache', '0 * * * *', 'SELECT cleanup_expired_cache()');

-- 수동 정리용 (API 엔드포인트에서 호출 가능)
-- SELECT cleanup_expired_cache();

-- RLS (Row Level Security) 비활성화 - 공개 서비스이므로
ALTER TABLE profile_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_context_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_stats ENABLE ROW LEVEL SECURITY;

-- 모든 사용자에게 읽기/쓰기 권한 부여
CREATE POLICY "Allow all access to profile_cache" ON profile_cache FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to profile_analyses" ON profile_analyses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to post_context_cache" ON post_context_cache FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to analysis_stats" ON analysis_stats FOR ALL USING (true) WITH CHECK (true);
