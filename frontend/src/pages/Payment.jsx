import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Payment.css";
import { apiFetch } from "../api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const CHECKOUT_CTX_KEY = "checkout_context";
const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

function readCheckoutContext() {
  try {
    return JSON.parse(sessionStorage.getItem(CHECKOUT_CTX_KEY) || "{}");
  } catch {
    return {};
  }
}

function toApiUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  const base = API_BASE_URL.replace(/\/+$/, "");
  const clean = String(path).startsWith("/") ? path : `/${path}`;
  return `${base}${clean}`;
}

function resolveBackendPaymentMethod(selectedMethod) {
  if (selectedMethod === "esewa") return "ESEWA";
  if (selectedMethod === "cod") return "COD";
  return null;
}

const Payment = () => {
  const navigate = useNavigate();

  const [selectedMethod, setSelectedMethod] = useState("esewa");
  const [search, setSearch] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const profileRef = useRef(null);

  const checkoutContext = useMemo(() => readCheckoutContext(), []);

  const items = Array.isArray(checkoutContext?.items) ? checkoutContext.items : [];
  const itemsTotal = Number(checkoutContext?.totals?.itemsTotal || 0);
  const deliveryFee = Number(checkoutContext?.totals?.deliveryFee || 0);
  const baseTotal = Number(checkoutContext?.totals?.total || 0);

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

  async function handleConfirmPayment() {
    setErrorMsg("");

    const backendPaymentMethod = resolveBackendPaymentMethod(selectedMethod);
    if (!backendPaymentMethod) {
      setErrorMsg("This payment method is not connected yet.");
      return;
    }

    if (!checkoutContext?.address_id) {
      setErrorMsg("Shipping address missing. Please return to checkout.");
      return;
    }

    if (!items.length) {
      setErrorMsg("No checkout items found. Please return to checkout.");
      return;
    }

    setLoading(true);

    try {
      let createdOrder;

      if (checkoutContext.mode === "BUY_NOW") {
        const item = items[0];

        createdOrder = await apiFetch("/orders/buy-now", {
          method: "POST",
          body: JSON.stringify({
            address_id: Number(checkoutContext.address_id),
            variant_id: Number(item.variant_id),
            quantity: Number(item.quantity),
            payment_method: backendPaymentMethod,
          }),
        });

        localStorage.removeItem(BUY_NOW_KEY);
        window.dispatchEvent(new Event("buy_now:updated"));
      } else {
        createdOrder = await apiFetch("/orders/order", {
          method: "POST",
          body: JSON.stringify({
            address_id: Number(checkoutContext.address_id),
            payment_method: backendPaymentMethod,
          }),
        });

        localStorage.removeItem(CART_KEY);
        window.dispatchEvent(new Event("cart:updated"));
      }

      const nextOrderId = createdOrder?.order_id;
      const nextTotal = Number(createdOrder?.total_price ?? baseTotal);
      const paymentRedirectUrl = createdOrder?.payment_redirect_url || null;

      if (!nextOrderId) {
        throw new Error("Order created, but order id was not returned.");
      }

      localStorage.setItem("current_order_id", String(nextOrderId));
      sessionStorage.setItem("current_order_total", String(nextTotal));

      if (paymentRedirectUrl) {
        window.location.assign(toApiUrl(paymentRedirectUrl));
        return;
      }

      navigate("/orders");
    } catch (e) {
      const detail = e?.detail;
      if (typeof detail === "string") setErrorMsg(detail);
      else setErrorMsg(e?.message || "Failed to create order");
    } finally {
      setLoading(false);
    }
  }

  const canProceed = !!checkoutContext?.address_id && items.length > 0;

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

        {!!errorMsg && (
          <div
            style={{
              marginBottom: 16,
              padding: "12px 14px",
              borderRadius: 10,
              background: "#ffe7e7",
              color: "#b00020",
              border: "1px solid #ffcdcd",
            }}
          >
            {errorMsg}
          </div>
        )}

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
                  <p>Not connected yet</p>
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
                  <p>Not connected yet</p>
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
                    Your order will be created first, then you will be redirected to eSewa.
                  </p>

                  <ol className="detail-list ordered">
                    <li>Click Pay Now.</li>
                    <li>Your order will be created with ESEWA payment method.</li>
                    <li>You will be redirected to eSewa to complete payment.</li>
                  </ol>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                    disabled={loading || !canProceed}
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
                    <li>A 2% cash handling fee is shown here for UI only.</li>
                    <li>Your order will be created immediately after confirmation.</li>
                  </ul>

                  <button
                    className="detail-action-btn"
                    type="button"
                    onClick={handleConfirmPayment}
                    disabled={loading || !canProceed}
                  >
                    {loading ? "Creating Order..." : "Confirm Order"}
                  </button>
                </div>
              )}

              {selectedMethod === "card" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <div className="detail-icon-box">💳</div>
                    <div>
                      <h3>Credit / Debit Card</h3>
                      <p>Not connected yet</p>
                    </div>
                  </div>

                  <p className="detail-intro">
                    This payment method is not connected to the backend yet.
                  </p>
                </div>
              )}

              {selectedMethod === "khalti" && (
                <div className="payment-detail-content">
                  <div className="detail-head">
                    <img src="/ime.png" alt="Khalti by IME" className="detail-brand-logo" />
                    <div>
                      <h3>Khalti by IME</h3>
                      <p>Not connected yet</p>
                    </div>
                  </div>

                  <p className="detail-intro">
                    This payment method is not connected to the backend yet.
                  </p>
                </div>
              )}
            </div>
          </div>

          <aside className="payment-summary-card">
            <h3>Order Summary</h3>

            <div className="summary-line">
              <span>Mode</span>
              <span>{checkoutContext?.mode || "N/A"}</span>
            </div>

            <div className="summary-line">
              <span>Items</span>
              <span>{items.length}</span>
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
              disabled={loading || !canProceed}
            >
              {loading
                ? "PLEASE WAIT..."
                : selectedMethod === "esewa"
                ? "PROCEED TO ESEWA"
                : selectedMethod === "cod"
                ? "CONFIRM ORDER"
                : "NOT AVAILABLE"}
            </button>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Payment;