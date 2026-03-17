import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_BASE_URL, apiFetch } from "../api";
import "./Payment.css";

const CHECKOUT_CTX_KEY = "checkout_context";
const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

const PAYMENT_METHODS = {
  ESEWA: "ESEWA",
  COD: "CASH ON DELIVERY",
};

function safeParse(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function money(n) {
  return Number(n || 0).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
  });
}

function formatApiError(err) {
  const detail = err?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "field";
        return `${field}: ${d.msg}`;
      })
      .join(" | ");
  }

  return err?.message || "Something went wrong";
}

function buildBackendUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;

  const base = String(API_BASE_URL || "").replace(/\/+$/, "");
  const rel = String(path).startsWith("/") ? path : `/${path}`;

  return `${base}${rel}`;
}

function cleanupAfterCod(mode) {
  sessionStorage.removeItem(CHECKOUT_CTX_KEY);

  if (mode === "BUY_NOW") {
    localStorage.removeItem(BUY_NOW_KEY);
    window.dispatchEvent(new Event("buy_now:updated"));
    return;
  }

  localStorage.removeItem(CART_KEY);
  window.dispatchEvent(new Event("cart:updated"));
}

export default function Payment() {
  const navigate = useNavigate();

  const [checkoutCtx, setCheckoutCtx] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState(PAYMENT_METHODS.ESEWA);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(CHECKOUT_CTX_KEY);
    const parsed = safeParse(raw);

    if (!parsed || !parsed.address_id || !Array.isArray(parsed.items) || parsed.items.length === 0) {
      setError("Checkout data is missing. Please go back to checkout.");
      return;
    }

    setCheckoutCtx(parsed);
  }, []);

  const totals = useMemo(() => checkoutCtx?.totals || {}, [checkoutCtx]);

  async function handlePlaceOrder() {
    setError("");

    if (!checkoutCtx) {
      setError("Checkout data is missing.");
      return;
    }

    if (!checkoutCtx.address_id) {
      setError("Address is missing.");
      return;
    }

    setPlacingOrder(true);

    try {
      let res;

      if (checkoutCtx.mode === "BUY_NOW") {
        const item = checkoutCtx.items?.[0];

        if (!item?.variant_id || !item?.quantity) {
          throw new Error("Buy now item is missing.");
        }

        res = await apiFetch("/orders/buy-now", {
          method: "POST",
          body: JSON.stringify({
            address_id: Number(checkoutCtx.address_id),
            variant_id: Number(item.variant_id),
            quantity: Number(item.quantity),
            payment_method: paymentMethod,
          }),
        });
      } else {
        res = await apiFetch("/orders/order", {
          method: "POST",
          body: JSON.stringify({
            address_id: Number(checkoutCtx.address_id),
            payment_method: paymentMethod,
          }),
        });
      }

      if (paymentMethod === PAYMENT_METHODS.ESEWA) {
        const redirectUrl = res?.payment_redirect_url;

        if (!redirectUrl) {
          throw new Error("Backend did not return eSewa redirect URL.");
        }

        const finalUrl = buildBackendUrl(redirectUrl);

        // IMPORTANT:
        // This must be a real browser redirect because backend /payments/esewa/initiate
        // returns HTML with auto-submit form, not JSON and not a React page.
        window.location.href = finalUrl;
        return;
      }

      // COD success
      cleanupAfterCod(checkoutCtx.mode);
      setSuccessData(res);
    } catch (e) {
      setError(formatApiError(e));
    } finally {
      setPlacingOrder(false);
    }
  }

  if (successData) {
    return (
      <div className="payment-page">
        <div className="payment-wrap">
          <h1>Order Placed Successfully</h1>

          <div className="payment-card">
            <p><strong>Order ID:</strong> {successData.order_id}</p>
            <p><strong>Status:</strong> {successData.status}</p>
            <p><strong>Total:</strong> {money(successData.total_price)}</p>
            <p><strong>Payment Method:</strong> CASH ON DELIVERY</p>
          </div>

          <div className="payment-actions" style={{ marginTop: 16, display: "flex", gap: 12 }}>
            <button type="button" onClick={() => navigate("/products")}>
              Continue Shopping
            </button>
            <Link to="/checkout">Back to Checkout</Link>
          </div>
        </div>
      </div>
    );
  }

  if (!checkoutCtx) {
    return (
      <div className="payment-page">
        <div className="payment-wrap">
          <h1>Payment</h1>

          <div className="payment-card">
            <p style={{ color: "red" }}>{error || "Checkout data is missing."}</p>
          </div>

          <div className="payment-actions" style={{ marginTop: 16, display: "flex", gap: 12 }}>
            <button type="button" onClick={() => navigate("/checkout")}>
              Back to Checkout
            </button>
            <Link to="/">Home</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-page">
      <div className="payment-wrap">
        <div className="payment-breadcrumb" style={{ marginBottom: 16 }}>
          <Link to="/">Home</Link> <span>›</span> <Link to="/checkout">Checkout</Link> <span>›</span> <span>Payment</span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.2fr 0.8fr",
            gap: 20,
            alignItems: "start",
          }}
        >
          <section className="payment-card">
            <h2>Choose Payment Method</h2>

            <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 14,
                  border: "1px solid #ddd",
                  borderRadius: 10,
                  cursor: "pointer",
                }}
              >
                <input
                  type="radio"
                  name="payment_method"
                  value={PAYMENT_METHODS.ESEWA}
                  checked={paymentMethod === PAYMENT_METHODS.ESEWA}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <span><strong>eSewa</strong> — Pay online now</span>
              </label>

              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 14,
                  border: "1px solid #ddd",
                  borderRadius: 10,
                  cursor: "pointer",
                }}
              >
                <input
                  type="radio"
                  name="payment_method"
                  value={PAYMENT_METHODS.COD}
                  checked={paymentMethod === PAYMENT_METHODS.COD}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                />
                <span><strong>Cash on Delivery</strong></span>
              </label>
            </div>

            <hr style={{ margin: "20px 0" }} />

            <h3>Shipping Address</h3>
            <p><strong>{checkoutCtx.address?.full_name}</strong></p>
            <p>{checkoutCtx.address?.phone_number}</p>
            <p>
              {checkoutCtx.address?.line1}
              {checkoutCtx.address?.line2 ? `, ${checkoutCtx.address.line2}` : ""}
              {checkoutCtx.address?.region ? `, ${checkoutCtx.address.region}` : ""}
              {checkoutCtx.address?.postal_code ? `, ${checkoutCtx.address.postal_code}` : ""}
              {checkoutCtx.address?.country ? `, ${checkoutCtx.address.country}` : ""}
            </p>

            {error ? (
              <div style={{ marginTop: 16, color: "red" }}>{error}</div>
            ) : null}
          </section>

          <aside className="payment-card">
            <h2>Order Summary</h2>

            <div style={{ display: "grid", gap: 10, marginTop: 16 }}>
              {checkoutCtx.items.map((item, index) => (
                <div
                  key={`${item.variant_id}_${index}`}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    borderBottom: "1px solid #eee",
                    paddingBottom: 10,
                  }}
                >
                  <div>
                    <div>{item.product_name}</div>
                    <div style={{ fontSize: 13, opacity: 0.75 }}>
                      {item.size ? `Size: ${item.size} ` : ""}
                      {item.color ? `Color: ${item.color} ` : ""}
                      Qty: {item.quantity}
                    </div>
                  </div>
                  <div>{money(Number(item.price) * Number(item.quantity))}</div>
                </div>
              ))}

              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
                <span>Items</span>
                <span>{totals.itemsCount || 0}</span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Items Total</span>
                <span>{money(totals.itemsTotal || 0)}</span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Delivery Fee</span>
                <span>{money(totals.deliveryFee || 0)}</span>
              </div>

              <hr />

              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
                <span>Total</span>
                <span>{money(totals.total || 0)}</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handlePlaceOrder}
              disabled={placingOrder}
              style={{
                marginTop: 20,
                width: "100%",
                padding: "12px 16px",
                borderRadius: 10,
                border: "none",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              {placingOrder
                ? "PROCESSING..."
                : paymentMethod === PAYMENT_METHODS.ESEWA
                ? "PAY WITH ESEWA"
                : "PLACE ORDER"}
            </button>

            <button
              type="button"
              onClick={() => navigate("/checkout")}
              style={{
                marginTop: 10,
                width: "100%",
                padding: "12px 16px",
                borderRadius: 10,
                cursor: "pointer",
              }}
            >
              BACK TO CHECKOUT
            </button>
          </aside>
        </div>
      </div>
    </div>
  );
}