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

  const scoreArr = [scores.reach, scores.engagement, scores.virality, scores.quality, scores.longevity];
  const labels = ["Reach", "Engage", "Viral", "Quality", "Long"];
  const colors = ["#3B82F6", "#22C55E", "#A855F7", "#EAB308", "#F97316"];

  const avgScore = Math.round(scoreArr.reduce((a, b) => a + b, 0) / 5);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#111827",
          padding: "50px 60px",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Username */}
        <span style={{ fontSize: "64px", fontWeight: "bold", color: "white" }}>
          @{username}
        </span>

        {/* Subtitle */}
        <span style={{ fontSize: "24px", color: "#9CA3AF", marginTop: "8px" }}>
          X Profile Analysis
        </span>

        {/* Average Score */}
        <div style={{ display: "flex", alignItems: "baseline", marginTop: "40px" }}>
          <span style={{ fontSize: "120px", fontWeight: "bold", color: "#3B82F6" }}>
            {avgScore}
          </span>
          <span style={{ fontSize: "32px", color: "#6B7280", marginLeft: "8px" }}>
            / 100
          </span>
        </div>

        {/* Score Pills */}
        <div style={{ display: "flex", gap: "16px", marginTop: "40px" }}>
          {scoreArr.map((score, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                backgroundColor: "#1F2937",
                borderRadius: "16px",
                padding: "16px 24px",
                minWidth: "100px",
              }}
            >
              <span style={{ fontSize: "36px", fontWeight: "bold", color: colors[i] }}>
                {Math.round(score)}
              </span>
              <span style={{ fontSize: "14px", color: "#9CA3AF", marginTop: "4px" }}>
                {labels[i]}
              </span>
            </div>
          ))}
        </div>

        {/* Footer */}
        <span style={{ fontSize: "18px", color: "#4B5563", marginTop: "auto" }}>
          xeo.selanetwork.io
        </span>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
