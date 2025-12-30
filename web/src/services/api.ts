// Hardcoded for local development, can be configured via build-time env vars if needed
export const API_BASE_URL = "http://localhost:8080"; 

// Local development tokens
const CHILD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXYtdXNlciIsInJvbGUiOiJDSElMRCIsImRldmljZV9pZCI6ImRldi1kZXZpY2UiLCJleHAiOjE3NjcxOTcyMjZ9.0RZAWPUUMBoywXuyk_c9q-ycjO2s13Wi5WojPtcXhyM";
const PARENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZXYtdXNlciIsInJvbGUiOiJQQVJFTlQiLCJkZXZpY2VfaWQiOiJkZXYtZGV2aWNlIiwiZXhwIjoxNzY3MTk3MjIwfQ.-2xGWLXobgxqGGGwArpDZghUwt-TIL2YPlgs5h94qTQ";

export class ApiService {
  private static token: string | null = null;

  static setToken(token: string) {
    this.token = token;
  }

  static async request(path: string, options: RequestInit = {}) {
    // Determine token based on path (PCI requires PARENT role)
    const isPci = path.startsWith("/pci") || path.startsWith("/questions");
    const activeToken = this.token || (isPci ? PARENT_TOKEN : CHILD_TOKEN);

    const headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${activeToken}`,
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
        console.error(`[ApiService] Error Response: ${response.status} ${response.statusText}`);
        if (response.status === 409) {
          throw new Error("Invalid state transition");
        }
        if (response.status === 403) {
          throw new Error("Access denied: role mismatch");
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
