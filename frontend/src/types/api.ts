export interface PentagonScores {
  reach: number;
  engagement: number;
  virality: number;
  quality: number;
  longevity: number;
}

export interface Insight {
  category: string;
  message: string;
  priority: "high" | "medium" | "low";
}

export interface Recommendation {
  action: string;
  expected_impact: string;
  description: string;
}

export interface ProfileAnalysis {
  username: string;
  scores: PentagonScores;
  insights: Insight[];
  recommendations: Recommendation[];
}

export interface PostContext {
  target_post_id: string;
  target_post_content: string;
  target_author: string;
  context_adjustments: Record<string, string>;
  recommendations: string[];
}

export interface PostAnalysis {
  scores: PentagonScores;
  breakdown: Record<string, number>;
  quick_tips: string[];
  context?: PostContext;
}

export interface AnalyzePostRequest {
  username: string;
  content: string;
  post_type: "original" | "reply" | "quote" | "thread";
  target_post_url?: string;
  media_type?: "image" | "video" | "gif";
}
