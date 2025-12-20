import React, { useState } from "react";
import "./Login.css";
import backgroundImage from "../assests/images/qq.jpg";

const Login = ({ switchPage, handleLogin }) => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const onSubmit = (e) => {
    e.preventDefault();
    handleLogin(formData);
  };

  return (
    <div
      className="page"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="overlay" />

      <header className="top-bar">
        <span className="logo">JAMES</span>
        <div className="top-actions">
          <button onClick={switchPage}>Sign Up</button>
          <button className="link">Log In</button>
        </div>
      </header>

      <div className="login-container">
        <form className="login-card" onSubmit={onSubmit}>
          <h1 className="login">LOGIN</h1>
          <input
            type="email"
            name="email"
            placeholder="username"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <input
            type="password"
            name="password"
            placeholder="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
          
          <button type="submit" className="login-btn">
            Log In
          </button>

          <p className="footer-text" onClick={switchPage}>
            Don’t have an account?
          </p>
        </form>
      </div>

      <footer className="footer-links">
        <span>About</span>
        <span>Help</span>
        <span>Privacy & Terms</span>
      </footer>
    </div>
  );
};

export default Login;
