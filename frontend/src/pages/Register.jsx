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
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.id]: e.target.value }));
  }

  function continueWithGoogle() {
    alert("Google login not connected yet. Add your OAuth URL here.");
  }

  function saveAuthTokens(res) {
    // Accept different token field names (backend variations)
    const access =
      res?.access_token || res?.accessToken || res?.token || res?.auth_token || res?.authToken;

    const refresh = res?.refresh_token || res?.refreshToken;

    if (access) localStorage.setItem("access_token", access);
    if (res?.auth_token) localStorage.setItem("auth_token", res.auth_token);
    if (refresh) localStorage.setItem("refresh_token", refresh);

    // Save username for Home initials
    localStorage.setItem("username", form.username.trim());

    // notify app to refresh auth state
    window.dispatchEvent(new Event("auth:changed"));
  }

  async function tryAutoLogin(email, password) {
    // We try multiple common FastAPI styles:
    // 1) JSON body {email, password}
    // 2) JSON body {username, password} (some APIs use "username" field)
    // 3) Form-encoded (OAuth2PasswordRequestForm) username=<email>&password=<pw>
    const attempts = [
      {
        name: "JSON email+password",
        url: "/user/login",
        options: {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        },
      },
      {
        name: "JSON username+password",
        url: "/user/login",
        options: {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, password }),
        },
      },
      {
        name: "FORM username+password",
        url: "/user/login",
        options: {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ username: email, password }).toString(),
        },
      },
    ];

    let lastErr = null;

    for (const a of attempts) {
      try {
        const res = await apiFetch(a.url, a.options);

        // must contain some token to be considered success
        const hasToken =
          res?.access_token || res?.accessToken || res?.token || res?.auth_token || res?.authToken;

        if (!hasToken) throw new Error("Login response did not include a token.");
        return res;
      } catch (e) {
        lastErr = e;
      }
    }

    throw lastErr || new Error("Auto-login failed");
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const payload = {
      username: form.username.trim(),
      email: form.email.trim(),
      phone_number: form.phone_number.trim(),
      password: form.password,
    };

    try {
      // 1) Register
      await apiFetch("/user/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      // 2) Auto-login
      const loginRes = await tryAutoLogin(payload.email, payload.password);

      // 3) Save token + redirect Home
      saveAuthTokens(loginRes);
      nav("/", { replace: true });
    } catch (err) {
      setError(err?.message || "Something went wrong");
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
              <input
                id="username"
                type="text"
                value={form.username}
                onChange={handleChange}
                required
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
              />
            </div>

            <div className="login-field">
              <label htmlFor="phone_number">Phone Number</label>
              <input
                id="phone_number"
                type="tel"
                value={form.phone_number}
                onChange={handleChange}
                required
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
              />
            </div>

            <button className="login-btn login-primary" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>

            <button
              className="login-btn login-google"
              type="button"
              onClick={continueWithGoogle}
              disabled={loading}
            >
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
