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

export interface QuickTip {
  tip_id: string;
  description: string;
  impact: string;
  target_score: string;
  selectable: boolean;
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
  quick_tips: QuickTip[];
  context?: PostContext;
}

export interface AnalyzePostRequest {
  username: string;
  content: string;
  post_type: "original" | "reply" | "quote" | "thread";
  target_post_url?: string;
  media_type?: "image" | "video" | "gif";
}

export interface ApplyTipsRequest {
  username: string;
  original_content: string;
  selected_tips: string[];
}

export interface AppliedTip {
  tip_id: string;
  description: string;
  impact: string;
}

export interface ApplyTipsResponse {
  original_content: string;
  suggested_content: string;
  applied_tips: AppliedTip[];
  predicted_improvement: Record<string, string>;
}
