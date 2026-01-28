import { ImageResponse } from "next/og";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PentagonScores {
  reach: number;
  engagement: number;
  virality: number;
  quality: number;
  longevity: number;
}

interface ProfileAnalysis {
  username: string;
  summary: string;
  scores: PentagonScores;
}

function getPoint(cx: number, cy: number, radius: number, index: number): { x: number; y: number } {
  const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
  return {
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle),
  };
}

function pentagonPath(cx: number, cy: number, radius: number): string {
  const pts = [0, 1, 2, 3, 4].map((i) => getPoint(cx, cy, radius, i));
  return `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y} L ${pts[2].x} ${pts[2].y} L ${pts[3].x} ${pts[3].y} L ${pts[4].x} ${pts[4].y} Z`;
}

function scorePath(cx: number, cy: number, scores: number[], maxR: number): string {
  const pts = scores.map((s, i) => getPoint(cx, cy, (s / 100) * maxR, i));
  return `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y} L ${pts[2].x} ${pts[2].y} L ${pts[3].x} ${pts[3].y} L ${pts[4].x} ${pts[4].y} Z`;
}

export const runtime = "edge";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ username: string }> }
) {
  const { username } = await params;

  let analysis: ProfileAnalysis | null = null;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/profile/${username}/analyze`,
      {
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
      }
    );
    clearTimeout(timeoutId);

    if (response.ok) {
      analysis = await response.json();
    }
  } catch {
    // Use fallback values
  }

  const scores = analysis?.scores || {
    reach: 50,
    engagement: 50,
    virality: 50,
    quality: 50,
    longevity: 50,
  };

  const cx = 220;
  const cy = 230;
  const maxR = 150;

  const scoreArr = [scores.reach, scores.engagement, scores.virality, scores.quality, scores.longevity];
  const labels = ["Reach", "Engagement", "Virality", "Quality", "Longevity"];
  const colors = ["#3B82F6", "#22C55E", "#A855F7", "#EAB308", "#F97316"];

  const grid1 = pentagonPath(cx, cy, maxR * 0.25);
  const grid2 = pentagonPath(cx, cy, maxR * 0.5);
  const grid3 = pentagonPath(cx, cy, maxR * 0.75);
  const grid4 = pentagonPath(cx, cy, maxR);
  const dataPath = scorePath(cx, cy, scoreArr, maxR);

  const axes = [0, 1, 2, 3, 4].map((i) => getPoint(cx, cy, maxR, i));
  const scorePts = scoreArr.map((s, i) => getPoint(cx, cy, (s / 100) * maxR, i));
  const labelPts = [0, 1, 2, 3, 4].map((i) => getPoint(cx, cy, maxR + 30, i));

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#111827",
          padding: "40px 80px 40px 120px",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Left - Pentagon Chart */}
        <div style={{ display: "flex", position: "relative", width: "440px", height: "460px" }}>
          <svg width="440" height="460" viewBox="0 0 440 460">
            {/* Grid lines */}
            <path d={grid1} fill="none" stroke="#374151" strokeWidth="1" />
            <path d={grid2} fill="none" stroke="#374151" strokeWidth="1" />
            <path d={grid3} fill="none" stroke="#374151" strokeWidth="1" />
            <path d={grid4} fill="none" stroke="#374151" strokeWidth="2" />

            {/* Axes */}
            <line x1={cx} y1={cy} x2={axes[0].x} y2={axes[0].y} stroke="#374151" strokeWidth="1" />
            <line x1={cx} y1={cy} x2={axes[1].x} y2={axes[1].y} stroke="#374151" strokeWidth="1" />
            <line x1={cx} y1={cy} x2={axes[2].x} y2={axes[2].y} stroke="#374151" strokeWidth="1" />
            <line x1={cx} y1={cy} x2={axes[3].x} y2={axes[3].y} stroke="#374151" strokeWidth="1" />
            <line x1={cx} y1={cy} x2={axes[4].x} y2={axes[4].y} stroke="#374151" strokeWidth="1" />

            {/* Data polygon */}
            <path d={dataPath} fill="rgba(59, 130, 246, 0.35)" stroke="#3B82F6" strokeWidth="3" />

            {/* Score points - small circles */}
            <circle cx={scorePts[0].x} cy={scorePts[0].y} r="5" fill={colors[0]} />
            <circle cx={scorePts[1].x} cy={scorePts[1].y} r="5" fill={colors[1]} />
            <circle cx={scorePts[2].x} cy={scorePts[2].y} r="5" fill={colors[2]} />
            <circle cx={scorePts[3].x} cy={scorePts[3].y} r="5" fill={colors[3]} />
            <circle cx={scorePts[4].x} cy={scorePts[4].y} r="5" fill={colors[4]} />
          </svg>
          {/* Labels positioned absolutely */}
          <span style={{ position: "absolute", left: `${labelPts[0].x - 30}px`, top: `${labelPts[0].y - 30}px`, fontSize: "16px", fontWeight: "bold", color: colors[0] }}>{labels[0]}</span>
          <span style={{ position: "absolute", left: `${labelPts[1].x + 10}px`, top: `${labelPts[1].y - 5}px`, fontSize: "16px", fontWeight: "bold", color: colors[1] }}>{labels[1]}</span>
          <span style={{ position: "absolute", left: `${labelPts[2].x + 5}px`, top: `${labelPts[2].y + 5}px`, fontSize: "16px", fontWeight: "bold", color: colors[2] }}>{labels[2]}</span>
          <span style={{ position: "absolute", left: `${labelPts[3].x - 70}px`, top: `${labelPts[3].y + 5}px`, fontSize: "16px", fontWeight: "bold", color: colors[3] }}>{labels[3]}</span>
          <span style={{ position: "absolute", left: `${labelPts[4].x - 90}px`, top: `${labelPts[4].y - 5}px`, fontSize: "16px", fontWeight: "bold", color: colors[4] }}>{labels[4]}</span>
        </div>

        {/* Right - Info */}
        <div style={{ display: "flex", flexDirection: "column", flex: 1, paddingLeft: "80px", justifyContent: "center" }}>
          {/* Username */}
          <span style={{ fontSize: "52px", fontWeight: "bold", color: "white" }}>
            @{username}
          </span>
          <span style={{ fontSize: "20px", color: "#6B7280", marginTop: "4px" }}>
            X Profile Analysis
          </span>

          {/* Scores - Vertical */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginTop: "30px" }}>
            {scoreArr.map((score, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center" }}>
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: colors[i] }} />
                <span style={{ fontSize: "18px", color: "#9CA3AF", marginLeft: "12px", width: "120px" }}>{labels[i]}</span>
                <span style={{ fontSize: "26px", fontWeight: "bold", color: colors[i], marginLeft: "40px" }}>{Math.round(score)}</span>
              </div>
            ))}
          </div>

          {/* Average */}
          <div style={{ display: "flex", alignItems: "center", marginTop: "30px" }}>
            <span style={{ fontSize: "22px", fontWeight: "bold", color: "white", width: "132px" }}>Average</span>
            <span style={{ fontSize: "32px", fontWeight: "bold", color: "white", marginLeft: "40px" }}>
              {Math.round(scoreArr.reduce((a, b) => a + b, 0) / 5)}
            </span>
          </div>

          {/* Footer - X Score Optimizer */}
          <div style={{ display: "flex", marginTop: "auto", paddingTop: "20px" }}>
            <span style={{ fontSize: "28px", fontWeight: "bold", color: "#3B82F6" }}>X Score Optimizer</span>
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      headers: {
        "Cache-Control": "public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400",
      },
    }
  );
}
