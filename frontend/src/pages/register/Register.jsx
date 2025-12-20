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
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const onSubmit = (e) => {
    e.preventDefault();
    handleRegister(formData);
  };

  return (
    <div className="page" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="login-card">
        <h1>JAMES</h1>
        <form onSubmit={onSubmit}>
          <div className="form-group">
            <label>Username</label>
            <div className="input-wrapper">
              <span className="icon">👤</span>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Enter username"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Email</label>
            <div className="input-wrapper">
              <span className="icon">📧</span>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <div className="input-wrapper">
              <span className="icon">📞</span>
              <input
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="Enter phone number"
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
                placeholder="Enter password"
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

          <div className="form-group">
            <label>Address</label>
            <div className="input-wrapper">
              <span className="icon">🏠</span>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="Enter address"
                required
              />
            </div>
          </div>

          <div className="options">
            <label className="remember">
              <input type="checkbox" required />
              I agree to the terms & conditions
            </label>
          </div>

          <button type="submit" className="login-btn">
            REGISTER
          </button>
        </form>

        <button className="signup" onClick={switchPage}>
          Already have an account? Login
        </button>
      </div>
    </div>
  );
};

export default Register;
