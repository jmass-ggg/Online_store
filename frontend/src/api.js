export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const ASSET_ORIGIN = import.meta.env.VITE_ASSET_ORIGIN || "";

const ACCESS_TOKEN_KEY = "access_token";
export const BUY_NOW_KEY = "buy_now_item";

// Get the stored access token from localStorage
export function getStoredAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || "";
}

// Set the access token in localStorage
export function setStoredAccessToken(token) {
  if (!token) return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  window.dispatchEvent(new Event("auth:changed"));
}

// Clear the stored access token from localStorage
export function clearStoredAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.dispatchEvent(new Event("auth:changed"));
}

// Join the base API URL with the given path
export function joinUrl(u) {
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;

  if (!ASSET_ORIGIN) {
    return u.startsWith("/") ? u : `/${u}`;
  }

  return `${ASSET_ORIGIN}${u.startsWith("/") ? u : `/${u}`}`;
}

// Parse the response body based on content type
async function parseResponse(res) {
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await res.json();
  }
  return await res.text();
}

// Parse the error from the response body
async function parseError(res) {
  try {
    const data = await parseResponse(res);
    if (typeof data === "string") {
      return data || `Request failed (${res.status})`;
    }
    return data?.detail || data?.message || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

// This variable ensures that only one refresh request is made at a time
let refreshPromise = null;

// Handle token refresh and retry the failed request
async function refreshAccessTokenOnce() {
  console.log("Attempting to refresh token...");

  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    console.log("Refresh token response status:", res.status);

    if (!res.ok) {
      clearStoredAccessToken();
      throw new Error(await parseError(res));
    }

    const data = await parseResponse(res);
    console.log("Refresh token data:", data);

    if (!data?.access_token) {
      clearStoredAccessToken();
      throw new Error("Refresh did not return access_token");
    }

    setStoredAccessToken(data.access_token);
    return data.access_token;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

// Handle API requests and trigger token refresh if necessary
export async function apiFetch(path, options = {}) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE_URL}${normalizedPath}`;
  const isRefreshRequest = normalizedPath === "/auth/refresh";
  const isLoginRequest = normalizedPath === "/auth/login";

  // Create headers for the request
  const makeHeaders = (token) => {
    const headers = new Headers(options.headers || {});
    const isFormData = options.body instanceof FormData;
    const hasBody = options.body !== undefined && options.body !== null;

    if (!headers.has("Content-Type") && hasBody && !isFormData) {
      headers.set("Content-Type", "application/json");
    }

    if (token && !headers.has("Authorization") && !isRefreshRequest && !isLoginRequest) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    return headers;
  };

  // Perform the fetch request
  const doFetch = (token) =>
    fetch(url, {
      ...options,
      headers: makeHeaders(token),
      credentials: "include",
    });

  let token = getStoredAccessToken();
  let res = await doFetch(token);

  // If the response is 401 (Unauthorized), refresh the token and retry
  if (res.status === 401 && !isRefreshRequest && !isLoginRequest) {
    console.log("Token expired, attempting to refresh...");
    try {
      token = await refreshAccessTokenOnce();
      res = await doFetch(token);
    } catch (err) {
      console.error("Token refresh failed:", err);
      clearStoredAccessToken();
      throw err instanceof Error
        ? err
        : new Error("Session expired. Please login again.");
    }
  }

  if (!res.ok) {
    throw new Error(await parseError(res));
  }

  return await parseResponse(res);
}