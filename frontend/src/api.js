export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const ASSET_ORIGIN = import.meta.env.VITE_ASSET_ORIGIN || ""; // optional

function getAccessToken() {
  return localStorage.getItem("access_token") || localStorage.getItem("auth_token") || "";
}

function setAccessToken(token) {
  localStorage.setItem("access_token", token);
  localStorage.setItem("auth_token", token);
  window.dispatchEvent(new Event("auth:changed"));
}

export function joinUrl(u) {
  if (!u) return "";
  if (/^https?:\/\//i.test(u)) return u;
  // keep relative in production (same origin). If ASSET_ORIGIN is set, it becomes absolute.
  if (!ASSET_ORIGIN) return u.startsWith("/") ? u : `/${u}`;
  return `${ASSET_ORIGIN}${u.startsWith("/") ? u : `/${u}`}`;
}

async function parseError(res) {
  try {
    const j = await res.json();
    return j?.detail || j?.message || JSON.stringify(j);
  } catch {
    try {
      return await res.text();
    } catch {
      return "Request failed";
    }
  }
}

async function tryRefresh() {
  try {
    const res = await fetch(`${API_BASE_URL}/login/refresh`, {
      method: "POST",
      credentials: "include", // refresh cookie
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data?.access_token) setAccessToken(data.access_token);
    return true;
  } catch {
    return false;
  }
}

/**
 * apiFetch("/product/slug/abc") -> calls /api/product/slug/abc
 * Automatically attaches Authorization header if token exists.
 * Automatically tries refresh once on 401.
 */
export async function apiFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers || {});
  const token = getAccessToken();

  // Only set JSON content-type if you didn't set something else and body is not FormData
  const isFormData = options.body instanceof FormData;
  if (!headers.has("Content-Type") && !isFormData && options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // IMPORTANT for cookies (refresh_token)
  });

  // attempt refresh once
  if (res.status === 401) {
    const ok = await tryRefresh();
    if (ok) {
      const headers2 = new Headers(headers);
      const token2 = getAccessToken();
      if (token2) headers2.set("Authorization", `Bearer ${token2}`);

      const res2 = await fetch(url, {
        ...options,
        headers: headers2,
        credentials: "include",
      });

      if (!res2.ok) throw new Error(await parseError(res2));
      return res2.headers.get("content-type")?.includes("application/json")
        ? res2.json()
        : res2.text();
    }
  }

  if (!res.ok) throw new Error(await parseError(res));

  return res.headers.get("content-type")?.includes("application/json")
    ? res.json()
    : res.text();
}
