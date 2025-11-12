// src/components/Cart.js
import React, { useState } from "react";
import styles from "./Homepage.module.css";

const Cart = ({ cartItems = [], removeFromCart, clearCart }) => {
  const [loading, setLoading] = useState(false);

  // Calculate total price
  const total = cartItems.reduce(
    (acc, item) => acc + item.price * item.quantity,
    0
  );

  if (cartItems.length === 0) {
    return (
      <div className={styles.cart}>
        <h2>Your Cart is Empty 🛒</h2>
      </div>
    );
  }

  // Place order handler
  const placeOrderHandler = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        alert("You must login first!");
        setLoading(false);
        return;
      }

      // ✅ Payload format as backend expects
      const payload = {
        items: cartItems.map((item) => ({
          product_id: item.product_id, // must match backend
          quantity: Number(item.quantity) || 1,
        })),
      };

      const response = await fetch("http://127.0.0.1:8000/order/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Order failed");
      }

      alert("✅ Order placed successfully!");
      console.log("Order response:", data);

      // ✅ Clear cart after successful order
      if (clearCart) clearCart();

    } catch (err) {
      console.error(err);
      alert(`❌ Error placing order: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.cart}>
      <h2>Your Cart</h2>
      {cartItems.map((item) => (
        <div key={item.product_id} className={styles.cartItem}>
          <span>{item.product_name}</span>
          <span>Qty: {item.quantity}</span>
          <span>${(item.price * item.quantity).toFixed(2)}</span>
          {removeFromCart && (
            <button onClick={() => removeFromCart(item.product_id)}>
              Remove
            </button>
          )}
        </div>
      ))}
      <h3>Total: ${total.toFixed(2)}</h3>
      <button onClick={placeOrderHandler} disabled={loading}>
        {loading ? "Placing Order..." : "Place Order"}
      </button>
    </div>
  );
};

export default Cart;
