import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API_BASE_URL } from "../api";
import "./login.css";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function continueWithGoogle() {
    alert("Google login not connected yet. Add your OAuth URL here.");
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${API_BASE_URL}/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!res.ok) {
        let msg = "Login failed";
        try {
          const err = await res.json();
          msg = err?.detail || msg;
        } catch {}
        throw new Error(msg);
      }

      const data = await res.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("auth_token", data.access_token);

      nav("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-left">
        <div className="login-formWrap">
          {/* ✅ LOGO */}
          <div className="login-logo">
            <Link to="/" className="login-logoText">
              JAMES
            </Link>
          </div>

          <h1 className="login-title">Welcome Back!</h1>
          <p className="login-sub">Welcome back please enter your details</p>

          {error && <p className="login-error">{error}</p>}

          <form className="login-form" onSubmit={onSubmit}>
            <div className="login-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <Link className="login-forgot" to="#">
                Forgot password
              </Link>
            </div>

            <button className="login-btn login-primary" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>

            <button
              className="login-btn login-google"
              type="button"
              onClick={continueWithGoogle}
              disabled={loading}
            >
              <span className="login-gIcon" aria-hidden="true">G</span>
              Sign in with Google
            </button>

            <p className="login-bottom">
              Don&apos;t have an account? <Link to="/register">Sign up</Link>
            </p>
          </form>
        </div>
      </section>

      <section className="login-right" aria-hidden="true" />
    </main>
  );
}
