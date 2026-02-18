import { Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

import Shoes from "./pages/Shoes.jsx";
import Product from "./pages/Product.jsx";

import Cart from "./pages/Cart.jsx";        // ✅ add
import Checkout from "./pages/Checkout.jsx";
import Payment from "./pages/Payment.jsx";

import ProtectedRoute from "./routes/ProtectedRoute.jsx";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected */}
      <Route
        path="/shoes"
        element={
          <ProtectedRoute>
            <Shoes />
          </ProtectedRoute>
        }
      />

      <Route
        path="/product/:slug"
        element={
          <ProtectedRoute>
            <Product />
          </ProtectedRoute>
        }
      />

      {/* ✅ Cart page */}
      <Route
        path="/cart"
        element={
          <ProtectedRoute>
            <Cart />
          </ProtectedRoute>
        }
      />

      {/* If you still use this page */}
      <Route
        path="/checkout"
        element={
          <ProtectedRoute>
            <Checkout />
          </ProtectedRoute>
        }
      />

      {/* ✅ Payment page */}
      <Route
        path="/payment"
        element={
          <ProtectedRoute>
            <Payment />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
