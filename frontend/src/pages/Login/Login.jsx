import React, { useState } from "react";
import "./Login.css";
import backgroundImage from "../assests/images/qq.jpg";

const Login = ({ switchPage, handleLogin }) => {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const onSubmit = (e) => {
    e.preventDefault();
    handleLogin(formData);
  };

  return (
    <div className="page" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="login-card">
        <h1>JAMES</h1>
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label>Email</label>
            <div className="input-wrapper">
              <span className="icon">👤</span>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter your email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-wrapper">
              <span className="icon">🔒</span>
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
              />
              <span
                className="eye"
                role="button"
                tabIndex={0}
                onClick={() => setShowPassword(!showPassword)}
                onKeyDown={(e) => e.key === "Enter" && setShowPassword(!showPassword)}
              >
                👁
              </span>
            </div>
          </div>

          <div className="options">
            <label className="remember">
              <input type="checkbox" />
              Remember me
            </label>
          </div>

          <button type="submit" className="login-btn">
            LOGIN
          </button>
        </form>

        <button className="signup" onClick={switchPage}>
          Don't have an account? Register
        </button>
      </div>
    </div>
  );
};

export default Login;
