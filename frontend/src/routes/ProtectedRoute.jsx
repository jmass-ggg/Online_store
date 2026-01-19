import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children }) {
  const isAuth = localStorage.getItem("auth_token");

  if (!isAuth) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
