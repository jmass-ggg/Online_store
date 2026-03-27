import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_BASE_URL, apiFetch } from "../api";
import "./Payment.css";

const CHECKOUT_CTX_KEY = "checkout_context";
const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

const CHECKOUT_PREVIEW_ENDPOINT = "/checkout/checkout";
const BUY_NOW_ENDPOINT = "/orders/buy-now";
const CART_ORDER_ENDPOINT = "/orders/order";

const TAB_KEYS = {
  ESEWA: "ESEWA",
  COD: "COD",
  CARD: "CARD",
  KHALTI: "KHALTI",
};

const PAYMENT_METHODS = {
  ESEWA: "ESEWA",
  COD: "CASH_ON_DELIVERY",
};

const PAYMENT_TABS = [
  {
    key: TAB_KEYS.ESEWA,
    title: "eSewa Wallet",
    subtitle: "Fast online payment",
    image: "/eswea.png",
    emoji: "💚",
    enabled: true,
  },
  {
    key: TAB_KEYS.COD,
    title: "Cash on Delivery",
    subtitle: "Pay when order arrives",
    image: "/cash_delivery.png",
    emoji: "📦",
    enabled: true,
  },
  {
    key: TAB_KEYS.CARD,
    title: "Credit / Debit Card",
    subtitle: "Coming soon",
    image: null,
    emoji: "💳",
    enabled: false,
  },
  {
    key: TAB_KEYS.KHALTI,
    title: "Khalti by IME",
    subtitle: "Coming soon",
    image: "/ime.png",
    emoji: "💜",
    enabled: false,
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

function money(value) {
  return `Rs. ${toNumber(value).toLocaleString("en-NP", {
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
      .map((item) => {
        const field = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : "field";
        return `${field}: ${item?.msg || "Invalid value"}`;
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

function cleanupAfterOrder(mode) {
  sessionStorage.removeItem(CHECKOUT_CTX_KEY);

  if (mode === "BUY_NOW") {
    localStorage.removeItem(BUY_NOW_KEY);
    window.dispatchEvent(new Event("buy_now:updated"));
    return;
  }

  localStorage.removeItem(CART_KEY);
  window.dispatchEvent(new Event("cart:updated"));
}

function normalizeSeed(parsed) {
  const mode = String(parsed?.mode || "BUY_NOW").toUpperCase();

  if (mode === "BUY_NOW") {
    return {
      mode: "BUY_NOW",
      address_id: toId(parsed?.address_id),
      variant_id: toId(parsed?.variant_id),
      quantity: Math.max(1, toNumber(parsed?.quantity, 1)),
      checkout: parsed?.checkout || null,
      items: [],
    };
  }

  const items = Array.isArray(parsed?.items) ? parsed.items : [];

  return {
    mode: "CART",
    address_id: toId(parsed?.address_id),
    variant_id: "",
    quantity: 0,
    checkout: parsed?.checkout || null,
    items: items
      .map((item, index) => ({
        key: `${toId(item?.variant_id ?? item?.id)}_${index}`,
        variant_id: toId(item?.variant_id ?? item?.id),
        quantity: Math.max(1, toNumber(item?.quantity, 1)),
        price: toNumber(item?.price, 0),
        product_name: String(item?.product_name || "").trim(),
        product_category: String(item?.product_category || "").trim(),
        size: String(item?.size || "").trim(),
        color: String(item?.color || "").trim(),
        image_url: String(item?.image_url || "").trim(),
      }))
      .filter((item) => item.variant_id),
  };
}

function buildBuyNowPreview(seed, preview) {
  const quantity = Math.max(1, toNumber(seed?.quantity, 1));

  return {
    mode: "BUY_NOW",
    seller_id: preview?.seller_id || "",
    items: [
      {
        key: `buy_now_${toId(preview?.variant?.id || seed?.variant_id)}`,
        variant_id: toId(preview?.variant?.id || seed?.variant_id),
        quantity,
        price: toNumber(preview?.unit_price, preview?.variant?.price),
        product_name: preview?.product?.product_name || "Selected Product",
        product_category: preview?.product?.product_category || "",
        size: preview?.variant?.size || "",
        color: preview?.variant?.color || "",
        image_url: preview?.product?.image_url || "",
      },
    ],
    totals: {
      itemsCount: quantity,
      itemsTotal: toNumber(preview?.items_subtotal, 0),
      deliveryFee: toNumber(preview?.delivery_charge, 0),
      total: toNumber(preview?.grand_total, 0),
    },
  };
}

function buildCartPreview(seed) {
  const items = Array.isArray(seed?.items) ? seed.items : [];
  const itemsCount = items.reduce((sum, item) => sum + Math.max(1, toNumber(item.quantity, 1)), 0);
  const itemsTotal = items.reduce(
    (sum, item) => sum + toNumber(item.price, 0) * Math.max(1, toNumber(item.quantity, 1)),
    0
  );

  return {
    mode: "CART",
    items,
    totals: {
      itemsCount,
      itemsTotal,
      deliveryFee: 0,
      total: itemsTotal,
    },
  };
}

function getMethodMeta(tabKey) {
  if (tabKey === TAB_KEYS.ESEWA) {
    return {
      title: "Pay with eSewa",
      subtitle: "Fast and secure wallet payment",
      intro:
        "Your order will be created first, then you will be redirected to eSewa to complete payment securely.",
      points: [
        "Click the payment button below.",
        "Order will be created with eSewa as selected payment method.",
        "You will be redirected to eSewa to complete the payment.",
      ],
      cta: "Proceed to eSewa",
      enabled: true,
      paymentMethod: PAYMENT_METHODS.ESEWA,
      image: "/eswea.png",
      emoji: "💚",
    };
  }

  if (tabKey === TAB_KEYS.COD) {
    return {
      title: "Cash on Delivery",
      subtitle: "Pay when your order arrives",
      intro: "Place your order now and pay in cash at the time of delivery.",
      points: [
        "Click the place order button below.",
        "Your order will be confirmed with Cash on Delivery.",
        "Please keep the payable amount ready on delivery.",
      ],
      cta: "Place Order",
      enabled: true,
      paymentMethod: PAYMENT_METHODS.COD,
      image: "/cash_delivery.png",
      emoji: "📦",
    };
  }

  if (tabKey === TAB_KEYS.CARD) {
    return {
      title: "Credit / Debit Card",
      subtitle: "This payment method is not connected yet",
      intro: "Card payment is visible in the UI, but backend integration is not completed yet.",
      points: [
        "Use eSewa for online payment.",
        "Use Cash on Delivery if you want to pay later.",
      ],
      cta: "Coming Soon",
      enabled: false,
      paymentMethod: null,
      image: null,
      emoji: "💳",
    };
  }

  return {
    title: "Khalti by IME",
    subtitle: "This payment method is not connected yet",
    intro: "Khalti / IME is shown in the UI, but backend integration is still pending.",
    points: [
      "Use eSewa for instant online payment.",
      "Use Cash on Delivery as an alternative.",
    ],
    cta: "Coming Soon",
    enabled: false,
    paymentMethod: null,
    image: "/ime.png",
    emoji: "💜",
  };
}

function SummaryItemCard({ item }) {
  const imageUrl = item?.image_url
    ? /^https?:\/\//i.test(item.image_url)
      ? item.image_url
      : buildBackendUrl(item.image_url)
    : "";

  return (
    <div className="payment-summary-item">
      <div className="payment-summary-thumbWrap">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={item.product_name || "Product"}
            className="payment-summary-thumb"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="payment-summary-thumbFallback">
            {(item.product_name || "P").slice(0, 1).toUpperCase()}
          </div>
        )}
      </div>

      <div className="payment-summary-itemBody">
        <div className="payment-summary-itemTop">
          <h4>{item.product_name || `Variant ${item.variant_id}`}</h4>
          <strong>{money(toNumber(item.price, 0) * toNumber(item.quantity, 1))}</strong>
        </div>

        <div className="payment-summary-itemMeta">
          {item.product_category ? <span>{item.product_category}</span> : null}
          {item.size ? <span>Size: {item.size}</span> : null}
          {item.color ? <span>Color: {item.color}</span> : null}
          <span>Qty: {item.quantity}</span>
        </div>
      </div>
    </div>
  );
}

function SuccessView({ successData }) {
  const navigate = useNavigate();

  return (
    <div className="payment-stateCard payment-stateCard--success">
      <div className="payment-stateIcon">✓</div>
      <div className="payment-stateBadge">Success</div>
      <h2>Order placed successfully</h2>
      <p>Your order has been created and is now waiting for fulfillment.</p>

      <div className="payment-successGrid">
        <div className="payment-successRow">
          <span>Order ID</span>
          <strong>{successData?.order_id || successData?.id || "-"}</strong>
        </div>
        <div className="payment-successRow">
          <span>Status</span>
          <strong>{successData?.status || "-"}</strong>
        </div>
        <div className="payment-successRow">
          <span>Total</span>
          <strong>{money(successData?.total_price || 0)}</strong>
        </div>
        <div className="payment-successRow">
          <span>Payment Method</span>
          <strong>{successData?.payment_method || PAYMENT_METHODS.COD}</strong>
        </div>
      </div>

      <div className="payment-stateActions">
        <button type="button" className="payment-primaryBtn" onClick={() => navigate("/products")}>
          Continue Shopping
        </button>
        <Link to="/" className="payment-ghostBtn">
          Back to Home
        </Link>
      </div>
    </div>
  );
}

export default function Payment() {
  const navigate = useNavigate();

  const [checkoutSeed, setCheckoutSeed] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [activeTab, setActiveTab] = useState(TAB_KEYS.ESEWA);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [error, setError] = useState("");
  const [successData, setSuccessData] = useState(null);

  useEffect(() => {
    const parsed = safeParse(sessionStorage.getItem(CHECKOUT_CTX_KEY));

    if (!parsed) {
      setError("Checkout data is missing. Please go back to checkout.");
      setLoadingPreview(false);
      return;
    }

    const normalized = normalizeSeed(parsed);
    setCheckoutSeed(normalized);

    async function loadPreview() {
      setError("");
      setLoadingPreview(true);

      try {
        if (normalized.mode === "BUY_NOW") {
          if (!normalized.address_id || !normalized.variant_id) {
            throw new Error("Checkout data is incomplete. Please go back to checkout.");
          }

          const preview = await apiFetch(CHECKOUT_PREVIEW_ENDPOINT, {
            method: "POST",
            body: JSON.stringify({
              address_id: normalized.address_id,
              variant_id: normalized.variant_id,
              quantity: normalized.quantity,
            }),
          });

          setPreviewData(buildBuyNowPreview(normalized, preview));
        } else {
          if (!normalized.address_id || normalized.items.length === 0) {
            throw new Error("Checkout data is incomplete. Please go back to checkout.");
          }

          setPreviewData(buildCartPreview(normalized));
        }
      } catch (e) {
        setError(formatApiError(e));
      } finally {
        setLoadingPreview(false);
      }
    }

    loadPreview();
  }, []);

  const methodMeta = useMemo(() => getMethodMeta(activeTab), [activeTab]);
  const totals = useMemo(
    () => previewData?.totals || { itemsCount: 0, itemsTotal: 0, deliveryFee: 0, total: 0 },
    [previewData]
  );

  const primaryButtonLabel = useMemo(() => {
    if (!methodMeta.enabled) return methodMeta.cta;
    return placingOrder ? "Processing..." : methodMeta.cta;
  }, [methodMeta, placingOrder]);

  function handleSelectTab(tab) {
    setError("");
    setActiveTab(tab.key);
  }

  async function handlePlaceOrder() {
    setError("");

    if (!checkoutSeed || !previewData) {
      setError("Checkout preview is missing.");
      return;
    }

    if (!checkoutSeed.address_id) {
      setError("Address is missing.");
      return;
    }

    if (!methodMeta.enabled || !methodMeta.paymentMethod) {
      setError(`${methodMeta.title} is not connected yet.`);
      return;
    }

    setPlacingOrder(true);

    try {
      let response;

      if (checkoutSeed.mode === "BUY_NOW") {
        response = await apiFetch(BUY_NOW_ENDPOINT, {
          method: "POST",
          body: JSON.stringify({
            address_id: checkoutSeed.address_id,
            variant_id: checkoutSeed.variant_id,
            quantity: checkoutSeed.quantity,
            payment_method: methodMeta.paymentMethod,
          }),
        });
      } else {
        response = await apiFetch(CART_ORDER_ENDPOINT, {
          method: "POST",
          body: JSON.stringify({
            address_id: checkoutSeed.address_id,
            payment_method: methodMeta.paymentMethod,
          }),
        });
      }

      if (methodMeta.paymentMethod === PAYMENT_METHODS.ESEWA) {
        const redirectUrl =
          response?.payment_redirect_url ||
          response?.paymentUrl ||
          response?.redirect_url ||
          response?.redirectUrl;

        if (!redirectUrl) {
          throw new Error("Backend did not return eSewa redirect URL.");
        }

        window.location.assign(buildBackendUrl(redirectUrl));
        return;
      }

      cleanupAfterOrder(checkoutSeed.mode);
      setSuccessData(response);
    } catch (e) {
      setError(formatApiError(e));
    } finally {
      setPlacingOrder(false);
    }
  }

  if (successData) {
    return (
      <div className="payment-shell">
        <main className="payment-container payment-container--single">
          <SuccessView successData={successData} />
        </main>
      </div>
    );
  }

  if (loadingPreview) {
    return (
      <div className="payment-shell">
        <main className="payment-container payment-container--single">
          <div className="payment-stateCard">
            <div className="payment-stateBadge">Payment</div>
            <h2>Loading checkout details</h2>
            <p>Fetching your items, subtotal, delivery fee, and grand total.</p>
          </div>
        </main>
      </div>
    );
  }

  if (!checkoutSeed || !previewData) {
    return (
      <div className="payment-shell">
        <main className="payment-container payment-container--single">
          <div className="payment-stateCard">
            <div className="payment-stateBadge">Payment</div>
            <h2>Checkout data missing</h2>
            <p>{error || "Please return to checkout and try again."}</p>

            <div className="payment-stateActions">
              <button
                type="button"
                className="payment-primaryBtn"
                onClick={() => navigate("/checkout")}
              >
                Back to Checkout
              </button>

              <Link to="/" className="payment-ghostBtn">
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
          <div className="payment-heroText">
            <div className="payment-kicker">Checkout</div>
            <h1 className="payment-title">Select Payment Method</h1>
            <p className="payment-subtitle">
              Review your order summary and choose how you want to complete payment.
            </p>
          </div>

          <button
            type="button"
            className="payment-backBtn"
            onClick={() =>
              navigate(checkoutSeed.mode === "BUY_NOW" ? "/checkout?mode=buy_now" : "/checkout")
            }
          >
            ← Back to Checkout
          </button>
        </section>

        <section className="payment-layout">
          <div className="payment-left">
            <div className="payment-card">
              <div className="payment-tabGrid">
                {PAYMENT_TABS.map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    className={[
                      "payment-tab",
                      activeTab === tab.key ? "is-active" : "",
                      !tab.enabled ? "is-disabled" : "",
                    ].join(" ")}
                    onClick={() => handleSelectTab(tab)}
                  >
                    <div className="payment-tabIcon">
                      {tab.image ? (
                        <img
                          src={tab.image}
                          alt={tab.title}
                          className="payment-tabIconImage"
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                          }}
                        />
                      ) : (
                        <span>{tab.emoji}</span>
                      )}
                    </div>

                    <div className="payment-tabText">
                      <strong>{tab.title}</strong>
                      <span>{tab.subtitle}</span>
                    </div>

                    {activeTab === tab.key ? <span className="payment-tabDot" /> : null}
                  </button>
                ))}
              </div>

              <div className="payment-methodPanel">
                <div className="payment-methodHead">
                  <div className="payment-methodBrand">
                    {methodMeta.image ? (
                      <img
                        src={methodMeta.image}
                        alt={methodMeta.title}
                        className="payment-methodBrandImage"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    ) : (
                      <div className="payment-methodBrandFallback">{methodMeta.emoji}</div>
                    )}
                  </div>

                  <div>
                    <h3>{methodMeta.title}</h3>
                    <p>{methodMeta.subtitle}</p>
                  </div>
                </div>

                <p className="payment-methodIntro">{methodMeta.intro}</p>

                <ol className="payment-steps">
                  {methodMeta.points.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ol>

                {error ? <div className="payment-errorBox">{error}</div> : null}

                <div className="payment-methodFooter">
                  <button
                    type="button"
                    className={`payment-primaryBtn ${!methodMeta.enabled ? "is-disabled" : ""}`}
                    onClick={handlePlaceOrder}
                    disabled={placingOrder || !methodMeta.enabled}
                  >
                    {primaryButtonLabel}
                  </button>

                  <div className="payment-trustText">
                    <span className="payment-trustDot" />
                    Secure checkout experience
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside className="payment-right">
            <div className="payment-summaryCard">
              <div className="payment-summaryTop">
                <h3>Order Summary</h3>
              </div>

              
              <div className="payment-summaryBreakdown">
                <div className="payment-summaryLine">
                  <span>Items</span>
                  <strong>{totals.itemsCount}</strong>
                </div>

                <div className="payment-summaryLine">
                  <span>Items Total</span>
                  <strong>{money(totals.itemsTotal)}</strong>
                </div>

                <div className="payment-summaryLine">
                  <span>Delivery Fee</span>
                  <strong>{money(totals.deliveryFee)}</strong>
                </div>

                <div className="payment-summaryDivider" />

                <div className="payment-summaryLine is-total">
                  <span>Total</span>
                  <strong>{money(totals.total)}</strong>
                </div>
              </div>

              <button
                type="button"
                className="payment-summaryBtn"
                onClick={handlePlaceOrder}
                disabled={placingOrder || !methodMeta.enabled}
              >
                {primaryButtonLabel}
              </button>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}