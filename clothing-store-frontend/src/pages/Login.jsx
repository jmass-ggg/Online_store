import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API_BASE_URL } from "../api";
import "./login.css";

export default function Login() {
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", email); // OAuth2 expects "username"
      formData.append("password", password);

      const res = await fetch(`${API_BASE_URL}/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Login failed");
      }

      const data = await res.json();

      // Store tokens
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      // Redirect to home
      nav("/", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="page">
      <section className="left">
        <div className="form-wrap">

          {/* LOGO */}
          <div className="login-logo">
            <Link to="/" className="logo-text">JAMES</Link>
          </div>

          <h1>Welcome Back!</h1>
          <p className="sub">Welcome back please enter your details</p>

          {error && <p style={{ color: "red", fontSize: 12 }}>{error}</p>}

          <form className="form" onSubmit={onSubmit}>
            <div className="field">
              <label>Email</label>
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label>Password</label>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button className="btn primary" type="submit">
              Sign in
            </button>

            <p className="bottom">
              Don&apos;t have an account?
              <Link to="/register"> Sign up</Link>
            </p>
          </form>
        </div>
      </section>

      <section className="right" aria-hidden="true"></section>
    </main>
  );
}
