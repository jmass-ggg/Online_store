import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./login.css";
import { apiFetch, setStoredAccessToken } from "../api";

export default function Login() {
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    if (loading) return;

    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email.trim());
      formData.append("password", password);

      const data = await apiFetch("/login/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!data?.access_token) throw new Error("Missing access token from server");

      setStoredAccessToken(data.access_token);
      nav("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-left">
        <div className="login-formWrap">
          <div className="login-logo">
            <Link to="/" className="login-logoText">JAMES</Link>
          </div>

          <h1 className="login-title">Welcome Back!</h1>
          <p className="login-sub">Please enter your details to sign in</p>

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

              <div className="login-passwordRow">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="login-showBtn"
                  onClick={() => setShowPw((v) => !v)}
                >
                  {showPw ? "Hide" : "Show"}
                </button>
              </div>

              <Link className="login-forgot" to="#">
                Forgot password?
              </Link>
            </div>

            <button className="login-btn login-primary" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
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
