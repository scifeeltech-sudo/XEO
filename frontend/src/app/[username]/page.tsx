"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { ProfileAnalysis } from "@/types/api";
import { RadarChart } from "@/components/charts/RadarChart";

export default function ProfilePage() {
  const params = useParams();
  const username = params.username as string;
  const [analysis, setAnalysis] = useState<ProfileAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalysis() {
      try {
        const result = await api.analyzeProfile(username);
        setAnalysis(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to analyze profile");
      } finally {
        setLoading(false);
      }
    }
    fetchAnalysis();
  }, [username]);

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-gray-400 text-lg">Analyzing @{username}&apos;s profile...</p>
            <p className="text-gray-500 text-sm mt-2">Please wait</p>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto text-center py-20">
          <h1 className="text-2xl text-red-500 mb-4">Analysis Failed</h1>
          <p className="text-gray-400">{error}</p>
          <Link
            href="/"
            className="text-blue-500 hover:underline mt-4 inline-block"
          >
            Go Back
          </Link>
        </div>
      </main>
    );
  }

  if (!analysis) return null;

  return (
    <main className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">@{username}</h1>
            <p className="text-gray-400">Profile Analysis Results</p>
          </div>
          <Link
            href={`/${username}/compose`}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Compose Post
          </Link>
        </div>

        {/* Score Chart */}
        <div className="bg-gray-800 rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Score Chart</h2>
          <div className="flex justify-center">
            <RadarChart scores={analysis.scores} size={350} />
          </div>
          <div className="grid grid-cols-5 gap-4 mt-6">
            {Object.entries(analysis.scores).map(([key, value]) => (
              <div key={key} className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {value.toFixed(0)}
                </div>
                <div className="text-sm text-gray-400 capitalize">{key}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Insights */}
        {analysis.insights.length > 0 && (
          <div className="bg-gray-800 rounded-2xl p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Insights</h2>
            <div className="space-y-4">
              {analysis.insights.map((insight, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-lg border-l-4 ${
                    insight.priority === "high"
                      ? "bg-red-900/20 border-red-500"
                      : insight.priority === "medium"
                      ? "bg-yellow-900/20 border-yellow-500"
                      : "bg-green-900/20 border-green-500"
                  }`}
                >
                  <div className="text-sm text-gray-400 mb-1">
                    {insight.category}
                  </div>
                  <div className="text-white">{insight.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {analysis.recommendations.length > 0 && (
          <div className="bg-gray-800 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Recommendations</h2>
            <div className="space-y-4">
              {analysis.recommendations.map((rec, i) => (
                <div key={i} className="p-4 bg-gray-700/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-blue-400 font-medium">
                      {rec.action}
                    </span>
                    <span className="text-green-400 text-sm">
                      {rec.expected_impact}
                    </span>
                  </div>
                  <p className="text-gray-300">{rec.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
