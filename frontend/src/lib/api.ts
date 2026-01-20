export const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

// Get stored tokens
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// Store tokens
export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

// Clear tokens
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Get authorization headers
function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    ...init,
  });
  if (!res.ok) {
    if (res.status === 401) {
      // Unauthorized - try to refresh token
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        // Retry the request with new token
        return getJSON<T>(path, init);
      }
      // Refresh failed, clear tokens and throw
      clearTokens();
      throw new Error("Session expired. Please login again.");
    }
    throw new Error(await res.text());
  }
  return res.json();
}

export async function postJSON<T>(
  path: string,
  body: unknown,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
    ...init,
  });
  if (!res.ok) {
    if (res.status === 401) {
      // Unauthorized - try to refresh token
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        // Retry the request with new token
        return postJSON<T>(path, body, init);
      }
      // Refresh failed, clear tokens and throw
      clearTokens();
      throw new Error("Session expired. Please login again.");
    }
    throw new Error(await res.text());
  }
  return res.json();
}

export async function uploadCSV(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/flights/upload_csv/`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: form,
  });
  if (!res.ok) {
    if (res.status === 401) {
      // Unauthorized - try to refresh token
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        // Retry the request with new token
        return uploadCSV(file);
      }
      // Refresh failed, clear tokens and throw
      clearTokens();
      throw new Error("Session expired. Please login again.");
    }
    throw new Error(await res.text());
  }
  return res.json();
}

// Try to refresh the access token
async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!res.ok) return false;

    const data = await res.json();
    if (data.access) {
      localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// Authentication APIs
export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Login failed");
  }

  const data = await res.json();
  if (data.access && data.refresh) {
    setTokens(data.access, data.refresh);
  } else {
    throw new Error("Invalid response from server");
  }
}

export function logout(): void {
  clearTokens();
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

// ML Operations
export function trainModel(opts: {
  contamination?: number;
  flight_limit?: number;
  save_model?: boolean;
}) {
  return postJSON("/api/anomalies/train_model/", opts);
}

export function runDetection(opts: {
  flight_ids?: string[];
  retrain?: boolean;
}) {
  return postJSON("/api/anomalies/detect_anomalies/", opts);
}
