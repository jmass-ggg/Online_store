import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { apiFetch, getStoredAccessToken, setStoredAccessToken } from "../api";

export default function ProtectedRoute({ children }) {
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let mounted = true;

    async function verifyAuth() {
      const token = getStoredAccessToken();

      if (token) {
        if (mounted) setStatus("authenticated");
        return;
      }

      try {
        const data = await apiFetch("/auth/refresh", { method: "POST" });

        if (data?.access_token) {
          setStoredAccessToken(data.access_token);
          if (mounted) setStatus("authenticated");
          return;
        }

        if (mounted) setStatus("unauthenticated");
      } catch (err) {
        console.error("Authentication failed:", err);
        if (mounted) setStatus("unauthenticated");
      }
    }

    verifyAuth();

    return () => {
      mounted = false;
    };
  }, []);

  if (status === "loading") return <div>Loading...</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;

  return children;
}