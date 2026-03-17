import { Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";

import Shoes from "./pages/Shoes.jsx";
import Clothes from "./pages/Clothes.jsx";
import Accessories from "./pages/Accessories.jsx";
import Jewellery from "./pages/Jewellery.jsx";

import Product from "./pages/Product.jsx";
import AllProduct from "./pages/AllProduct.jsx";
import Cart from "./pages/Cart.jsx";
import Checkout from "./pages/Checkout.jsx";
import Payment from "./pages/Payment.jsx";
import EsewaResult from "./pages/EsewaResult.jsx";

import ProtectedRoute from "./routes/ProtectedRoute.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/products"
        element={
          <ProtectedRoute>
            <AllProduct />
          </ProtectedRoute>
        }
      />

      <Route
        path="/shoes"
        element={
          <ProtectedRoute>
            <Shoes />
          </ProtectedRoute>
        }
      />

      <Route
        path="/clothes"
        element={
          <ProtectedRoute>
            <Clothes />
          </ProtectedRoute>
        }
      />

      <Route
        path="/accessories"
        element={
          <ProtectedRoute>
            <Accessories />
          </ProtectedRoute>
        }
      />

      <Route
        path="/jewellery"
        element={
          <ProtectedRoute>
            <Jewellery />
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

      <Route path="/payment/esewa/result" element={<EsewaResult />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}