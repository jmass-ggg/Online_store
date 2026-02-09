import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./login.css";
import { apiFetch } from "../api";

export default function Register() {
  const nav = useNavigate();

  const [form, setForm] = useState({
    username: "",
    email: "",
    phone_number: "",
    password: "",
    address: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.id]: e.target.value }));
  }

  function continueWithGoogle() {
    alert("Google login not connected yet. Add your OAuth URL here.");
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await apiFetch("/user/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      nav("/login", { replace: true });
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
          <div className="login-logo">
            <Link to="/" className="login-logoText">JAMES</Link>
          </div>

          <h1 className="login-title">Create Account</h1>
          <p className="login-sub">Please fill in your details to register</p>

          {error && <p className="login-error">{error}</p>}

          <form className="login-form" onSubmit={onSubmit}>
            <div className="login-field">
              <label htmlFor="username">Username</label>
              <input id="username" type="text" value={form.username} onChange={handleChange} required />
            </div>

            <div className="login-field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={form.email} onChange={handleChange} required />
            </div>

            <div className="login-field">
              <label htmlFor="phone_number">Phone Number</label>
              <input id="phone_number" type="tel" value={form.phone_number} onChange={handleChange} required />
            </div>

            <div className="login-field">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" value={form.password} onChange={handleChange} required />
            </div>

            <div className="login-field">
              <label htmlFor="address">Address</label>
              <input id="address" type="text" value={form.address} onChange={handleChange} required />
            </div>

            <button className="login-btn login-primary" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>

            <button className="login-btn login-google" type="button" onClick={continueWithGoogle} disabled={loading}>
              <span className="login-gIcon" aria-hidden="true">G</span>
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
