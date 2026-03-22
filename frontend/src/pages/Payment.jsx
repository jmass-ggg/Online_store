import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_BASE_URL, apiFetch } from "../api";
import "./Payment.css";

const CHECKOUT_CTX_KEY = "checkout_context";
const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

const PAYMENT_METHODS = {
  ESEWA: "ESEWA",
  COD: "CASH_ON_DELIVERY",
};

const TAB_KEYS = {
  CARD: "CARD",
  ESEWA: "ESEWA",
  KHALTI: "KHALTI",
  COD: "COD",
};

const PAYMENT_TABS = [
  {
    key: TAB_KEYS.CARD,
    title: "Credit / Debit Card",
    subtitle: "Coming soon",
    image: null,
    emoji: "💳",
    enabled: false,
  },
  {
    key: TAB_KEYS.ESEWA,
    title: "eSewa Wallet",
    subtitle: "Fast online payment",
    image: "/eswea.png",
    emoji: null,
    enabled: true,
  },
  {
    key: TAB_KEYS.KHALTI,
    title: "Khalti by IME",
    subtitle: "Coming soon",
    image: "/ime.png",
    emoji: null,
    enabled: false,
  },
  {
    key: TAB_KEYS.COD,
    title: "Cash on Delivery",
    subtitle: "Pay on arrival",
    image: "/cash_delivery.png",
    emoji: null,
    enabled: true,
  },
];

function safeParse(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function toId(value) {
  return String(value ?? "").trim();
}

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function money(n) {
  return `Rs. ${toNumber(n).toLocaleString("en-NP", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatApiError(err) {
  const detail = err?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => {
        const field = Array.isArray(d?.loc) ? d.loc[d.loc.length - 1] : "field";
        return `${field}: ${d?.msg || "Invalid value"}`;
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

function normalizeCheckoutContext(parsed) {
  const items = Array.isArray(parsed?.items) ? parsed.items : [];

  const normalizedItems = items
    .map((item, index) => ({
      key: `${toId(item?.variant_id ?? item?.id)}_${index}`,
      variant_id: toId(item?.variant_id ?? item?.variantId ?? item?.id),
      quantity: Math.max(1, toNumber(item?.quantity, 1)),
      price: toNumber(item?.price, 0),
      product_name: String(item?.product_name || "").trim(),
      size: String(item?.size || "").trim(),
      color: String(item?.color || "").trim(),
      image_url: String(item?.image_url || "").trim(),
    }))
    .filter((item) => item.variant_id);

  const totals = {
    itemsCount:
      toNumber(parsed?.totals?.itemsCount) ||
      normalizedItems.reduce((sum, item) => sum + item.quantity, 0),
    itemsTotal:
      toNumber(parsed?.totals?.itemsTotal) ||
      normalizedItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
    deliveryFee:
      parsed?.totals?.deliveryFee != null
        ? toNumber(parsed.totals.deliveryFee)
        : normalizedItems.length > 0
        ? 100
        : 0,
  };

  totals.total =
    parsed?.totals?.total != null
      ? toNumber(parsed.totals.total)
      : totals.itemsTotal + totals.deliveryFee;

  return {
    mode: String(parsed?.mode || "BUY_NOW").toUpperCase(),
    address_id: toId(parsed?.address_id ?? parsed?.address?.id),
    address: parsed?.address || null,
    items: normalizedItems,
    totals,
  };
}

function getMethodDetails(activeTab) {
  if (activeTab === TAB_KEYS.ESEWA) {
    return {
      title: "Pay with eSewa",
      subtitle: "Fast and secure wallet payment",
      image: "/eswea.png",
      emoji: null,
      intro:
        "Your order will be created first, then you will be redirected to eSewa to complete the payment securely.",
      points: [
        "Click the payment button below.",
        "Your order will be created with eSewa as the selected payment method.",
        "You will be redirected to eSewa to complete payment.",
      ],
      cta: "PROCEED TO ESEWA",
      enabled: true,
    };
  }

  if (activeTab === TAB_KEYS.COD) {
    return {
      title: "Cash on Delivery",
      subtitle: "Pay when your order arrives",
      image: "/cash_delivery.png",
      emoji: null,
      intro:
        "Place your order now and pay in cash when the package is delivered to your address.",
      points: [
        "Click the place order button below.",
        "Your order will be confirmed with Cash on Delivery.",
        "Please keep the payment amount ready at delivery time.",
      ],
      cta: "PLACE ORDER",
      enabled: true,
    };
  }

  if (activeTab === TAB_KEYS.CARD) {
    return {
      title: "Credit / Debit Card",
      subtitle: "This method is not connected yet",
      image: null,
      emoji: "💳",
      intro:
        "Card payments are shown in the interface, but the gateway integration has not been completed yet.",
      points: [
        "Use eSewa for instant online payment.",
        "Use Cash on Delivery if you want to pay at arrival.",
      ],
      cta: "NOT CONNECTED YET",
      enabled: false,
    };
  }

  return {
    title: "Khalti by IME",
    subtitle: "This method is not connected yet",
    image: "/ime.png",
    emoji: null,
    intro:
      "Khalti / IME support is visible in the interface, but backend integration is still pending.",
    points: [
      "Once the gateway is integrated, this method can be enabled.",
      "For now, use eSewa or Cash on Delivery.",
    ],
    cta: "NOT CONNECTED YET",
    enabled: false,
  };
}

function SuccessView({ successData }) {
  const navigate = useNavigate();

  return (
    <div className="payment-state-card success">
      <div className="payment-state-badge success">Success</div>
      <h2 className="payment-state-title">Order placed successfully</h2>
      <p className="payment-state-text">
        Your order has been created and is now waiting for fulfillment.
      </p>

      <div className="success-grid">
        <div className="success-row">
          <span>Order ID</span>
          <strong>{successData?.order_id || successData?.id || "-"}</strong>
        </div>
        <div className="success-row">
          <span>Status</span>
          <strong>{successData?.status || "-"}</strong>
        </div>
        <div className="success-row">
          <span>Total</span>
          <strong>{money(successData?.total_price || 0)}</strong>
        </div>
        <div className="success-row">
          <span>Payment Method</span>
          <strong>Cash on Delivery</strong>
        </div>
      </div>

      <div className="payment-state-actions">
        <button
          type="button"
          className="primary-btn"
          onClick={() => navigate("/products")}
        >
          Continue Shopping
        </button>

        <Link className="ghost-link" to="/">
          Back to Home
        </Link>
      </div>
    </div>
  );
}

export default function Payment() {
  const navigate = useNavigate();

  const [checkoutCtx, setCheckoutCtx] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState(PAYMENT_METHODS.ESEWA);
  const [activeTab, setActiveTab] = useState(TAB_KEYS.ESEWA);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(CHECKOUT_CTX_KEY);
    const parsed = safeParse(raw);

    if (!parsed) {
      setError("Checkout data is missing. Please go back to checkout.");
      return;
    }

    const normalized = normalizeCheckoutContext(parsed);

    if (!normalized.address_id || normalized.items.length === 0) {
      setError("Checkout data is incomplete. Please go back to checkout.");
      return;
    }

    setCheckoutCtx(normalized);
  }, []);

  const totals = useMemo(() => checkoutCtx?.totals || {}, [checkoutCtx]);

  const activeTabMeta = useMemo(() => {
    return PAYMENT_TABS.find((tab) => tab.key === activeTab) || PAYMENT_TABS[1];
  }, [activeTab]);

  const detail = useMemo(() => getMethodDetails(activeTab), [activeTab]);

  const primaryButtonLabel = useMemo(() => {
    if (!detail.enabled) return detail.cta;
    return placingOrder ? "PROCESSING..." : detail.cta;
  }, [detail, placingOrder]);

  function handleSelectTab(tab) {
    setError("");
    setActiveTab(tab.key);

    if (!tab.enabled) return;

    if (tab.key === TAB_KEYS.ESEWA) {
      setPaymentMethod(PAYMENT_METHODS.ESEWA);
    } else if (tab.key === TAB_KEYS.COD) {
      setPaymentMethod(PAYMENT_METHODS.COD);
    }
  }

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

    if (activeTab !== TAB_KEYS.ESEWA && activeTab !== TAB_KEYS.COD) {
      setError(`${activeTabMeta.title} is not connected yet.`);
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

        const payload = {
          address_id: checkoutCtx.address_id,
          variant_id: item.variant_id,
          quantity: Number(item.quantity),
          payment_method: paymentMethod,
        };

        console.log("BUY_NOW payload:", payload);

        res = await apiFetch("/orders/buy-now", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      } else {
        const payload = {
          address_id: checkoutCtx.address_id,
          payment_method: paymentMethod,
        };

        console.log("CART payload:", payload);

        res = await apiFetch("/orders/order", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }

      if (paymentMethod === PAYMENT_METHODS.ESEWA) {
        const redirectUrl =
          res?.payment_redirect_url ||
          res?.paymentUrl ||
          res?.redirect_url ||
          res?.redirectUrl;

        if (!redirectUrl) {
          throw new Error("Backend did not return eSewa redirect URL.");
        }

        window.location.assign(buildBackendUrl(redirectUrl));
        return;
      }

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
      <div className="payment-shell">
        <main className="payment-container">
          <SuccessView successData={successData} />
        </main>
      </div>
    );
  }

  if (!checkoutCtx) {
    return (
      <div className="payment-shell">
        <main className="payment-container">
          <div className="payment-state-card">
            <div className="payment-state-badge">Payment</div>
            <h2 className="payment-state-title">Checkout data missing</h2>
            <p className="payment-state-text">
              {error || "Please return to checkout and try again."}
            </p>

            <div className="payment-state-actions">
              <button
                type="button"
                className="primary-btn"
                onClick={() => navigate("/checkout")}
              >
                Back to Checkout
              </button>

              <Link className="ghost-link" to="/">
                Home
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="payment-shell">
      <main className="payment-container">
        <section className="payment-hero">
          <div>
            <div className="payment-kicker">Checkout</div>
            <h1 className="payment-title">Select Payment Method</h1>
            <p className="payment-subtitle">
              Choose how you want to complete your order.
            </p>
          </div>

          <button
            type="button"
            className="back-btn"
            onClick={() =>
              navigate(
                checkoutCtx.mode === "BUY_NOW" ? "/checkout?mode=buy_now" : "/checkout"
              )
            }
          >
            ← Back to Checkout
          </button>
        </section>

        <section className="payment-layout">
          <div className="payment-left-col">
            <div className="payment-panel">
              <div className="payment-method-tabs">
                {PAYMENT_TABS.map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    className={`payment-method-tab ${
                      activeTab === tab.key ? "active" : ""
                    } ${!tab.enabled ? "is-disabled" : ""}`}
                    onClick={() => handleSelectTab(tab)}
                  >
                    <div className="payment-method-iconWrap">
                      {tab.image ? (
                        <img
                          src={tab.image}
                          alt={tab.title}
                          className="method-icon"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <div className="method-icon-emoji">{tab.emoji}</div>
                      )}
                    </div>

                    <div className="method-text">
                      <h4>{tab.title}</h4>
                      <p>{tab.subtitle}</p>
                    </div>

                    {activeTab === tab.key ? <span className="method-active-dot" /> : null}
                  </button>
                ))}
              </div>

              <div className="payment-detail-panel">
                <div className="detail-head">
                  {detail.image ? (
                    <img
                      src={detail.image}
                      alt={detail.title}
                      className="detail-brand-logo"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="detail-icon-box">{detail.emoji}</div>
                  )}

                  <div>
                    <h3>{detail.title}</h3>
                    <p>{detail.subtitle}</p>
                  </div>
                </div>

                <p className="detail-intro">{detail.intro}</p>

                <ol className="detail-list ordered">
                  {detail.points.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ol>

                <div className="detail-footer">
                  <button
                    type="button"
                    className={`primary-btn detail-btn ${
                      !detail.enabled ? "disabled" : ""
                    }`}
                    onClick={handlePlaceOrder}
                    disabled={placingOrder || !detail.enabled}
                  >
                    {primaryButtonLabel}
                  </button>

                  <div className="detail-trust">
                    <span className="detail-trust-dot" />
                    Secure checkout experience
                  </div>
                </div>

                {error ? <div className="payment-inline-error">{error}</div> : null}
              </div>
            </div>
          </div>

          <aside className="payment-summary-card">
            <div className="summary-top">
              <h3>Order Summary</h3>
              <span className="summary-chip">{checkoutCtx.mode}</span>
            </div>

            <div className="summary-items">
              {checkoutCtx.items.map((item, index) => (
                <div
                  key={`${item.variant_id}_${index}`}
                  className="summary-item-row"
                >
                  <div className="summary-item-info">
                    <div className="summary-item-name">{item.product_name}</div>
                    <div className="summary-item-meta">
                      {item.size ? `Size: ${item.size} · ` : ""}
                      {item.color ? `Color: ${item.color} · ` : ""}
                      Qty: {item.quantity}
                    </div>
                  </div>

                  <div className="summary-item-price">
                    {money(Number(item.price) * Number(item.quantity))}
                  </div>
                </div>
              ))}
            </div>

            <div className="summary-divider" />

            <div className="summary-line">
              <span>Items</span>
              <span>{totals.itemsCount || 0}</span>
            </div>

            <div className="summary-line">
              <span>Items Total</span>
              <span>{money(totals.itemsTotal || 0)}</span>
            </div>

            <div className="summary-line">
              <span>Delivery Fee</span>
              <span>{money(totals.deliveryFee || 0)}</span>
            </div>

            <div className="summary-divider" />

            <div className="summary-line total">
              <span>Total</span>
              <span>{money(totals.total || 0)}</span>
            </div>

            <button
              type="button"
              className="summary-main-btn"
              onClick={handlePlaceOrder}
              disabled={placingOrder || !detail.enabled}
            >
              {primaryButtonLabel}
            </button>

            <div className="summary-note">
              By proceeding, you confirm that your shipping and payment details
              are correct.
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}