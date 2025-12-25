import { useNavigate, Link } from "react-router-dom";
import "./login.css";

export default function Login() {
  const nav = useNavigate();

  function onSubmit(e) {
    e.preventDefault();
    localStorage.setItem("auth_token", "demo_token");
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

          <h1>Welcome Back!</h1>
          <p className="sub">Welcome back please enter your details</p>

          <form className="form" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" placeholder="Enter your email" />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
              />
              <a
                className="forgot"
                href="#"
                onClick={(e) => e.preventDefault()}
              >
                Forgot password
              </a>
            </div>

            <button className="btn primary" type="submit">
              Sign in
            </button>

            <button className="btn google" type="button">
              <span className="g-icon">G</span>
              <span>Sign in with Google</span>
            </button>

            <p className="bottom">
              Don&apos;t have an account?
              <a href="/register"> Sign up</a>
            </p>
          </form>
        </div>
      </section>

      <section className="right" aria-hidden="true"></section>
    </main>
  );
}
