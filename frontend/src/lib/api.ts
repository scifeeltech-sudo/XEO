import {
  ProfileAnalysis,
  PostAnalysis,
  AnalyzePostRequest,
  ApplyTipsRequest,
  ApplyTipsResponse,
  PolishRequest,
  PolishResponse,
  TargetPostContext,
  PersonalizedPostRequest,
  PersonalizedPostResponse,
  Persona,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async analyzeProfile(username: string, refresh: boolean = false): Promise<ProfileAnalysis> {
    const url = new URL(`${this.baseUrl}/api/v1/profile/${username}/analyze`);
    if (refresh) {
      url.searchParams.set("refresh", "true");
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Failed to analyze profile: ${response.statusText}`);
    }

    return response.json();
  }

  async analyzePost(request: AnalyzePostRequest): Promise<PostAnalysis> {
    const response = await fetch(`${this.baseUrl}/api/v1/post/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze post: ${response.statusText}`);
    }

    return response.json();
  }

  async applyTips(request: ApplyTipsRequest): Promise<ApplyTipsResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/post/apply-tips`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to apply tips: ${response.statusText}`);
    }

    return response.json();
  }

  async polishPost(request: PolishRequest): Promise<PolishResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/post/polish`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to polish post: ${response.statusText}`);
    }

    return response.json();
  }

  async getPostContext(url: string): Promise<TargetPostContext> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/post/context?url=${encodeURIComponent(url)}`
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData.detail || response.statusText;
      throw new Error(detail);
    }

    return response.json();
  }

  async generatePersonalizedPost(
    request: PersonalizedPostRequest
  ): Promise<PersonalizedPostResponse | null> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/post/generate-personalized`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to generate personalized post: ${response.status}`);
    }

    return response.json();
  }

  async getPersonas(): Promise<Persona[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/post/personas`);

    if (!response.ok) {
      throw new Error(`Failed to get personas: ${response.statusText}`);
    }

    const data = await response.json();
    return data.personas;
  }
}

export const api = new APIClient();
