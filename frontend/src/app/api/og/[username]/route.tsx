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

// Pentagon chart helper functions
function getPoint(
  cx: number,
  cy: number,
  radius: number,
  index: number
): { x: number; y: number } {
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
    const timeoutId = setTimeout(() => controller.abort(), 5000);

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

  const cx = 150;
  const cy = 150;
  const maxR = 120;

  const scoreArr = [scores.reach, scores.engagement, scores.virality, scores.quality, scores.longevity];
  const labels = ["Reach", "Engage", "Viral", "Quality", "Long"];
  const colors = ["#3B82F6", "#22C55E", "#A855F7", "#EAB308", "#F97316"];

  // Pre-calculate all paths as strings
  const grid1 = pentagonPath(cx, cy, maxR * 0.25);
  const grid2 = pentagonPath(cx, cy, maxR * 0.5);
  const grid3 = pentagonPath(cx, cy, maxR * 0.75);
  const grid4 = pentagonPath(cx, cy, maxR);
  const dataPath = scorePath(cx, cy, scoreArr, maxR);

  // Pre-calculate axis lines
  const axes = [0, 1, 2, 3, 4].map((i) => getPoint(cx, cy, maxR, i));

  // Pre-calculate score points
  const scorePts = scoreArr.map((s, i) => getPoint(cx, cy, (s / 100) * maxR, i));

  // Pre-calculate label positions
  const labelPts = [0, 1, 2, 3, 4].map((i) => getPoint(cx, cy, maxR + 30, i));

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#111827",
          padding: "40px",
        }}
      >
        {/* Left - Chart */}
        <div style={{ display: "flex", width: "450px", alignItems: "center", justifyContent: "center" }}>
          <div style={{ display: "flex", position: "relative", width: "300px", height: "300px" }}>
            <svg width="300" height="300" viewBox="0 0 300 300">
              {/* Grid */}
              <path d={grid1} fill="none" stroke="#374151" strokeWidth="1" />
              <path d={grid2} fill="none" stroke="#374151" strokeWidth="1" />
              <path d={grid3} fill="none" stroke="#374151" strokeWidth="1" />
              <path d={grid4} fill="none" stroke="#374151" strokeWidth="1" />

              {/* Axes */}
              <line x1={cx} y1={cy} x2={axes[0].x} y2={axes[0].y} stroke="#374151" strokeWidth="1" />
              <line x1={cx} y1={cy} x2={axes[1].x} y2={axes[1].y} stroke="#374151" strokeWidth="1" />
              <line x1={cx} y1={cy} x2={axes[2].x} y2={axes[2].y} stroke="#374151" strokeWidth="1" />
              <line x1={cx} y1={cy} x2={axes[3].x} y2={axes[3].y} stroke="#374151" strokeWidth="1" />
              <line x1={cx} y1={cy} x2={axes[4].x} y2={axes[4].y} stroke="#374151" strokeWidth="1" />

              {/* Data polygon */}
              <path d={dataPath} fill="rgba(59, 130, 246, 0.4)" stroke="#3B82F6" strokeWidth="3" />

              {/* Score points */}
              <circle cx={scorePts[0].x} cy={scorePts[0].y} r="8" fill={colors[0]} />
              <circle cx={scorePts[1].x} cy={scorePts[1].y} r="8" fill={colors[1]} />
              <circle cx={scorePts[2].x} cy={scorePts[2].y} r="8" fill={colors[2]} />
              <circle cx={scorePts[3].x} cy={scorePts[3].y} r="8" fill={colors[3]} />
              <circle cx={scorePts[4].x} cy={scorePts[4].y} r="8" fill={colors[4]} />
            </svg>

            {/* Labels */}
            <div style={{ display: "flex", position: "absolute", top: labelPts[0].y - 45, left: labelPts[0].x - 30, flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: "18px", fontWeight: "bold", color: colors[0] }}>{Math.round(scoreArr[0])}</span>
              <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{labels[0]}</span>
            </div>
            <div style={{ display: "flex", position: "absolute", top: labelPts[1].y - 10, left: labelPts[1].x + 5, flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: "18px", fontWeight: "bold", color: colors[1] }}>{Math.round(scoreArr[1])}</span>
              <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{labels[1]}</span>
            </div>
            <div style={{ display: "flex", position: "absolute", top: labelPts[2].y + 5, left: labelPts[2].x - 15, flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: "18px", fontWeight: "bold", color: colors[2] }}>{Math.round(scoreArr[2])}</span>
              <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{labels[2]}</span>
            </div>
            <div style={{ display: "flex", position: "absolute", top: labelPts[3].y + 5, left: labelPts[3].x - 45, flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: "18px", fontWeight: "bold", color: colors[3] }}>{Math.round(scoreArr[3])}</span>
              <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{labels[3]}</span>
            </div>
            <div style={{ display: "flex", position: "absolute", top: labelPts[4].y - 10, left: labelPts[4].x - 60, flexDirection: "column", alignItems: "center" }}>
              <span style={{ fontSize: "18px", fontWeight: "bold", color: colors[4] }}>{Math.round(scoreArr[4])}</span>
              <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{labels[4]}</span>
            </div>
          </div>
        </div>

        {/* Right - Info */}
        <div style={{ display: "flex", flexDirection: "column", flex: "1", paddingLeft: "40px", justifyContent: "center" }}>
          <span style={{ fontSize: "52px", fontWeight: "bold", color: "white" }}>@{username}</span>
          <span style={{ fontSize: "22px", color: "#9CA3AF", marginTop: "8px" }}>X Score Optimizer</span>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "32px" }}>
            <div style={{ display: "flex", alignItems: "center", backgroundColor: "#1F2937", borderRadius: "10px", padding: "10px 14px" }}>
              <span style={{ fontSize: "24px", fontWeight: "bold", color: colors[0], marginRight: "8px" }}>{Math.round(scoreArr[0])}</span>
              <span style={{ fontSize: "14px", color: "#9CA3AF" }}>{labels[0]}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", backgroundColor: "#1F2937", borderRadius: "10px", padding: "10px 14px" }}>
              <span style={{ fontSize: "24px", fontWeight: "bold", color: colors[1], marginRight: "8px" }}>{Math.round(scoreArr[1])}</span>
              <span style={{ fontSize: "14px", color: "#9CA3AF" }}>{labels[1]}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", backgroundColor: "#1F2937", borderRadius: "10px", padding: "10px 14px" }}>
              <span style={{ fontSize: "24px", fontWeight: "bold", color: colors[2], marginRight: "8px" }}>{Math.round(scoreArr[2])}</span>
              <span style={{ fontSize: "14px", color: "#9CA3AF" }}>{labels[2]}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", backgroundColor: "#1F2937", borderRadius: "10px", padding: "10px 14px" }}>
              <span style={{ fontSize: "24px", fontWeight: "bold", color: colors[3], marginRight: "8px" }}>{Math.round(scoreArr[3])}</span>
              <span style={{ fontSize: "14px", color: "#9CA3AF" }}>{labels[3]}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", backgroundColor: "#1F2937", borderRadius: "10px", padding: "10px 14px" }}>
              <span style={{ fontSize: "24px", fontWeight: "bold", color: colors[4], marginRight: "8px" }}>{Math.round(scoreArr[4])}</span>
              <span style={{ fontSize: "14px", color: "#9CA3AF" }}>{labels[4]}</span>
            </div>
          </div>

          <span style={{ fontSize: "16px", color: "#6B7280", marginTop: "auto" }}>xeo.selanetwork.io</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
