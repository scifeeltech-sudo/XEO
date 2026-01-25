import { ProfileAnalysis, PostAnalysis, AnalyzePostRequest } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async analyzeProfile(username: string): Promise<ProfileAnalysis> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/profile/${username}/analyze`
    );

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
}

export const api = new APIClient();
