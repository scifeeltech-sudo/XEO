"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { PostAnalysis, ApplyTipsResponse, PolishType, TargetPostContext, PersonalizedPostResponse } from "@/types/api";
import { RadarChart } from "@/components/charts/RadarChart";

interface PostEditorProps {
  username: string;
}

// Simple language detection based on character ranges
function detectLanguage(text: string): string {
  // Korean
  if (/[\uac00-\ud7af]/.test(text)) return "ko";
  // Japanese
  if (/[\u3040-\u309f\u30a0-\u30ff]/.test(text)) return "ja";
  // Chinese
  if (/[\u4e00-\u9fff]/.test(text)) return "zh";
  // Default to English
  return "en";
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
  const [polishing, setPolishing] = useState<PolishType | null>(null);
  const [detectedLanguage, setDetectedLanguage] = useState<string>("en");
  const [targetLanguage, setTargetLanguage] = useState<"ko" | "en" | "ja" | "zh">("en");

  // Target post preview state
  const [targetPostContext, setTargetPostContext] = useState<TargetPostContext | null>(null);
  const [fetchingTarget, setFetchingTarget] = useState(false);
  const [targetFetchError, setTargetFetchError] = useState<string | null>(null);

  // Personalized post state
  const [personalizedPost, setPersonalizedPost] = useState<PersonalizedPostResponse | null>(null);
  const [fetchingPersonalized, setFetchingPersonalized] = useState(false);

  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const targetUrlDebounceRef = useRef<NodeJS.Timeout | null>(null);

  const analyzePost = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        setAnalysis(null);
        return;
      }

      setLoading(true);
      try {
        // For reply/quote mode, pass target_language to ensure tips are in correct language
        const langToUse = postType !== "original" ? targetLanguage : undefined;

        const result = await api.analyzePost({
          username,
          content: text,
          post_type: postType,
          target_post_url: targetUrl || undefined,
          media_type: mediaType,
          target_language: langToUse,
        });
        setAnalysis(result);
        // Reset tip selection when analysis changes
        setSelectedTips([]);
        setSuggestion(null);
        // Update detected language for apply-tips
        if (result.context?.target_post_content) {
          // Reply/Quote: use target post language from context
          const lang = detectLanguage(result.context.target_post_content);
          setDetectedLanguage(lang);
        } else if (postType !== "original") {
          // Reply/Quote without context: use selected target language
          setDetectedLanguage(targetLanguage);
        } else {
          // Original: use user content language
          const lang = detectLanguage(text);
          setDetectedLanguage(lang);
        }
      } catch (error) {
        console.error("Analysis failed:", error);
      } finally {
        setLoading(false);
      }
    },
    [username, postType, targetUrl, mediaType, targetLanguage]
  );

  // Auto-analyze only for original posts, not for reply/quote
  useEffect(() => {
    if (postType !== "original") {
      // For reply/quote, clear analysis when content changes
      // User must click "Analyze" button manually
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      analyzePost(content);
    }, 300);  // Reduced from 500ms for faster feedback

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [content, analyzePost, postType]);

  // Clear analysis when switching post type
  useEffect(() => {
    setAnalysis(null);
    setSelectedTips([]);
    setSuggestion(null);
    setTargetPostContext(null);
    setTargetFetchError(null);
  }, [postType]);

  // Fetch target post context when URL changes
  useEffect(() => {
    if (postType === "original" || !targetUrl) {
      setTargetPostContext(null);
      setTargetFetchError(null);
      return;
    }

    // Validate URL format
    if (!targetUrl.match(/^https?:\/\/(x\.com|twitter\.com)\/\w+\/status\/\d+/)) {
      setTargetPostContext(null);
      setTargetFetchError(null);
      return;
    }

    if (targetUrlDebounceRef.current) {
      clearTimeout(targetUrlDebounceRef.current);
    }

    targetUrlDebounceRef.current = setTimeout(async () => {
      setFetchingTarget(true);
      setTargetFetchError(null);
      try {
        const context = await api.getPostContext(targetUrl);
        setTargetPostContext(context);
        // Auto-detect language from target post
        const lang = detectLanguage(context.content.text);
        setTargetLanguage(lang as "ko" | "en" | "ja" | "zh");
      } catch (error) {
        console.error("Failed to fetch target post:", error);
        setTargetPostContext(null);
        setTargetFetchError("Could not fetch target post. Please select language manually.");
      } finally {
        setFetchingTarget(false);
      }
    }, 400);  // Reduced from 800ms for faster response

    return () => {
      if (targetUrlDebounceRef.current) {
        clearTimeout(targetUrlDebounceRef.current);
      }
    };
  }, [targetUrl, postType]);

  // Fetch personalized post when target context is loaded
  useEffect(() => {
    if (!targetPostContext || postType === "original") {
      setPersonalizedPost(null);
      return;
    }

    const fetchPersonalized = async () => {
      setFetchingPersonalized(true);
      try {
        const result = await api.generatePersonalizedPost({
          username,
          target_post_content: targetPostContext.content.text,
          target_author: targetPostContext.author.username,
          post_type: postType as "reply" | "quote",
          language: targetLanguage,
        });
        setPersonalizedPost(result);
      } catch (error) {
        console.error("Failed to generate personalized post:", error);
        setPersonalizedPost(null);
      } finally {
        setFetchingPersonalized(false);
      }
    };

    fetchPersonalized();
  }, [targetPostContext, postType, username, targetLanguage]);

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
        language: detectedLanguage,
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
    alert("Copied to clipboard!");
  };

  const handleUseSuggestion = () => {
    if (suggestion) {
      setContent(suggestion.suggested_content);
      setSuggestion(null);
      setSelectedTips([]);
    }
  };

  const handlePolishSuggestion = async (type: PolishType) => {
    if (!suggestion || polishing) return;

    setPolishing(type);
    try {
      const result = await api.polishPost({
        content: suggestion.suggested_content,
        polish_type: type,
        language: detectedLanguage,
        target_post_content: analysis?.context?.target_post_content,
      });
      setSuggestion({
        ...suggestion,
        suggested_content: result.polished_content,
      });
    } catch (error) {
      console.error("Failed to polish:", error);
    } finally {
      setPolishing(null);
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
              {type === "original" ? "Original" : type === "reply" ? "Reply" : "Quote"}
            </button>
          ))}
        </div>

        {/* Target URL (for reply/quote) */}
        {postType !== "original" && (
          <div className="space-y-3">
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="Target post URL (https://x.com/...)"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />

            {/* Target Post Preview */}
            {fetchingTarget && (
              <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                <div className="flex items-center gap-2 text-gray-400">
                  <span className="animate-spin">⏳</span>
                  <span>Fetching target post...</span>
                </div>
              </div>
            )}

            {targetPostContext && !fetchingTarget && (
              <div className="p-4 bg-gray-800 border border-blue-500/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-white">
                        @{targetPostContext.author.username}
                      </span>
                      {targetPostContext.author.verified && (
                        <span className="text-blue-400">✓</span>
                      )}
                      <span className="text-gray-500 text-sm">
                        • {targetPostContext.author.followers_count.toLocaleString()} followers
                      </span>
                    </div>
                    <p className="text-gray-300 mb-3">
                      {targetPostContext.content.text.length > 200
                        ? targetPostContext.content.text.slice(0, 200) + "..."
                        : targetPostContext.content.text}
                    </p>
                    <div className="flex gap-4 text-sm text-gray-500">
                      <span>❤️ {targetPostContext.metrics.likes.toLocaleString()}</span>
                      <span>🔁 {targetPostContext.metrics.reposts.toLocaleString()}</span>
                      <span>💬 {targetPostContext.metrics.replies.toLocaleString()}</span>
                      <span>👁 {targetPostContext.metrics.views.toLocaleString()}</span>
                    </div>
                    {/* Opportunity Score */}
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 text-sm">Opportunity Score:</span>
                        <span className={`font-bold ${
                          targetPostContext.opportunity_score.overall >= 70 ? "text-green-400" :
                          targetPostContext.opportunity_score.overall >= 40 ? "text-yellow-400" :
                          "text-red-400"
                        }`}>
                          {targetPostContext.opportunity_score.overall}/100
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          targetPostContext.analysis.freshness === "very_fresh" ? "bg-green-900/50 text-green-400" :
                          targetPostContext.analysis.freshness === "fresh" ? "bg-blue-900/50 text-blue-400" :
                          "bg-gray-700 text-gray-400"
                        }`}>
                          {targetPostContext.analysis.freshness === "very_fresh" ? "🔥 Very Fresh" :
                           targetPostContext.analysis.freshness === "fresh" ? "✨ Fresh" :
                           targetPostContext.analysis.freshness === "moderate" ? "Moderate" : "Old"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Error or Language Selector */}
            {targetFetchError && !fetchingTarget && (
              <div className="p-3 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
                <p className="text-yellow-400 text-sm mb-2">⚠️ {targetFetchError}</p>
              </div>
            )}

            {/* Target Language Selector - Always show for manual override */}
            <div className="flex gap-2 items-center">
              <span className="text-gray-400 text-sm">
                {targetPostContext ? "Detected language:" : "Target post language:"}
              </span>
              {(["en", "ko", "ja", "zh"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setTargetLanguage(lang)}
                  className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                    targetLanguage === lang
                      ? "bg-blue-600 text-white"
                      : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  {lang === "en" ? "English" : lang === "ko" ? "한국어" : lang === "ja" ? "日本語" : "中文"}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Content Editor */}
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post content..."
            className="w-full h-48 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <div className="absolute bottom-3 right-3 text-gray-500 text-sm">
            {content.length}/280
          </div>
        </div>

        {/* Analyze Button */}
        <button
          onClick={() => analyzePost(content)}
          disabled={!content.trim() || loading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <span>🔍</span>
          <span>{loading ? "Analyzing..." : "Analyze"}</span>
        </button>

        {/* Media Type */}
        <div className="flex gap-2 items-center">
          <span className="text-gray-400">Media:</span>
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
              {type ?? "None"}
            </button>
          ))}
        </div>

        {/* Copy Button */}
        <button
          onClick={() => handleCopy(content)}
          disabled={!content}
          className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          Copy to Clipboard
        </button>

        {/* Suggestion Panels Container */}
        <div className="grid grid-cols-1 gap-4">
          {/* Post Suggestion */}
          {suggestion && (
            <div className="bg-gray-800 rounded-xl p-4 border-2 border-blue-500">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                ✨ Post Suggestion
              </h3>
              <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                <p className="text-white whitespace-pre-wrap">
                  {suggestion.suggested_content}
                </p>
                <div className="text-xs text-gray-500 mt-2">
                  {suggestion.suggested_content.length}/280
                </div>
              </div>

              {/* Polish Buttons inside suggestion */}
              <div className="mb-4">
                <span className="text-gray-400 text-sm block mb-2">
                  Polish with Claude AI:
                </span>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handlePolishSuggestion("grammar")}
                    disabled={polishing !== null}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      polishing === "grammar"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                    } disabled:opacity-50`}
                  >
                    ✍️ Keep Tone {polishing === "grammar" && "⏳"}
                  </button>
                  <button
                    onClick={() => handlePolishSuggestion("twitter")}
                    disabled={polishing !== null}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      polishing === "twitter"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                    } disabled:opacity-50`}
                  >
                    🐦 Twitter Style {polishing === "twitter" && "⏳"}
                  </button>
                  <button
                    onClick={() => handlePolishSuggestion("280char")}
                    disabled={polishing !== null}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      polishing === "280char"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                    } disabled:opacity-50`}
                  >
                    📏 Fit 280 chars {polishing === "280char" && "⏳"}
                  </button>
                </div>
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
                  Expected improvement:{" "}
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
                  Use This Content
                </button>
                <button
                  onClick={() => handleCopy(suggestion.suggested_content)}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
                >
                  📋 Copy
                </button>
              </div>
            </div>
          )}

          {/* AI Personalized Post (for reply/quote only) */}
          {postType !== "original" && (fetchingPersonalized || personalizedPost) && (
            <div className="bg-gray-800 rounded-xl p-4 border-2 border-purple-500">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                🤖 AI Personalized Post
                <span className="text-sm font-normal text-purple-400">
                  (Auto-generated in {username}&apos;s style)
                </span>
              </h3>

              {fetchingPersonalized ? (
                <div className="flex items-center justify-center py-8 text-gray-400">
                  <span className="animate-spin mr-2">⏳</span>
                  AI is analyzing {username}&apos;s style and generating post...
                </div>
              ) : personalizedPost && (
                <>
                  {/* Generated Content */}
                  <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                    <p className="text-white whitespace-pre-wrap">
                      {personalizedPost.generated_content}
                    </p>
                    <div className="text-xs text-gray-500 mt-2">
                      {personalizedPost.generated_content.length}/280
                    </div>
                  </div>

                  {/* Style Analysis */}
                  <div className="mb-4 p-3 bg-purple-900/20 rounded-lg border border-purple-700/30">
                    <div className="text-sm text-purple-300 mb-2 font-medium">
                      📊 Style Analysis (Confidence: {Math.round(personalizedPost.confidence * 100)}%)
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-400">Tone:</span>
                        <span className="text-gray-300 ml-1">{personalizedPost.style_analysis.tone}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Emoji:</span>
                        <span className="text-gray-300 ml-1">{personalizedPost.style_analysis.emoji_style}</span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-400">Interests:</span>
                        <span className="text-gray-300 ml-1">
                          {personalizedPost.style_analysis.topics.slice(0, 3).join(", ")}
                        </span>
                      </div>
                    </div>
                    {personalizedPost.reasoning && (
                      <div className="mt-2 pt-2 border-t border-purple-700/30 text-xs text-gray-400">
                        {personalizedPost.reasoning}
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setContent(personalizedPost.generated_content);
                        setPersonalizedPost(null);
                      }}
                      className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                    >
                      Use This Content
                    </button>
                    <button
                      onClick={() => handleCopy(personalizedPost.generated_content)}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
                    >
                      📋 Copy
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Analysis Results */}
      <div className="space-y-6">
        {loading && (
          <div className="text-center py-8 text-gray-400">Analyzing...</div>
        )}

        {analysis && !loading && (
          <>
            {/* Radar Chart */}
            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-4">
                Predicted Score
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
                  💡 Quick Tips{" "}
                  <span className="text-sm font-normal text-gray-400">
                    (Select up to 3)
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
                    {applyingTips ? "Applying..." : `✨ Apply ${selectedTips.length} Tips`}
                  </button>
                )}
              </div>
            )}

            {/* Context (for reply/quote) */}
            {analysis.context && (
              <div className="bg-gray-800 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Context Analysis
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-gray-700/50 rounded-lg">
                    <div className="text-sm text-gray-400">Target Post</div>
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

        {!analysis && !loading && (
          <div className="text-center py-12 text-gray-500">
            {postType === "original" ? (
              "Enter your post content to see real-time score analysis"
            ) : (
              <>
                Enter the target post URL and your content, then
                <br />
                click <span className="text-blue-400">[🔍 Analyze]</span> button
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
