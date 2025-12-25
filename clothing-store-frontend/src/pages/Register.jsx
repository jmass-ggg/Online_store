import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API_BASE_URL } from "../api";
import "./login.css"; // reuse same CSS

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
    setForm({ ...form, [e.target.id]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/user/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Registration failed");
      }

      // ✅ success → go to login
      nav("/login", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="left">
        <div className="form-wrap">

          {/* LOGO */}
          <div className="login-logo">
            <Link to="/" className="logo-text">
              JAMES
            </Link>
          </div>

          <h1>Create Account</h1>
          <p className="sub">Please fill in your details to register</p>

          {error && <p style={{ color: "red", fontSize: 12 }}>{error}</p>}

          <form className="form" onSubmit={onSubmit}>
            <div className="field">
              <label>Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={form.username}
                onChange={handleChange}
                required
              />
            </div>

            <div className="field">
              <label>Email</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="field">
              <label>Phone Number</label>
              <input
                id="phone_number"
                type="tel"
                placeholder="Enter your phone number"
                value={form.phone_number}
                onChange={handleChange}
                required
              />
            </div>

            <div className="field">
              <label>Password</label>
              <input
                id="password"
                type="password"
                placeholder="Create a password"
                value={form.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="field">
              <label>Address</label>
              <input
                id="address"
                type="text"
                placeholder="Enter your address"
                value={form.address}
                onChange={handleChange}
                required
              />
            </div>

            <button className="btn primary" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>

            <p className="bottom">
              Already have an account?
              <Link to="/login"> Sign in</Link>
            </p>
          </form>
        </div>
      </section>

      <section className="right" aria-hidden="true"></section>
    </main>
  );
}
