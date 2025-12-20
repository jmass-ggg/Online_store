import React, { useState } from "react";
import Login from "./pages/Login/Login";
import Register from "./pages/register/Register";
import { registerUser, loginUser } from "./api/auth";

const App = () => {
  const [isLoginPage, setIsLoginPage] = useState(true);

  const switchPage = () => setIsLoginPage(!isLoginPage);

  const handleRegister = async (userData) => {
    try {
      const res = await registerUser(userData);
      alert(`Registered successfully! Welcome, ${res.username}`);
      setIsLoginPage(true); // switch to login after registration
    } catch (err) {
      alert(err.detail || "Registration failed");
    }
  };

  const handleLogin = async (userData) => {
    try {
      const res = await loginUser(userData.email, userData.password);
      alert("Login successful!");
      console.log("Tokens:", res);
      // redirect to dashboard or homepage
    } catch (err) {
      alert(err.detail || "Login failed");
    }
  };

  return isLoginPage ? (
    <Login switchPage={switchPage} handleLogin={handleLogin} />
  ) : (
    <Register switchPage={switchPage} handleRegister={handleRegister} />
  );
};

export default App;
