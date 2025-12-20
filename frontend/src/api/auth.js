import axios from "axios";

const BASE_URL = "http://localhost:8000";

export const registerUser = async (userData) => {
  try {
    const res = await axios.post(`${BASE_URL}/user/register`, userData);
    return res.data;
  } catch (err) {
    throw err.response?.data || { detail: "Something went wrong" };
  }
};

export const loginUser = async (email, password) => {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  try {
    const res = await axios.post(`${BASE_URL}/login/`, formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("access_token", res.data.access_token);
    localStorage.setItem("refresh_token", res.data.refresh_token);
    return res.data;
  } catch (err) {
    throw err.response?.data || { detail: "Login failed" };
  }
};
