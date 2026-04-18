export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const ASSET_ORIGIN = import.meta.env.VITE_ASSET_ORIGIN || "";

const ACCESS_TOKEN_KEY = "access_token";
export const BUY_NOW_KEY = "buy_now_item";


export function getStoredAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || "";
}

export function setStoredAccessToken(token) {
  if (!token) return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  window.dispatchEvent(new Event("auth:changed"));
}

export function clearStoredAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.dispatchEvent(new Event("auth:changed"));
}

export function joinUrl(u) {
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;

  if (!ASSET_ORIGIN) {
    return u.startsWith("/") ? u : `/${u}`;
  }

  return `${ASSET_ORIGIN}${u.startsWith("/") ? u : `/${u}`}`;
}

async function parseResponse(res) {
  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return await res.json();
  }

  return await res.text();
}

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

let refreshPromise = null;

async function refreshAccessTokenOnce() {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (!res.ok) {
      clearStoredAccessToken();
      throw new Error(await parseError(res));
    }

    const data = await parseResponse(res);

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

export async function apiFetch(path, options = {}) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE_URL}${normalizedPath}`;
  const isRefreshRequest = normalizedPath === "/auth/refresh";
  const isLoginRequest = normalizedPath === "/auth/login";

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

  const doFetch = (token) =>
    fetch(url, {
      ...options,
      headers: makeHeaders(token),
      credentials: "include",
    });

  let token = getStoredAccessToken();
  let res = await doFetch(token);

  if (res.status === 401 && !isRefreshRequest && !isLoginRequest) {
    try {
      token = await refreshAccessTokenOnce();
      res = await doFetch(token);
    } catch (err) {
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