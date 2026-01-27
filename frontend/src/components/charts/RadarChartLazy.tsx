"use client";

import { useState, useEffect, memo } from "react";
import { PentagonScores } from "@/types/api";

interface RadarChartProps {
  scores: PentagonScores;
  size?: number;
}

// Loading skeleton that matches chart dimensions to prevent layout shift
function RadarChartSkeleton({ size = 300 }: { size?: number }) {
  return (
    <div
      className="flex items-center justify-center animate-pulse"
      style={{ width: "100%", height: size }}
    >
      <div
        className="rounded-full bg-gray-700/50"
        style={{ width: size * 0.7, height: size * 0.7 }}
      />
    </div>
  );
}

// Lazy-loaded RadarChart with proper size handling
function RadarChartLazyComponent({ scores, size = 300 }: RadarChartProps) {
  const [ChartComponent, setChartComponent] = useState<React.ComponentType<RadarChartProps> | null>(null);

  useEffect(() => {
    // Dynamic import on client side only
    import("./RadarChart").then((mod) => {
      setChartComponent(() => mod.RadarChart);
    });
  }, []);

  if (!ChartComponent) {
    return <RadarChartSkeleton size={size} />;
  }

  return <ChartComponent scores={scores} size={size} />;
}

// Memoize to prevent unnecessary re-renders
export const RadarChartLazy = memo(RadarChartLazyComponent);
