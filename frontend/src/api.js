export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const ASSET_ORIGIN = import.meta.env.VITE_ASSET_ORIGIN || ""; // optional

const ACCESS_TOKEN_KEY = "access_token";
const AUTH_TOKEN_KEY = "auth_token";

export function getStoredAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function setStoredAccessToken(token) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.dispatchEvent(new Event("auth:changed"));
}

export function clearStoredAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(AUTH_TOKEN_KEY);
  window.dispatchEvent(new Event("auth:changed"));
}

export function joinUrl(u) {
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;

  if (!ASSET_ORIGIN) return u.startsWith("/") ? u : `/${u}`;
  return `${ASSET_ORIGIN}${u.startsWith("/") ? u : `/${u}`}`;
}

// ---------- error parsing ----------
async function parseError(res) {
  try {
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const j = await res.json();
      return j?.detail || j?.message || JSON.stringify(j);
    }
    return await res.text();
  } catch {
    return `Request failed (${res.status})`;
  }
}

// ---------- refresh lock (prevents multiple refresh calls at once) ----------
let refreshPromise = null;

async function refreshAccessTokenOnce() {
  // If a refresh is already happening, await it.
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const res = await fetch(`${API_BASE_URL}/login/refresh`, {
      method: "POST",
      credentials: "include", // ✅ send refresh cookie
    });

    if (!res.ok) {
      // Refresh failed: session expired
      throw new Error(await parseError(res));
    }

    const data = await res.json();
    if (!data?.access_token) throw new Error("Refresh did not return access_token");

    setStoredAccessToken(data.access_token);
    return data.access_token;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

// ---------- main fetch ----------
export async function apiFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const makeHeaders = (token) => {
    const headers = new Headers(options.headers || {});

    const isFormData = options.body instanceof FormData;
    const hasBody = options.body !== undefined && options.body !== null;

    // Only set JSON content type if caller didn't set it and body is not FormData
    if (!headers.has("Content-Type") && hasBody && !isFormData) {
      headers.set("Content-Type", "application/json");
    }

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    return headers;
  };

  const doFetch = async (token) => {
    const res = await fetch(url, {
      ...options,
      headers: makeHeaders(token),
      credentials: "include", // ✅ include cookies always
    });
    return res;
  };

  // 1) try normally with current token
  let token = getStoredAccessToken();
  let res = await doFetch(token);

  // 2) if 401 try refresh once, then retry
  if (res.status === 401) {
    try {
      token = await refreshAccessTokenOnce();
      res = await doFetch(token);
    } catch (e) {
      // refresh failed => log user out
      clearStoredAccessToken();
      throw e instanceof Error ? e : new Error("Session expired. Please login again.");
    }
  }

  // 3) handle non-ok
  if (!res.ok) {
    throw new Error(await parseError(res));
  }

  // 4) return json or text
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}
