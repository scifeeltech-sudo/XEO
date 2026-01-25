"use client";

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

export function RadarChart({ scores, size = 300 }: RadarChartProps) {
  const data = Object.entries(scores).map(([key, value]) => ({
    subject: LABELS[key as keyof PentagonScores],
    value: value,
    fullMark: 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={size}>
      <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: "#6b7280", fontSize: 12 }}
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
        <Tooltip
          formatter={(value) => [
            `${typeof value === "number" ? value.toFixed(1) : value}`,
            "Score",
          ]}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
