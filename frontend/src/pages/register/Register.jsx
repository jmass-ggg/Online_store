import React, { useState } from "react";
import "./Register.css";
import backgroundImage from "../assests/images/qq.jpg";

const Register = ({ switchPage, handleRegister }) => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    phone_number: "",
    password: "",
    address: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const onSubmit = (e) => {
    e.preventDefault();
    handleRegister(formData);
  };

  return (
    <div
      className="page"
      style={{ backgroundImage: `url(${backgroundImage})` }}
    >
      <div className="overlay" />

      {/* HEADER */}
      <header className="top-bar">
        <span className="logo">JAMES</span>
        <div className="top-actions">
          <button className="link">Sign Up</button>
          <button onClick={switchPage}>Log In</button>
        </div>
      </header>

      {/* REGISTER FORM */}
      <div className="register-container">
        
        <form className="register-card" onSubmit={onSubmit}>
          <h1 className="Register">REGISTER</h1>
          <input
            type="text"
            name="username"
            placeholder="username"
            value={formData.username}
            onChange={handleChange}
            required
          />

          <input
            type="email"
            name="email"
            placeholder="email"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <input
            type="tel"
            name="phone_number"
            placeholder="phone number"
            value={formData.phone_number}
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

          <input
            type="text"
            name="address"
            placeholder="address"
            value={formData.address}
            onChange={handleChange}
            required
          />

          <button type="submit" className="register-btn">
            Register
          </button>

          <p className="footer-text" onClick={switchPage}>
            Already have an account?
          </p>
        </form>
      </div>

      {/* FOOTER */}
      <footer className="footer-links">
        <span>About</span>
        <span>Help</span>
        <span>Privacy & Terms</span>
      </footer>
    </div>
  );
};

export default Register;
