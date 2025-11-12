import React, { useState } from "react";
import emailIcon from "../img/email.svg";
import passwordIcon from "../img/password.svg";
import styles from "./SignUp.module.css";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { notify } from "./toast";
import { Link, useHistory } from "react-router-dom"; // <-- useHistory for v5
import axios from "axios";

const Login = () => {
  const [data, setData] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const history = useHistory(); // <-- useHistory

  const checkData = async (obj) => {
    try {
      setLoading(true);

      const formBody = new URLSearchParams();
      formBody.append("username", obj.email);
      formBody.append("password", obj.password);

      const res = await axios.post(
        "http://localhost:8000/user/login",
        formBody,
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        }
      );

      const token = res.data.access_token;
      localStorage.setItem("token", token);

      notify("Login successful ✅", "success");

      history.push("/homepage"); // <-- replace navigate("/") with history.push
    } catch (err) {
      console.error("Login failed:", err.response?.data || err.message);
      notify("Invalid email or password ❌", "error");
    } finally {
      setLoading(false);
    }
  };

  const changeHandler = (event) => {
    setData({ ...data, [event.target.name]: event.target.value });
  };

  const submitHandler = (event) => {
    event.preventDefault();
    checkData(data);
  };

  return (
    <div className={styles.container}>
      <form className={styles.formLogin} onSubmit={submitHandler} autoComplete="off">
        <h2>Sign In</h2>
        <div>
          <div>
            <input
              type="text"
              name="email"
              value={data.email}
              placeholder="E-mail"
              onChange={changeHandler}
              autoComplete="off"
              required
            />
            <img src={emailIcon} alt="" />
          </div>
        </div>
        <div>
          <div>
            <input
              type="password"
              name="password"
              value={data.password}
              placeholder="Password"
              onChange={changeHandler}
              autoComplete="off"
              required
            />
            <img src={passwordIcon} alt="" />
          </div>
        </div>
        <div>
          <button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
          <span
            style={{
              color: "#a29494",
              textAlign: "center",
              display: "inline-block",
              width: "100%",
            }}
          >
            Don&apos;t have an account? <Link to="/signup">Create account</Link>
          </span>
        </div>
      </form>
      <ToastContainer />
    </div>
  );
};

export default Login;
