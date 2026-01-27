"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { PostAnalysis, ApplyTipsResponse, PolishType, TargetPostContext, PersonalizedPostResponse, Persona, PersonaType, PentagonScores } from "@/types/api";
// Lazy-loaded RadarChart to reduce initial bundle size (~500KB reduction)
// Fallback: import { RadarChart } from "@/components/charts/RadarChart";
import { RadarChartLazy as RadarChart } from "@/components/charts/RadarChartLazy";

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
  const [analysis, setAnalysis] = useState<PostAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  // Tip selection state
  const [selectedTips, setSelectedTips] = useState<string[]>([]);
  const [suggestion, setSuggestion] = useState<ApplyTipsResponse | null>(null);
  const [applyingTips, setApplyingTips] = useState(false);
  const [polishing, setPolishing] = useState<PolishType | null>(null);
  const [detectedLanguage, setDetectedLanguage] = useState<string>("en");
  const [suggestionLanguage, setSuggestionLanguage] = useState<string>("en"); // Track current suggestion language
  const [targetLanguage, setTargetLanguage] = useState<"ko" | "en" | "ja" | "zh">("en");

  // Target post preview state
  const [targetPostContext, setTargetPostContext] = useState<TargetPostContext | null>(null);
  const [fetchingTarget, setFetchingTarget] = useState(false);
  const [targetFetchError, setTargetFetchError] = useState<string | null>(null);

  // Personalized post state
  const [personalizedPost, setPersonalizedPost] = useState<PersonalizedPostResponse | null>(null);
  const [fetchingPersonalized, setFetchingPersonalized] = useState(false);

  // Persona state
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<PersonaType | null>(null);
  const [regeneratingSuggestion, setRegeneratingSuggestion] = useState(false);

  // Mobile UI state
  const [activeTab, setActiveTab] = useState<"suggestion" | "personalized">("personalized");
  const [showPolishMenu, setShowPolishMenu] = useState(false);
  const [showTranslateMenu, setShowTranslateMenu] = useState(false);

  // Improved scores after applying tips
  const [improvedScores, setImprovedScores] = useState<PentagonScores | null>(null);

  const targetUrlDebounceRef = useRef<NodeJS.Timeout | null>(null);

  // Reset all state to start fresh
  const handleReset = useCallback(() => {
    setContent("");
    setPostType("original");
    setTargetUrl("");
    setAnalysis(null);
    setSelectedTips([]);
    setSuggestion(null);
    setDetectedLanguage("en");
    setSuggestionLanguage("en");
    setTargetLanguage("en");
    setTargetPostContext(null);
    setTargetFetchError(null);
    setPersonalizedPost(null);
    setSelectedPersona(null);
    setImprovedScores(null);
  }, []);

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
          target_language: langToUse,
        });
        setAnalysis(result);
        // Reset tip selection when analysis changes
        setSelectedTips([]);
        setSuggestion(null);
        setImprovedScores(null);
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
    [username, postType, targetUrl, targetLanguage]
  );

  // Fetch personas on mount
  useEffect(() => {
    api.getPersonas().then(setPersonas).catch(console.error);
  }, []);

  // Clear analysis when switching post type
  useEffect(() => {
    setAnalysis(null);
    setSelectedTips([]);
    setSuggestion(null);
    setTargetPostContext(null);
    setTargetFetchError(null);
    setSelectedPersona(null);
    setImprovedScores(null);
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
        setTargetPostContext(null);
        // Extract error message from API response
        const errorMessage = error instanceof Error ? error.message : "Unknown error";
        if (errorMessage.includes("recent 200 posts")) {
          setTargetFetchError("Post not found in recent 200 posts. Try a more recent post from this account.");
        } else {
          setTargetFetchError("Could not fetch target post. Please select language manually.");
        }
      } finally {
        setFetchingTarget(false);
      }
    }, 400);

    return () => {
      if (targetUrlDebounceRef.current) {
        clearTimeout(targetUrlDebounceRef.current);
      }
    };
  }, [targetUrl, postType]);

  // Fetch personalized post when target context is loaded or persona changes
  useEffect(() => {
    if (!targetPostContext || postType === "original") {
      setPersonalizedPost(null);
      return;
    }

    if (!username) {
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
          persona: selectedPersona || undefined,
        });
        setPersonalizedPost(result);
      } catch {
        // Silently skip if profile not found - feature just won't be available
        setPersonalizedPost(null);
      } finally {
        setFetchingPersonalized(false);
      }
    };

    fetchPersonalized();
  }, [targetPostContext, postType, username, targetLanguage, selectedPersona]);

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
    if (selectedTips.length === 0 || !analysis) return;

    setApplyingTips(true);
    try {
      // Build tip selections with descriptions from analysis
      const tipSelections = selectedTips.map((tipId) => {
        const tip = analysis.quick_tips.find((t) => t.tip_id === tipId);
        return {
          tip_id: tipId,
          description: tip?.description || tipId,
        };
      });

      const result = await api.applyTips({
        username,
        original_content: content,
        selected_tips: tipSelections,
        language: detectedLanguage,
      });
      setSuggestion(result);
      setSuggestionLanguage(detectedLanguage); // Set initial suggestion language

      // Calculate improved scores based on predicted_improvement
      if (result.predicted_improvement && analysis) {
        const newScores = { ...analysis.scores };
        Object.entries(result.predicted_improvement).forEach(([key, value]) => {
          // Parse "+15%" format to number
          const match = value.match(/([+-]?\d+)/);
          if (match && key in newScores) {
            const improvement = parseInt(match[1], 10);
            newScores[key as keyof typeof newScores] = Math.min(100, Math.max(0, newScores[key as keyof typeof newScores] + improvement));
          }
        });
        setImprovedScores(newScores);
      }
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

  const handlePolishSuggestion = async (type: PolishType) => {
    if (!suggestion || polishing) return;

    setPolishing(type);
    try {
      // For translation, the language parameter doesn't matter (target is in the type)
      // For other polish types, use the current suggestion language
      const result = await api.polishPost({
        content: suggestion.suggested_content,
        polish_type: type,
        language: suggestionLanguage,
        target_post_content: analysis?.context?.target_post_content,
      });
      setSuggestion({
        ...suggestion,
        suggested_content: result.polished_content,
      });

      // Update suggestion language if translation was done
      if (type === "translate_en") {
        setSuggestionLanguage("en");
      } else if (type === "translate_ko") {
        setSuggestionLanguage("ko");
      } else if (type === "translate_zh") {
        setSuggestionLanguage("zh");
      }
    } catch (error) {
      console.error("Failed to polish:", error);
    } finally {
      setPolishing(null);
    }
  };

  // Polish personalized post
  const handlePolishPersonalized = async (type: PolishType) => {
    if (!personalizedPost || polishing) return;

    setPolishing(type);
    try {
      const result = await api.polishPost({
        content: personalizedPost.generated_content,
        polish_type: type,
        language: targetLanguage,
        target_post_content: targetPostContext?.content.text,
      });
      setPersonalizedPost({
        ...personalizedPost,
        generated_content: result.polished_content,
      });
    } catch (error) {
      console.error("Failed to polish personalized:", error);
    } finally {
      setPolishing(null);
    }
  };

  // Unified polish handler - applies to both suggestion and personalized post in parallel
  const handlePolishAll = async (type: PolishType) => {
    if (polishing) return;

    // Polish both in parallel for faster execution
    const tasks: Promise<void>[] = [];
    if (suggestion) {
      tasks.push(handlePolishSuggestion(type));
    }
    if (personalizedPost) {
      tasks.push(handlePolishPersonalized(type));
    }
    await Promise.all(tasks);
  };

  // Regenerate suggestion with persona styling
  const handleSuggestionPersona = async (personaId: PersonaType | null) => {
    if (!suggestion || regeneratingSuggestion) return;

    // selectedPersona is now unified - we update it and regenerate
    if (!personaId) return; // Just deselecting

    setRegeneratingSuggestion(true);
    try {
      // Use generate-personalized-post to restyle the suggestion with persona
      const result = await api.generatePersonalizedPost({
        username,
        target_post_content: suggestion.suggested_content,
        target_author: username, // Self as author since we're restyling our own content
        post_type: "quote", // Use quote to "add perspective" to existing content
        language: suggestionLanguage,
        persona: personaId,
      });

      if (result?.generated_content) {
        setSuggestion({
          ...suggestion,
          suggested_content: result.generated_content,
        });
      }
    } catch (error) {
      console.error("Failed to apply persona to suggestion:", error);
    } finally {
      setRegeneratingSuggestion(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Row 1: Input + Analysis (2-col on desktop) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          {/* Post Type Selector + Reset Button */}
          <div className="flex justify-between items-center">
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
                  {type === "original" ? "My Post" : type === "reply" ? "Reply" : "Quote"}
                </button>
              ))}
            </div>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-yellow-600/70 hover:bg-yellow-600 text-yellow-100 font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              <span>🔄</span>
              <span>Reset</span>
            </button>
          </div>

          {/* Target URL (for reply/quote) - URL input + preview */}
          {postType !== "original" && (
            <div className="space-y-3">
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="Target post URL (https://x.com/...)"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />

              {/* Fetching state */}
              {fetchingTarget && (
                <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                  <div className="flex items-center gap-3 text-gray-400">
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <div>
                      <span className="text-white">Fetching target post...</span>
                      <p className="text-sm text-gray-500">Please wait</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Target Preview - below URL input */}
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
                      </div>
                      <p className="text-gray-300 mb-3 text-sm">
                        {targetPostContext.content.text.length > 280
                          ? targetPostContext.content.text.slice(0, 280) + "..."
                          : targetPostContext.content.text}
                      </p>
                      <div className="flex gap-3 text-xs text-gray-500">
                        <span>❤️ {targetPostContext.metrics.likes.toLocaleString()}</span>
                        <span>🔁 {targetPostContext.metrics.reposts.toLocaleString()}</span>
                        <span>💬 {targetPostContext.metrics.replies.toLocaleString()}</span>
                      </div>
                      {/* Hidden meaning / interpretation */}
                      {targetPostContext.interpretation && (
                        <div className="mt-3 pt-3 border-t border-gray-700">
                          <div className="text-xs text-yellow-400 font-medium mb-1">💡 What this post means:</div>
                          <p className="text-gray-400 text-xs">
                            {targetPostContext.interpretation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Error message */}
              {targetFetchError && !fetchingTarget && (
                <div className="p-3 bg-yellow-900/20 border border-yellow-700/50 rounded-lg">
                  <p className="text-yellow-400 text-sm">⚠️ {targetFetchError}</p>
                </div>
              )}
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
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Analyzing... Please wait</span>
              </>
            ) : (
              <>
                <span>🔍</span>
                <span>Analyze</span>
              </>
            )}
          </button>
        </div>

        {/* Analysis Results - Part of Row 1 */}
        <div className="flex flex-col justify-center h-full">
        {loading && (
          <div className="flex flex-col items-center justify-center h-full min-h-[300px]">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-gray-400">Analyzing post...</p>
            <p className="text-gray-500 text-sm mt-1">Please wait</p>
          </div>
        )}

        {analysis && !loading && (
          <div className="bg-gray-800 rounded-xl p-4 h-full flex flex-col justify-center mt-6">
            <h3 className="text-lg font-semibold text-white mb-2 text-center">
              {improvedScores ? "Improved Score" : "Predicted Score"}
              {improvedScores && <span className="text-green-400 text-sm ml-2">✨</span>}
            </h3>
            <RadarChart scores={improvedScores || analysis.scores} size={240} />
            <div className="text-center mt-2">
              <span className={`text-2xl font-bold ${improvedScores ? "text-green-400" : "text-blue-400"}`}>
                {(
                  Object.values(improvedScores || analysis.scores).reduce((a, b) => a + b, 0) /
                  5
                ).toFixed(0)}
              </span>
              <span className="text-gray-400 ml-2">/ 100</span>
              {improvedScores && analysis && (
                <span className="text-green-400 text-sm ml-2">
                  (+{(
                    (Object.values(improvedScores).reduce((a, b) => a + b, 0) -
                    Object.values(analysis.scores).reduce((a, b) => a + b, 0)) / 5
                  ).toFixed(0)})
                </span>
              )}
            </div>
          </div>
        )}

        {!analysis && !loading && (
          <div className="text-center py-12 text-gray-500">
            {postType === "original" ? (
              <>
                Enter your post content, then
                <br />
                click <span className="text-blue-400">[🔍 Analyze]</span> button
              </>
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
      {/* End of Row 1 */}

      {/* Row 2: Quick Tips (full width) */}
      {analysis && !loading && analysis.quick_tips.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-4">
          <h3 className="text-lg font-semibold text-white mb-4">
            💡 Quick Tips{" "}
            <span className="text-sm font-normal text-gray-400">
              (Select up to 3)
            </span>
          </h3>
          <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {analysis.quick_tips.map((tip) => (
              <li key={tip.tip_id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-700/30">
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
                  <span className="text-gray-300 text-sm">{tip.description}</span>
                  <span
                    className={`ml-2 text-xs font-medium ${
                      tip.target_score === "engagement"
                        ? "text-green-400"
                        : tip.target_score === "reach"
                        ? "text-blue-400"
                        : tip.target_score === "virality"
                        ? "text-purple-400"
                        : tip.target_score === "quality"
                        ? "text-yellow-400"
                        : "text-orange-400"
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

      {/* Row 3: Suggestions (full width) */}
      {(suggestion || (postType !== "original" && (fetchingPersonalized || personalizedPost || targetPostContext))) && (
        <div className="w-full">
          {/* Unified Controls: Persona Selector + Polish Buttons (side by side) */}
          <div className="mb-4 p-4 bg-gray-700/50 rounded-lg">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Left: Persona Selector */}
              {personas.length > 0 && (
                <div>
                  <span className="text-gray-300 text-sm block mb-2">
                    Choose Your Voice:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {personas.map((persona) => (
                      <button
                        key={persona.id}
                        onClick={() => {
                          const newPersona = selectedPersona === persona.id ? null : persona.id;
                          setSelectedPersona(newPersona);
                          if (suggestion && newPersona) {
                            handleSuggestionPersona(newPersona);
                          }
                        }}
                        disabled={regeneratingSuggestion || polishing !== null || fetchingPersonalized}
                        className={`px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-all disabled:opacity-50 ${
                          selectedPersona === persona.id
                            ? "bg-blue-600 text-white ring-2 ring-blue-400"
                            : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                        }`}
                      >
                        <span>{persona.icon}</span>
                        <span className="hidden sm:inline">{persona.name}</span>
                        {persona.risk_level === "medium" && (
                          <span className="text-yellow-400 text-xs">⚡</span>
                        )}
                        {(regeneratingSuggestion || fetchingPersonalized) && selectedPersona === persona.id && (
                          <span className="text-xs">⏳</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Right: Polish Buttons - applies to both suggestion and personalized */}
              {(suggestion || personalizedPost) && (
                <div>
                  <span className="text-gray-300 text-sm block mb-2">
                    Polish with Claude AI:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handlePolishAll("grammar")}
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
                      onClick={() => handlePolishAll("twitter")}
                      disabled={polishing !== null}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        polishing === "twitter"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      } disabled:opacity-50`}
                    >
                      🐦 Twitter {polishing === "twitter" && "⏳"}
                    </button>
                    <button
                      onClick={() => handlePolishAll("280char")}
                      disabled={polishing !== null}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        polishing === "280char"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      } disabled:opacity-50`}
                    >
                      📏 280 {polishing === "280char" && "⏳"}
                    </button>
                    <button
                      onClick={() => handlePolishAll("translate_en")}
                      disabled={polishing !== null}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        polishing === "translate_en"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      } disabled:opacity-50`}
                    >
                      🇺🇸 {polishing === "translate_en" && "⏳"}
                    </button>
                    <button
                      onClick={() => handlePolishAll("translate_ko")}
                      disabled={polishing !== null}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        polishing === "translate_ko"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      } disabled:opacity-50`}
                    >
                      🇰🇷 {polishing === "translate_ko" && "⏳"}
                    </button>
                    <button
                      onClick={() => handlePolishAll("translate_zh")}
                      disabled={polishing !== null}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        polishing === "translate_zh"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                      } disabled:opacity-50`}
                    >
                      🇨🇳 {polishing === "translate_zh" && "⏳"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Mobile: Tab switcher */}
          {postType !== "original" && suggestion && (
            <div className="flex lg:hidden border-b border-gray-700 mb-4">
              <button
                onClick={() => setActiveTab("suggestion")}
                className={`flex-1 py-3 text-center ${
                  activeTab === "suggestion"
                    ? "border-b-2 border-blue-500 text-blue-400"
                    : "text-gray-500"
                }`}
              >
                ✨ Suggestion
              </button>
              <button
                onClick={() => setActiveTab("personalized")}
                className={`flex-1 py-3 text-center ${
                  activeTab === "personalized"
                    ? "border-b-2 border-purple-500 text-purple-400"
                    : "text-gray-500"
                }`}
              >
                🤖 AI Post
              </button>
            </div>
          )}

          {/* Desktop: Side by side */}
          <div className="hidden lg:grid lg:grid-cols-2 gap-4">
            {/* Post Suggestion Panel */}
            {suggestion && (
              <div className="bg-gray-800 rounded-xl p-4 border-2 border-blue-500">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  ✨ Post Suggestion
                  {selectedPersona && (
                    <span className="text-sm font-normal px-2 py-0.5 bg-blue-900/50 text-blue-300 rounded">
                      {personas.find(p => p.id === selectedPersona)?.icon} {personas.find(p => p.id === selectedPersona)?.name}
                    </span>
                  )}
                </h3>

                <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                  <p className="text-white whitespace-pre-wrap">
                    {suggestion.suggested_content}
                  </p>
                  <div className="text-xs text-gray-500 mt-2">
                    {suggestion.suggested_content.length}/280
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
                <button
                  onClick={() => handleCopy(suggestion.suggested_content)}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <span>📋</span>
                  <span>Copy to Clipboard</span>
                </button>
              </div>
            )}

            {/* AI Personalized Post Panel */}
            {postType !== "original" && (fetchingPersonalized || personalizedPost || targetPostContext) && (
              <div className="bg-gray-800 rounded-xl p-4 border-2 border-purple-500">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  🤖 AI Personalized Post
                  {personalizedPost?.persona && (
                    <span className="text-sm font-normal px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded">
                      {personalizedPost.persona.icon} {personalizedPost.persona.name}
                    </span>
                  )}
                </h3>

                {fetchingPersonalized ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin mb-3"></div>
                    <p className="text-gray-400">
                      {selectedPersona
                        ? `Generating ${selectedPersona} response...`
                        : "AI is generating personalized post..."}
                    </p>
                    <p className="text-gray-500 text-sm mt-1">Please wait</p>
                  </div>
                ) : personalizedPost && (
                  <>
                    <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                      <p className="text-white whitespace-pre-wrap">
                        {personalizedPost.generated_content}
                      </p>
                      <div className="text-xs text-gray-500 mt-2">
                        {personalizedPost.generated_content.length}/280
                      </div>
                    </div>

                    {personalizedPost.persona && (
                      <div className="mb-4 p-3 bg-purple-900/30 rounded-lg border border-purple-600/30">
                        <div className="text-sm text-purple-300 mb-2 font-medium">
                          📈 Expected Impact ({personalizedPost.persona.name})
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(personalizedPost.persona.pentagon_boost).map(([key, value]) => (
                            <span
                              key={key}
                              className={`text-xs px-2 py-1 rounded ${
                                value > 0
                                  ? "bg-green-900/50 text-green-400"
                                  : value < 0
                                    ? "bg-red-900/50 text-red-400"
                                    : "bg-gray-700 text-gray-400"
                              }`}
                            >
                              {key}: {value > 0 ? "+" : ""}{Math.round(value * 100)}%
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

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

                    <button
                      onClick={() => handleCopy(personalizedPost.generated_content)}
                      className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <span>📋</span>
                      <span>Copy to Clipboard</span>
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Mobile: Show based on active tab */}
          <div className="lg:hidden">
            {/* If only suggestion exists (original post), show it directly */}
            {postType === "original" && suggestion && (
              <div className="bg-gray-800 rounded-xl p-4 border-2 border-blue-500">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  ✨ Post Suggestion
                  {selectedPersona && (
                    <span className="text-sm font-normal px-2 py-0.5 bg-blue-900/50 text-blue-300 rounded">
                      {personas.find(p => p.id === selectedPersona)?.icon} {personas.find(p => p.id === selectedPersona)?.name}
                    </span>
                  )}
                </h3>

                <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                  <p className="text-white whitespace-pre-wrap">
                    {suggestion.suggested_content}
                  </p>
                  <div className="text-xs text-gray-500 mt-2">
                    {suggestion.suggested_content.length}/280
                  </div>
                </div>

                {/* Mobile: Polish/Translate Dropdowns */}
                <div className="flex gap-2 mb-4">
                  {/* Polish dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowPolishMenu(!showPolishMenu);
                        setShowTranslateMenu(false);
                      }}
                      className="px-3 py-2 bg-gray-700 rounded-lg text-sm text-gray-300"
                    >
                      ✍️ Polish ▼
                    </button>
                    {showPolishMenu && (
                      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10 min-w-[140px]">
                        <button onClick={() => { handlePolishSuggestion("grammar"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Keep Tone</button>
                        <button onClick={() => { handlePolishSuggestion("twitter"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Twitter Style</button>
                        <button onClick={() => { handlePolishSuggestion("280char"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Fit 280</button>
                      </div>
                    )}
                  </div>

                  {/* Translate dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowTranslateMenu(!showTranslateMenu);
                        setShowPolishMenu(false);
                      }}
                      className="px-3 py-2 bg-gray-700 rounded-lg text-sm text-gray-300"
                    >
                      🌐 Translate ▼
                    </button>
                    {showTranslateMenu && (
                      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10 min-w-[120px]">
                        <button onClick={() => { handlePolishSuggestion("translate_en"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇺🇸 English</button>
                        <button onClick={() => { handlePolishSuggestion("translate_ko"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇰🇷 한국어</button>
                        <button onClick={() => { handlePolishSuggestion("translate_zh"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇨🇳 中文</button>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleCopy(suggestion.suggested_content)}
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
                  >
                    📋 Copy
                  </button>
                </div>

                <div className="flex flex-wrap gap-2 mb-2">
                  {suggestion.applied_tips.map((tip) => (
                    <span
                      key={tip.tip_id}
                      className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs"
                    >
                      {tip.description}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* For reply/quote, show based on tab */}
            {postType !== "original" && activeTab === "suggestion" && suggestion && (
              <div className="bg-gray-800 rounded-xl p-4 border-2 border-blue-500">
                <h3 className="text-lg font-semibold text-white mb-3">✨ Post Suggestion</h3>

                <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                  <p className="text-white whitespace-pre-wrap">
                    {suggestion.suggested_content}
                  </p>
                  <div className="text-xs text-gray-500 mt-2">
                    {suggestion.suggested_content.length}/280
                  </div>
                </div>

                {/* Mobile dropdowns */}
                <div className="flex gap-2 mb-4">
                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowPolishMenu(!showPolishMenu);
                        setShowTranslateMenu(false);
                      }}
                      className="px-3 py-2 bg-gray-700 rounded-lg text-sm text-gray-300"
                    >
                      ✍️ Polish ▼
                    </button>
                    {showPolishMenu && (
                      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10 min-w-[140px]">
                        <button onClick={() => { handlePolishSuggestion("grammar"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Keep Tone</button>
                        <button onClick={() => { handlePolishSuggestion("twitter"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Twitter Style</button>
                        <button onClick={() => { handlePolishSuggestion("280char"); setShowPolishMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">Fit 280</button>
                      </div>
                    )}
                  </div>

                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowTranslateMenu(!showTranslateMenu);
                        setShowPolishMenu(false);
                      }}
                      className="px-3 py-2 bg-gray-700 rounded-lg text-sm text-gray-300"
                    >
                      🌐 Translate ▼
                    </button>
                    {showTranslateMenu && (
                      <div className="absolute bottom-full mb-2 left-0 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10 min-w-[120px]">
                        <button onClick={() => { handlePolishSuggestion("translate_en"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇺🇸 English</button>
                        <button onClick={() => { handlePolishSuggestion("translate_ko"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇰🇷 한국어</button>
                        <button onClick={() => { handlePolishSuggestion("translate_zh"); setShowTranslateMenu(false); }} className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700">🇨🇳 中文</button>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleCopy(suggestion.suggested_content)}
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
                  >
                    📋 Copy
                  </button>
                </div>
              </div>
            )}

            {postType !== "original" && activeTab === "personalized" && (
              <div className="bg-gray-800 rounded-xl p-4 border-2 border-purple-500">
                <h3 className="text-lg font-semibold text-white mb-3">🤖 AI Personalized Post</h3>

                {fetchingPersonalized ? (
                  <div className="flex flex-col items-center justify-center py-8">
                    <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin mb-3"></div>
                    <p className="text-gray-400">Generating...</p>
                  </div>
                ) : personalizedPost ? (
                  <>
                    <div className="bg-gray-700/50 rounded-lg p-4 mb-4">
                      <p className="text-white whitespace-pre-wrap">
                        {personalizedPost.generated_content}
                      </p>
                      <div className="text-xs text-gray-500 mt-2">
                        {personalizedPost.generated_content.length}/280
                      </div>
                    </div>

                    <button
                      onClick={() => handleCopy(personalizedPost.generated_content)}
                      className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <span>📋</span>
                      <span>Copy to Clipboard</span>
                    </button>
                  </>
                ) : (
                  <p className="text-gray-500 text-center py-4">Enter a target URL to generate</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
