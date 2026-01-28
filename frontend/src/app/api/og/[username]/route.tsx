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
function getPointOnPentagon(
  centerX: number,
  centerY: number,
  radius: number,
  index: number,
  total: number = 5
): { x: number; y: number } {
  // Start from top (-90 degrees) and go clockwise
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle),
  };
}

function createPentagonPath(
  centerX: number,
  centerY: number,
  scores: number[],
  maxRadius: number
): string {
  const points = scores.map((score, i) => {
    const radius = (score / 100) * maxRadius;
    return getPointOnPentagon(centerX, centerY, radius, i);
  });
  return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
}

function createGridPath(
  centerX: number,
  centerY: number,
  radius: number
): string {
  const points = [0, 1, 2, 3, 4].map((i) =>
    getPointOnPentagon(centerX, centerY, radius, i)
  );
  return points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
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

  // Pentagon chart dimensions
  const chartSize = 280;
  const chartCenter = chartSize / 2;
  const maxRadius = 120;

  // Score values in order: Reach, Engagement, Virality, Quality, Longevity
  const scoreValues = [
    scores.reach,
    scores.engagement,
    scores.virality,
    scores.quality,
    scores.longevity,
  ];

  // Labels with positions
  const labels = [
    { name: "Reach", color: "#3B82F6", score: scores.reach },
    { name: "Engage", color: "#22C55E", score: scores.engagement },
    { name: "Viral", color: "#A855F7", score: scores.virality },
    { name: "Quality", color: "#EAB308", score: scores.quality },
    { name: "Long", color: "#F97316", score: scores.longevity },
  ];

  // Calculate label positions
  const labelPositions = labels.map((_, i) => {
    const point = getPointOnPentagon(chartCenter, chartCenter, maxRadius + 35, i);
    return point;
  });

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#111827",
          padding: 48,
        }}
      >
        {/* Left side - Pentagon Chart */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: 400,
          }}
        >
          <svg
            width={chartSize}
            height={chartSize}
            viewBox={`0 0 ${chartSize} ${chartSize}`}
            style={{ overflow: "visible" }}
          >
            {/* Grid lines */}
            {[0.2, 0.4, 0.6, 0.8, 1].map((scale) => (
              <path
                key={scale}
                d={createGridPath(chartCenter, chartCenter, maxRadius * scale)}
                fill="none"
                stroke="#374151"
                strokeWidth="1"
              />
            ))}

            {/* Axis lines */}
            {[0, 1, 2, 3, 4].map((i) => {
              const point = getPointOnPentagon(chartCenter, chartCenter, maxRadius, i);
              return (
                <line
                  key={i}
                  x1={chartCenter}
                  y1={chartCenter}
                  x2={point.x}
                  y2={point.y}
                  stroke="#374151"
                  strokeWidth="1"
                />
              );
            })}

            {/* Score polygon */}
            <path
              d={createPentagonPath(chartCenter, chartCenter, scoreValues, maxRadius)}
              fill="rgba(59, 130, 246, 0.3)"
              stroke="#3B82F6"
              strokeWidth="3"
            />

            {/* Score points */}
            {scoreValues.map((score, i) => {
              const radius = (score / 100) * maxRadius;
              const point = getPointOnPentagon(chartCenter, chartCenter, radius, i);
              return (
                <circle
                  key={i}
                  cx={point.x}
                  cy={point.y}
                  r="6"
                  fill={labels[i].color}
                />
              );
            })}
          </svg>

          {/* Labels around the chart */}
          <div
            style={{
              display: "flex",
              position: "relative",
              width: chartSize + 100,
              height: chartSize + 80,
              marginTop: -chartSize - 20,
            }}
          >
            {labels.map((label, i) => {
              const pos = labelPositions[i];
              return (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: pos.x + 50 - 40,
                    top: pos.y + 40 - 12,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: 14, color: label.color, fontWeight: 600 }}>
                    {Math.round(label.score)}
                  </span>
                  <span style={{ fontSize: 11, color: "#9CA3AF" }}>
                    {label.name}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right side - Info */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            paddingLeft: 32,
            justifyContent: "center",
          }}
        >
          <span style={{ fontSize: 56, fontWeight: 700, color: "white" }}>
            @{username}
          </span>
          <span style={{ fontSize: 24, color: "#9CA3AF", marginTop: 8, marginBottom: 24 }}>
            X Score Optimizer
          </span>

          {/* Score summary boxes */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
            {labels.map((label) => (
              <div
                key={label.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  backgroundColor: "#1F2937",
                  borderRadius: 12,
                  padding: "12px 16px",
                  gap: 8,
                }}
              >
                <span style={{ fontSize: 28, fontWeight: 700, color: label.color }}>
                  {Math.round(label.score)}
                </span>
                <span style={{ fontSize: 14, color: "#9CA3AF" }}>{label.name}</span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", marginTop: "auto" }}>
            <span style={{ fontSize: 16, color: "#6B7280" }}>xeo.selanetwork.io</span>
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
