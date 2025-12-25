import { useNavigate, Link } from "react-router-dom";
import "./login.css"; // reuse same CSS

export default function Register() {
  const nav = useNavigate();

  function onSubmit(e) {
    e.preventDefault();

    // Fake register for now
    localStorage.setItem("auth_token", "demo_token");

    // Go to home after register
    nav("/", { replace: true });
  }

  return (
    <main className="page">
      <section className="left">
        <div className="form-wrap">

          {/* ===== LOGO ===== */}
          <div className="login-logo">
            <Link to="/" className="logo-text">
              JAMES
            </Link>
          </div>

          <h1>Create Account</h1>
          <p className="sub">Please fill in your details to register</p>

          <form className="form" onSubmit={onSubmit}>
            {/* Username */}
            <div className="field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter your username"
                required
              />
            </div>

            {/* Email */}
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                required
              />
            </div>

            {/* Phone Number */}
            <div className="field">
              <label htmlFor="phone">Phone Number</label>
              <input
                id="phone"
                type="tel"
                placeholder="Enter your phone number"
                required
              />
            </div>

            {/* Password */}
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Create a password"
                required
              />
            </div>

            {/* Address */}
            <div className="field">
              <label htmlFor="address">Address</label>
              <input
                id="address"
                type="text"
                placeholder="Enter your address"
                required
              />
            </div>

            <button className="btn primary" type="submit">
              Create Account
            </button>

            <p className="bottom">
              Already have an account?
              <a href="/login"> Sign in</a>
            </p>
          </form>
        </div>
      </section>

      <section className="right" aria-hidden="true"></section>
    </main>
  );
}
