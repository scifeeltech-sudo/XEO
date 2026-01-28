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

export async function GET(
  request: Request,
  { params }: { params: Promise<{ username: string }> }
) {
  const { username } = await params;

  let analysis: ProfileAnalysis | null = null;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/profile/${username}/analyze`,
      { signal: controller.signal }
    );
    clearTimeout(timeoutId);

    if (response.ok) {
      analysis = await response.json();
    }
  } catch {
    // Use fallback values
  }

  const scores = analysis?.scores || {
    reach: 0,
    engagement: 0,
    virality: 0,
    quality: 0,
    longevity: 0,
  };

  const summary = analysis?.summary || "Analyze your X profile to see insights and optimization tips.";
  const truncatedSummary = summary.length > 120 ? summary.slice(0, 117) + "..." : summary;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#111827",
          padding: 48,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", marginBottom: 32 }}>
          <span style={{ fontSize: 56, fontWeight: 700, color: "white" }}>
            @{username}
          </span>
          <span style={{ fontSize: 24, color: "#9CA3AF", marginTop: 8 }}>
            X Score Optimizer - Profile Analysis
          </span>
        </div>

        <div style={{ display: "flex", gap: 16, marginBottom: 32 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", backgroundColor: "#1F2937", borderRadius: 16, padding: "20px 28px", width: 180 }}>
            <span style={{ fontSize: 48, fontWeight: 700, color: "#3B82F6" }}>{Math.round(scores.reach)}</span>
            <span style={{ fontSize: 16, color: "#9CA3AF", marginTop: 4 }}>REACH</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", backgroundColor: "#1F2937", borderRadius: 16, padding: "20px 28px", width: 180 }}>
            <span style={{ fontSize: 48, fontWeight: 700, color: "#22C55E" }}>{Math.round(scores.engagement)}</span>
            <span style={{ fontSize: 16, color: "#9CA3AF", marginTop: 4 }}>ENGAGE</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", backgroundColor: "#1F2937", borderRadius: 16, padding: "20px 28px", width: 180 }}>
            <span style={{ fontSize: 48, fontWeight: 700, color: "#A855F7" }}>{Math.round(scores.virality)}</span>
            <span style={{ fontSize: 16, color: "#9CA3AF", marginTop: 4 }}>VIRAL</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", backgroundColor: "#1F2937", borderRadius: 16, padding: "20px 28px", width: 180 }}>
            <span style={{ fontSize: 48, fontWeight: 700, color: "#EAB308" }}>{Math.round(scores.quality)}</span>
            <span style={{ fontSize: 16, color: "#9CA3AF", marginTop: 4 }}>QUALITY</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", backgroundColor: "#1F2937", borderRadius: 16, padding: "20px 28px", width: 180 }}>
            <span style={{ fontSize: 48, fontWeight: 700, color: "#F97316" }}>{Math.round(scores.longevity)}</span>
            <span style={{ fontSize: 16, color: "#9CA3AF", marginTop: 4 }}>LONG</span>
          </div>
        </div>

        <div style={{ display: "flex", backgroundColor: "#1F2937", borderRadius: 16, padding: 24, flex: 1 }}>
          <span style={{ fontSize: 22, color: "#D1D5DB" }}>
            {truncatedSummary}
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 20 }}>
          <span style={{ fontSize: 18, color: "#6B7280" }}>xeo.app</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
