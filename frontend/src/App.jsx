// src/App.jsx
import { Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

import Shoes from "./pages/Shoes.jsx";
import Product from "./pages/Product.jsx";

import AllProduct from "./pages/AllProduct.jsx"; // ✅ add
import Cart from "./pages/Cart.jsx";
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

      {/* ✅ All Products */}
      <Route
        path="/products"
        element={
          <ProtectedRoute>
            <AllProduct />
          </ProtectedRoute>
        }
      />

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

      <Route
        path="/cart"
        element={
          <ProtectedRoute>
            <Cart />
          </ProtectedRoute>
        }
      />

      <Route
        path="/checkout"
        element={
          <ProtectedRoute>
            <Checkout />
          </ProtectedRoute>
        }
      />

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
