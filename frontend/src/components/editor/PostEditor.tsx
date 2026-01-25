"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { PostAnalysis, ApplyTipsResponse } from "@/types/api";
import { RadarChart } from "@/components/charts/RadarChart";

interface PostEditorProps {
  username: string;
}

export function PostEditor({ username }: PostEditorProps) {
  const [content, setContent] = useState("");
  const [postType, setPostType] = useState<"original" | "reply" | "quote">(
    "original"
  );
  const [targetUrl, setTargetUrl] = useState("");
  const [mediaType, setMediaType] = useState<
    "image" | "video" | "gif" | undefined
  >();
  const [analysis, setAnalysis] = useState<PostAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  // Tip selection state
  const [selectedTips, setSelectedTips] = useState<string[]>([]);
  const [suggestion, setSuggestion] = useState<ApplyTipsResponse | null>(null);
  const [applyingTips, setApplyingTips] = useState(false);

  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const analyzePost = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        setAnalysis(null);
        return;
      }

      setLoading(true);
      try {
        const result = await api.analyzePost({
          username,
          content: text,
          post_type: postType,
          target_post_url: targetUrl || undefined,
          media_type: mediaType,
        });
        setAnalysis(result);
        // Reset tip selection when analysis changes
        setSelectedTips([]);
        setSuggestion(null);
      } catch (error) {
        console.error("Analysis failed:", error);
      } finally {
        setLoading(false);
      }
    },
    [username, postType, targetUrl, mediaType]
  );

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      analyzePost(content);
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [content, analyzePost]);

  const handleTipToggle = (tipId: string) => {
    setSelectedTips((prev) => {
      if (prev.includes(tipId)) {
        return prev.filter((id) => id !== tipId);
      }
      // Max 3 tips
      if (prev.length >= 3) {
        return prev;
      }
      return [...prev, tipId];
    });
  };

  const handleApplyTips = async () => {
    if (selectedTips.length === 0) return;

    setApplyingTips(true);
    try {
      const result = await api.applyTips({
        username,
        original_content: content,
        selected_tips: selectedTips,
      });
      setSuggestion(result);
    } catch (error) {
      console.error("Failed to apply tips:", error);
    } finally {
      setApplyingTips(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    alert("클립보드에 복사되었습니다!");
  };

  const handleUseSuggestion = () => {
    if (suggestion) {
      setContent(suggestion.suggested_content);
      setSuggestion(null);
      setSelectedTips([]);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Editor */}
      <div className="space-y-6">
        {/* Post Type Selector */}
        <div className="flex gap-2">
          {(["original", "reply", "quote"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setPostType(type)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                postType === type
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {type === "original" ? "원본" : type === "reply" ? "답글" : "인용"}
            </button>
          ))}
        </div>

        {/* Target URL (for reply/quote) */}
        {postType !== "original" && (
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="대상 포스트 URL (https://x.com/...)"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        )}

        {/* Content Editor */}
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="포스트 내용을 입력하세요..."
            className="w-full h-48 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <div className="absolute bottom-3 right-3 text-gray-500 text-sm">
            {content.length}/280
          </div>
        </div>

        {/* Media Type */}
        <div className="flex gap-2 items-center">
          <span className="text-gray-400">미디어:</span>
          {[undefined, "image", "video", "gif"].map((type) => (
            <button
              key={type ?? "none"}
              onClick={() =>
                setMediaType(type as "image" | "video" | "gif" | undefined)
              }
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                mediaType === type
                  ? "bg-blue-600 text-white"
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {type ?? "없음"}
            </button>
          ))}
        </div>

        {/* Copy Button */}
        <button
          onClick={() => handleCopy(content)}
          disabled={!content}
          className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          클립보드에 복사
        </button>

        {/* Post Suggestion */}
        {suggestion && (
          <div className="bg-gray-800 rounded-xl p-4 border-2 border-blue-500">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              ✨ 포스팅 제안
            </h3>
            <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
              <p className="text-white whitespace-pre-wrap">
                {suggestion.suggested_content}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {suggestion.applied_tips.map((tip) => (
                <span
                  key={tip.tip_id}
                  className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-sm"
                >
                  {tip.description} ({tip.impact})
                </span>
              ))}
            </div>
            {Object.keys(suggestion.predicted_improvement).length > 0 && (
              <div className="text-sm text-green-400 mb-4">
                예상 개선:{" "}
                {Object.entries(suggestion.predicted_improvement)
                  .map(([k, v]) => `${k} ${v}`)
                  .join(", ")}
              </div>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleUseSuggestion}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                이 내용 사용하기
              </button>
              <button
                onClick={() => handleCopy(suggestion.suggested_content)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                📋 복사
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Results */}
      <div className="space-y-6">
        {loading && (
          <div className="text-center py-8 text-gray-400">분석 중...</div>
        )}

        {analysis && !loading && (
          <>
            {/* Radar Chart */}
            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-4">
                예상 스코어
              </h3>
              <RadarChart scores={analysis.scores} size={280} />
              <div className="text-center mt-2">
                <span className="text-2xl font-bold text-blue-400">
                  {(
                    Object.values(analysis.scores).reduce((a, b) => a + b, 0) /
                    5
                  ).toFixed(0)}
                </span>
                <span className="text-gray-400 ml-2">/ 100</span>
              </div>
            </div>

            {/* Quick Tips with Checkboxes */}
            {analysis.quick_tips.length > 0 && (
              <div className="bg-gray-800 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  💡 빠른 팁{" "}
                  <span className="text-sm font-normal text-gray-400">
                    (최대 3개 선택)
                  </span>
                </h3>
                <ul className="space-y-3">
                  {analysis.quick_tips.map((tip) => (
                    <li key={tip.tip_id} className="flex items-start gap-3">
                      {tip.selectable ? (
                        <input
                          type="checkbox"
                          checked={selectedTips.includes(tip.tip_id)}
                          onChange={() => handleTipToggle(tip.tip_id)}
                          disabled={
                            !selectedTips.includes(tip.tip_id) &&
                            selectedTips.length >= 3
                          }
                          className="mt-1 w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                      ) : (
                        <span className="mt-1 text-gray-500">💡</span>
                      )}
                      <div className="flex-1">
                        <span className="text-gray-300">{tip.description}</span>
                        <span
                          className={`ml-2 text-sm ${
                            tip.target_score === "engagement"
                              ? "text-green-400"
                              : tip.target_score === "reach"
                              ? "text-blue-400"
                              : "text-yellow-400"
                          }`}
                        >
                          {tip.impact} {tip.target_score}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
                {selectedTips.length > 0 && (
                  <button
                    onClick={handleApplyTips}
                    disabled={applyingTips}
                    className="w-full mt-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white font-medium rounded-lg transition-colors"
                  >
                    {applyingTips ? "적용 중..." : `✨ ${selectedTips.length}개 팁 반영하기`}
                  </button>
                )}
              </div>
            )}

            {/* Context (for reply/quote) */}
            {analysis.context && (
              <div className="bg-gray-800 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  컨텍스트 분석
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-gray-700/50 rounded-lg">
                    <div className="text-sm text-gray-400">대상 포스트</div>
                    <div className="text-white">
                      @{analysis.context.target_author}
                    </div>
                    <div className="text-gray-300 text-sm mt-1">
                      {analysis.context.target_post_content.slice(0, 100)}...
                    </div>
                  </div>
                  {Object.entries(analysis.context.context_adjustments).map(
                    ([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-gray-400">{key}</span>
                        <span
                          className={
                            value.startsWith("+")
                              ? "text-green-400"
                              : "text-red-400"
                          }
                        >
                          {value}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {!analysis && !loading && content.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            포스트 내용을 입력하면 실시간으로 스코어가 분석됩니다
          </div>
        )}
      </div>
    </div>
  );
}
