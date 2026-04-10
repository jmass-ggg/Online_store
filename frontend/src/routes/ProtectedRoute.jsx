import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { apiFetch, setStoredAccessToken, clearStoredAccessToken } from "../api";

export default function ProtectedRoute({ children }) {
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let mounted = true;

    async function verifyAuth() {
      try {
        const refreshData = await apiFetch("/login/refresh", {
          method: "POST",
        });

        if (!refreshData?.access_token) {
          throw new Error("Missing access token");
        }

        setStoredAccessToken(refreshData.access_token);

        if (mounted) setStatus("authenticated");
      } catch {
        clearStoredAccessToken();
        if (mounted) setStatus("unauthenticated");
      }
    }

    verifyAuth();

    return () => {
      mounted = false;
    };
  }, []);

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  return children;
}