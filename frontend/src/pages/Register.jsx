import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./login.css";
import { apiFetch } from "../api";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e) {
    const { id, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [id]: value,
    }));
  }

  function continueWithGoogle() {
    alert("Google login not connected yet. Add your OAuth URL here.");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;

    setError("");
    setLoading(true);

    try {
      await apiFetch("/user/register", {
        method: "POST",
        body: JSON.stringify({
          username: form.username.trim(),
          email: form.email.trim(),
          password: form.password,
        }),
      });

      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-left">
        <div className="login-formWrap">
          <div className="login-logo">
            <Link to="/" className="login-logoText">
              JAMES
            </Link>
          </div>

          <h1 className="login-title">Create Account</h1>
          <p className="login-sub">Please fill in your details to register</p>

          {error ? <p className="login-error">{error}</p> : null}

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="login-field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="Enter your username"
              />
            </div>

            <div className="login-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
                placeholder="Enter your email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                required
                autoComplete="new-password"
                placeholder="Create a password"
              />
            </div>

            <button
              className="login-btn login-primary"
              type="submit"
              disabled={loading}
            >
              {loading ? "Creating account..." : "Create Account"}
            </button>

            <button
              className="login-btn login-google"
              type="button"
              onClick={continueWithGoogle}
              disabled={loading}
            >
              <span className="login-gIcon" aria-hidden="true">
                G
              </span>
              Continue with Google
            </button>

            <p className="login-bottom">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </form>
        </div>
      </section>

      <section className="login-right" aria-hidden="true" />
    </main>
  );
}