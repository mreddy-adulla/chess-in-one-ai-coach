// Production API endpoint (Tailscale Funnel)
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8080"; 

// Local development token (Fallback for easier testing)
const DEV_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXYtdXNlciIsInJvbGUiOiJDSElMRCIsImRldmljZV9pZCI6ImRldi1kZXZpY2UiLCJleHAiOjE3NjcyMzE3MDF9.AX67cotVYvFYzEwunGm-Q19VR5dmxmvcAHNNVIUNN9M";

export class ApiService {
  private static token: string | null = localStorage.getItem('auth_token') || DEV_TOKEN;

  static setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  static async request(path: string, options: RequestInit = {}) {
    if (!this.token) {
      console.warn(`[ApiService] No auth token found. Request to ${path} may fail.`);
    }

    const headers = {
      "Content-Type": "application/json",
      ...(this.token ? { "Authorization": `Bearer ${this.token}` } : {}),
      ...options.headers,
    };

    const url = `${API_BASE_URL}${path}`;
    console.log(`[ApiService] Request: ${options.method || 'GET'} ${url}`);
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        console.error(`[ApiService] Error Response: ${response.status} ${response.statusText} for ${url}`);
        if (response.status === 409) {
          throw new Error("Invalid state transition");
        }
        if (response.status === 403) {
          throw new Error("Access denied: role mismatch or approval required");
        }
        if (response.status === 401) {
          throw new Error("Unauthorized: Please log in again");
        }
        throw new Error(`API Error: ${response.statusText}`);
      }

      if (response.status === 204) return null;
      return response.json();
    } catch (error) {
      console.error(`[ApiService] Network Error:`, error);
      throw error;
    }
  }
}
