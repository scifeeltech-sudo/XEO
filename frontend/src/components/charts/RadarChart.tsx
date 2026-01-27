"use client";

import { memo, useMemo } from "react";
import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { PentagonScores } from "@/types/api";

interface RadarChartProps {
  scores: PentagonScores;
  size?: number;
}

const LABELS: Record<keyof PentagonScores, string> = {
  reach: "Reach",
  engagement: "Engagement",
  virality: "Virality",
  quality: "Quality",
  longevity: "Longevity",
};

const COLORS: Record<string, string> = {
  Engagement: "#4ade80", // green-400
  Reach: "#60a5fa",      // blue-400
  Virality: "#c084fc",   // purple-400
  Quality: "#facc15",    // yellow-400
  Longevity: "#fb923c",  // orange-400
};

// Custom tick component for colored labels
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTick = (props: any) => {
  const { payload, x, y, textAnchor } = props;
  const color = COLORS[payload?.value] || "#6b7280";
  return (
    <text
      x={x}
      y={y}
      textAnchor={textAnchor}
      fill={color}
      fontSize={12}
      fontWeight={500}
    >
      {payload?.value}
    </text>
  );
};

// Memoized tooltip formatter to prevent recreation on each render
const tooltipFormatter = (value: unknown) => [
  `${typeof value === "number" ? value.toFixed(1) : value}`,
  "Score",
];

function RadarChartComponent({ scores, size = 300 }: RadarChartProps) {
  // Memoize data transformation to prevent recalculation on parent re-renders
  const data = useMemo(
    () =>
      Object.entries(scores).map(([key, value]) => ({
        subject: LABELS[key as keyof PentagonScores],
        value: value,
        fullMark: 100,
      })),
    [scores]
  );

  return (
    <ResponsiveContainer width="100%" height={size}>
      <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={CustomTick}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "#9ca3af", fontSize: 10 }}
        />
        <Radar
          name="Score"
          dataKey="value"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip formatter={tooltipFormatter} />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}

// Memoize the entire component to prevent re-renders when parent updates
// Only re-renders when scores or size actually change
export const RadarChart = memo(RadarChartComponent);
