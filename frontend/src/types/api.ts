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
  target_language?: "ko" | "en" | "ja" | "zh";
}

export interface TipSelection {
  tip_id: string;
  description: string;
}

export interface ApplyTipsRequest {
  username: string;
  original_content: string;
  selected_tips: TipSelection[];
  language?: string;
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

export type PolishType = "grammar" | "twitter" | "280char" | "translate_en" | "translate_ko" | "translate_zh";

export interface PolishRequest {
  content: string;
  polish_type: PolishType;
  language?: string;
  target_post_content?: string;
}

export interface PolishChange {
  type: string;
  description: string;
}

export interface PolishResponse {
  original_content: string;
  polished_content: string;
  polish_type: string;
  language_detected: string;
  changes: PolishChange[];
  character_count: {
    original: number;
    polished: number;
  };
}

// Target Post Context types
export interface TargetPostAuthor {
  username: string;
  display_name?: string;
  followers_count: number;
  verified: boolean;
}

export interface TargetPostMetrics {
  likes: number;
  reposts: number;
  replies: number;
  quotes: number;
  views: number;
}

export interface TargetPostContent {
  text: string;
  media: { type: string; url: string }[];
  hashtags: string[];
}

export interface TargetPostAnalysis {
  age_minutes: number;
  freshness: string;
  virality_status: string;
  reply_saturation: string;
}

export interface TargetPostContext {
  post_id: string;
  post_url: string;
  author: TargetPostAuthor;
  content: TargetPostContent;
  metrics: TargetPostMetrics;
  created_at?: string;
  analysis: TargetPostAnalysis;
  opportunity_score: {
    overall: number;
    factors: Record<string, number>;
  };
  tips: string[];
  interpretation?: string;
}

// Personalized Post types
export interface StyleAnalysis {
  tone: string;
  emoji_style: string;
  topics: string[];
  writing_pattern: string;
}

// Persona types
export type PersonaType = "empathetic" | "contrarian" | "expander" | "expert";

export interface Persona {
  id: PersonaType;
  name: string;
  name_ko: string;
  icon: string;
  description: string;
  description_ko: string;
  risk_level: "low" | "medium" | "high";
  pentagon_boost: Record<string, number>;
  target_actions: string[];
}

export interface PersonaInfo {
  id: PersonaType;
  name: string;
  name_ko: string;
  icon: string;
  pentagon_boost: Record<string, number>;
}

export interface PersonalizedPostRequest {
  username: string;
  target_post_content: string;
  target_author: string;
  post_type: "reply" | "quote";
  language: string;
  persona?: PersonaType;
}

export interface TargetAnalysis {
  main_topic: string;
  key_points: string[];
  sentiment: string;
  what_to_address: string;
}

export interface PersonalizedPostResponse {
  username: string;
  generated_content: string;
  target_analysis?: TargetAnalysis;
  style_analysis: StyleAnalysis;
  confidence: number;
  reasoning: string;
  post_type: string;
  target_author: string;
  persona?: PersonaInfo;
}
