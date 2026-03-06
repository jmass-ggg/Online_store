import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Payment.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const CHECKOUT_CTX_KEY = "checkout_context";

const Payment = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [selectedMethod, setSelectedMethod] = useState("esewa");
  const [search, setSearch] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const profileRef = useRef(null);

  const checkoutContext = useMemo(() => {
    try {
      return JSON.parse(sessionStorage.getItem(CHECKOUT_CTX_KEY) || "{}");
    } catch {
      return {};
    }
  }, []);

  const orderId = String(
    location.state?.orderId ||
      localStorage.getItem("current_order_id") ||
      checkoutContext?.order_id ||
      ""
  );

  const itemsTotal = Number(checkoutContext?.totals?.itemsTotal || 0);
  const deliveryFee = Number(checkoutContext?.totals?.deliveryFee || 0);
  const baseTotal = Number(
    location.state?.totalAmount ||
      sessionStorage.getItem("current_order_total") ||
      checkoutContext?.totals?.total ||
      0
  );

  const codFee = selectedMethod === "cod" ? Number((baseTotal * 0.02).toFixed(2)) : 0;
  const totalAmount = useMemo(() => baseTotal + codFee, [baseTotal, codFee]);

  useEffect(() => {
    function onDocMouseDown(e) {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }

    function onEsc(e) {
      if (e.key === "Escape") {
        setProfileOpen(false);
      }
    }

    document.addEventListener("mousedown", onDocMouseDown);
    window.addEventListener("keydown", onEsc);

    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      window.removeEventListener("keydown", onEsc);
    };
  }, []);

  const go = (path) => {
    setProfileOpen(false);
    navigate(path);
  };

  const logout = () => {
    setProfileOpen(false);
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  };

  const handleEsewaPayment = () => {
    if (!orderId) {
      alert("Order ID not found. Please go back to checkout.");
      return;
    }

    setLoading(true);

    window.location.assign(
      `${API_BASE_URL}/payments/esewa/initiate?order_id=${encodeURIComponent(orderId)}`
    );
  };

  const handleConfirmPayment = () => {
    if (!selectedMethod) {
      alert("Please select a payment method");
      return;
    }

    if (selectedMethod === "esewa") {
      handleEsewaPayment();
      return;
    }

    if (selectedMethod === "cod") {
      alert("Order confirmed with Cash on Delivery");
      return;
    }

    if (selectedMethod === "khalti") {
      alert("Khalti payment integration not connected yet.");
      return;
    }

    alert("Card payment integration not connected yet.");
  };

  return (
    <div className="payment-shell">
      <header className="payment-top-header">
        <div className="payment-wrap payment-header-row">
          <div className="payment-brand">
            <Link to="/" className="payment-brand-logo">
              JAMES
            </Link>
          </div>

          <nav className="payment-top-nav">
            <Link to="/">Categories</Link>
            <Link to="/">Flash Sale</Link>
          </nav>

          <div className="payment-header-actions">
            <div className="payment-search">
              <span className="payment-search-icon" aria-hidden="true">
                🔎
              </span>
              <input
                type="text"
                placeholder="Search for products..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <button
              className="payment-icon-btn"
              type="button"
              title="Cart"
              onClick={() => navigate("/checkout")}
            >
              🛒
            </button>

            <button className="payment-icon-btn" type="button" title="Notifications">
              🔔
            </button>

            <div className="payment-profile-wrap" ref={profileRef}>
              <button
                className="payment-profile-btn"
                type="button"
                aria-expanded={profileOpen}
                onClick={() => setProfileOpen((prev) => !prev)}
                title="Account"
              >
                <span className="payment-profile-avatar">👤</span>
              </button>

              {profileOpen && (
                <div className="payment-profile-menu" role="menu">
                  <button
                    className="payment-profile-item"
                    type="button"
                    onClick={() => go("/account")}
                  >
                    Manage My Account
                  </button>

                  <button
                    className="payment-profile-item"
                    type="button"
                    onClick={() => go("/orders")}
                  >
                    My Orders
                  </button>

                  <button
                    className="payment-profile-item"
                    type="button"
                    onClick={() => go("/wishlist")}
                  >
                    Wishlist
                  </button>

                  <div className="payment-profile-divider" />

                  <button
                    className="payment-profile-item danger"
                    type="button"
                    onClick={logout}
                  >
                    Log out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="payment-wrap">
        <div className="payment-breadcrumb">
          Home <span>›</span> Cart <span>›</span> <strong>Payment</strong>
        </div>

        <h2 className="payment-title">Select Payment Method</h2>

        <div className="payment-main-grid">
          <div className="payment-left">
            <div className="payment-method-tabs">
              <button
                className={`payment-method-tab ${selectedMethod === "card" ? "active" : ""}`}
                onClick={() => setSelectedMethod("card")}
                type="button"
              >
                <div className="method-icon-emoji">💳</div>
                <div className="method-text">
                  <h4>Credit / Debit Card</h4>
                  <p>Credit / Debit Card</p>
                </div>
              </button>

              <button
                className={`payment-method-tab ${selectedMethod === "esewa" ? "active" : ""}`}
                onClick={() => setSelectedMethod("esewa")}
                type="button"
              >
                <img src="/eswea.png" alt="eSewa" className="method-icon" />
                <div className="method-text">
                  <h4>eSewa Mobile Wallet</h4>
                  <p>Mobile Wallet</p>
                </div>
              </button>

              <button
                className={`payment-method-tab ${selectedMethod === "khalti" ? "active" : ""}`}
                onClick={() => setSelectedMethod("khalti")}
                type="button"
              >
                <img src="/ime.png" alt="Khalti by IME" className="method-icon" />
                <div className="method-text">
                  <h4>Khalti by IME</h4>
                  <p>Mobile Wallet</p>
                </div>
              </button>

              <button
                className={`payment-method-tab ${selectedMethod === "cod" ? "active" : ""}`}
                onClick={() => setSelectedMethod("cod")}
                type="button"
              >
                <img
                  src="/cash_delivery.png"
                  alt="Cash on Delivery"
                  className="method-icon"
                />
                <div className="method-text">
                  <h4>Cash on Delivery</h4>
                  <p>Cash on Delivery</p>
                </div>
              </button>
            </div>

            <div className="payment-detail-panel">
              {selectedMethod === "esewa" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <img src="/eswea.png" alt="eSewa" className="detail-brand-logo" />
                    <div>
                      <h3>Pay with eSewa</h3>
                      <p>Fast and secure wallet payment</p>
                    </div>
                  </div>

                  <p className="detail-intro">
                    You will be redirected to your eSewa account to complete your payment:
                  </p>

                  <ol className="detail-list ordered">
                    <li>Login to your eSewa account using your eSewa ID and password.</li>
                    <li>Make sure your account is active and has sufficient balance.</li>
                    <li>Enter OTP sent to your registered mobile number.</li>
                  </ol>

                  <p className="detail-note">
                    Login using your eSewa mobile number and password.
                  </p>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                    disabled={loading || !orderId}
                  >
                    {loading ? "Redirecting..." : "Pay Now"}
                  </button>
                </div>
              )}

              {selectedMethod === "cod" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <img
                      src="/cash_delivery.png"
                      alt="Cash on Delivery"
                      className="detail-brand-logo"
                    />
                    <div>
                      <h3>Cash on Delivery</h3>
                      <p>Pay when the parcel arrives</p>
                    </div>
                  </div>

                  <ul className="detail-list">
                    <li>You may pay in cash to our courier upon receiving your parcel.</li>
                    <li>A 2% cash handling fee is applied for Cash on Delivery orders.</li>
                    <li>Before receiving the parcel, confirm the delivery status is updated.</li>
                    <li>Check the parcel details before making payment to the courier.</li>
                  </ul>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                  >
                    Confirm Order
                  </button>
                </div>
              )}

              {selectedMethod === "card" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <div className="detail-icon-box">💳</div>
                    <div>
                      <h3>Credit / Debit Card</h3>
                      <p>Visa, MasterCard supported</p>
                    </div>
                  </div>

                  <p className="detail-intro">
                    Secure card payment is available for this order.
                  </p>

                  <ul className="detail-list">
                    <li>Enter your card number, expiry date, and CVV on the next screen.</li>
                    <li>Your payment will be processed through a secure checkout gateway.</li>
                    <li>Please make sure your card supports online transactions.</li>
                  </ul>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                  >
                    Continue
                  </button>
                </div>
              )}

              {selectedMethod === "khalti" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <img src="/ime.png" alt="Khalti by IME" className="detail-brand-logo" />
                    <div>
                      <h3>Khalti by IME</h3>
                      <p>Wallet payment option</p>
                    </div>
                  </div>

                  <p className="detail-intro">Pay quickly using your Khalti wallet.</p>

                  <ul className="detail-list">
                    <li>Login to your Khalti wallet account.</li>
                    <li>Verify the payment amount before confirmation.</li>
                    <li>Complete the payment using OTP or MPIN.</li>
                  </ul>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                  >
                    Continue
                  </button>
                </div>
              )}
            </div>
          </div>

          <aside className="payment-summary-card">
            <h3>Order Summary</h3>

            <div className="summary-line">
              <span>Order ID</span>
              <span>{orderId || "N/A"}</span>
            </div>

            <div className="summary-line">
              <span>Items Total</span>
              <span>${itemsTotal.toFixed(2)}</span>
            </div>

            <div className="summary-line">
              <span>Delivery Fee</span>
              <span>${deliveryFee.toFixed(2)}</span>
            </div>

            {selectedMethod === "cod" && (
              <div className="summary-line">
                <span>Cash Payment Fee (2%)</span>
                <span>${codFee.toFixed(2)}</span>
              </div>
            )}

            <div className="summary-divider" />

            <div className="summary-line total">
              <span>Total Amount</span>
              <span>${totalAmount.toFixed(2)}</span>
            </div>

            <button
              className="summary-main-btn"
              type="button"
              onClick={handleConfirmPayment}
              disabled={loading || !orderId}
            >
              {loading
                ? "PLEASE WAIT..."
                : selectedMethod === "esewa"
                ? "PROCEED TO ESEWA"
                : selectedMethod === "cod"
                ? "CONFIRM ORDER"
                : selectedMethod === "khalti"
                ? "PROCEED TO KHALTI"
                : "CONFIRM PAYMENT"}
            </button>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Payment;