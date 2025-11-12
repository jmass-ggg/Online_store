// src/api/api.js
import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000", // FastAPI backend
});

// Register user
export const registerUser = async (userData) => {
  return await API.post("/user/register", {
    username: userData.name,
    email: userData.email,
    password: userData.password,
  });
};

// Login user
export const loginUser = async (credentials) => {
  const formBody = new URLSearchParams();
  formBody.append("username", credentials.email);
  formBody.append("password", credentials.password);

  return await API.post("/user/login", formBody, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};

// Get orders
export const getMyOrders = async (token) => {
  return await API.get("/orders/my", {
    headers: { Authorization: `Bearer ${token}` },
  });
};

// ✅ Add this default export so Homepage.js can import it
export default API;
