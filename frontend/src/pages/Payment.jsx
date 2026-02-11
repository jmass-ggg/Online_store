// src/pages/Payment.jsx
import React, { useState } from "react";
import "./Payment.css";
import { useNavigate } from "react-router-dom";

const Payment = () => {
  const navigate = useNavigate();
  const [selectedMethod, setSelectedMethod] = useState("");

  const totalAmount = 1000004.5; // You can pass this via props or context later

  const handleConfirmPayment = () => {
    if (!selectedMethod) {
      alert("Please select a payment method");
      return;
    }

    alert(`Payment method selected: ${selectedMethod}`);
    // Here you can redirect to success page
    // navigate("/order-success");
  };

  return (
    <div className="payment-page">
      <h2>Select Payment Method</h2>

      <div className="payment-container">
        {/* Left Side */}
        <div className="payment-methods">

          <div
            className={`payment-card ${selectedMethod === "card" ? "active" : ""}`}
            onClick={() => setSelectedMethod("card")}
          >
            <h4>Credit / Debit Card</h4>
            <p>Pay with Visa, MasterCard</p>
          </div>

          <div
            className={`payment-card ${selectedMethod === "esewa" ? "active" : ""}`}
            onClick={() => setSelectedMethod("esewa")}
          >
            <h4>eSewa Mobile Wallet</h4>
            <p>Pay using eSewa</p>
          </div>

          <div
            className={`payment-card ${selectedMethod === "khalti" ? "active" : ""}`}
            onClick={() => setSelectedMethod("khalti")}
          >
            <h4>Khalti by IME</h4>
            <p>Pay using Khalti Wallet</p>
          </div>

          <div
            className={`payment-card ${selectedMethod === "cod" ? "active" : ""}`}
            onClick={() => setSelectedMethod("cod")}
          >
            <h4>Cash on Delivery</h4>
            <p>Pay when product arrives</p>
          </div>

        </div>

        {/* Right Side */}
        <div className="order-summary">
          <h3>Order Summary</h3>
          <div className="summary-row">
            <span>Subtotal</span>
            <span>${totalAmount.toFixed(2)}</span>
          </div>

          <div className="summary-row total">
            <span>Total Amount</span>
            <span>${totalAmount.toFixed(2)}</span>
          </div>

          <button className="confirm-btn" onClick={handleConfirmPayment}>
            CONFIRM PAYMENT
          </button>
        </div>
      </div>
    </div>
  );
};

export default Payment;
