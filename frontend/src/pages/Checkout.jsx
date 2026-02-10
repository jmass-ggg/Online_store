// Checkout.jsx
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import "./Checkout.css";
import { apiFetch } from "../api";

const CART_KEY = "cart_items";
const BUY_NOW_KEY = "buy_now_item";

function money(n) {
  const v = Number(n || 0);
  return v.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

// ---------------- Local helpers (display enrichment) ----------------
function readLocalCartArray() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY) || "[]");
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function readLocalMapByVariantId() {
  const arr = readLocalCartArray();
  const map = new Map();
  for (const x of arr) {
    const vid = Number(x?.variant_id ?? x?.variantId ?? x?.id);
    if (Number.isFinite(vid)) map.set(vid, x);
  }
  return map;
}

// ---------------- Buy Now helpers ----------------
function readBuyNow() {
  try {
    const raw = JSON.parse(localStorage.getItem(BUY_NOW_KEY) || "null");
    if (!raw?.item?.variant_id) return null;
    return raw;
  } catch {
    return null;
  }
}

// ---------------- Error formatting (Fixes [object Object]) ----------------
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

/**
 * Nepal address data (simple version).
 * Expand anytime.
 * lat/lng are province center points (approx).
 */
const NEPAL = {
  provinces: [
    {
      name: "Koshi Province",
      lat: 26.67,
      lng: 87.27,
      cities: [
        { name: "Biratnagar", zones: ["Main Road", "Traffic Chowk", "Bargachhi"] },
        { name: "Dharan", zones: ["Bhanuchowk", "Putali Line", "Siddha Kali"] },
      ],
    },
    {
      name: "Madhesh Province",
      lat: 26.72,
      lng: 85.92,
      cities: [
        { name: "Janakpur", zones: ["Ramanand Chowk", "Mills Area", "Kuwa"] },
        { name: "Birgunj", zones: ["Ghantaghar", "Adarshanagar", "Dryport"] },
      ],
    },
    {
      name: "Bagmati Province",
      lat: 27.72,
      lng: 85.32,
      cities: [
        { name: "Kathmandu", zones: ["New Baneshwor", "Koteshwor", "Kalanki", "Boudha"] },
        { name: "Lalitpur", zones: ["Jawalakhel", "Patan", "Satdobato"] },
        { name: "Bhaktapur", zones: ["Suryabinayak", "Thimi", "Durbar Square"] },
      ],
    },
    {
      name: "Gandaki Province",
      lat: 28.21,
      lng: 83.99,
      cities: [
        { name: "Pokhara", zones: ["Lakeside", "Chipledhunga", "Bagar"] },
        {
          name: "Beni",
          zones: ["Birendra Chowk", "Campus Chowk", "Hospital Chowk", "New Road Area"],
        },
      ],
    },
    {
      name: "Lumbini Province",
      lat: 27.53,
      lng: 83.45,
      cities: [
        { name: "Butwal", zones: ["Traffic Chowk", "Golpark", "Kalikanagar"] },
        { name: "Bhairahawa", zones: ["Siddharthnagar", "Buspark", "Airport Area"] },
      ],
    },
    {
      name: "Karnali Province",
      lat: 28.6,
      lng: 81.6,
      cities: [{ name: "Birendranagar", zones: ["Yarichowk", "Mangalgadhi", "Airport Area"] }],
    },
    {
      name: "Sudurpashchim Province",
      lat: 28.95,
      lng: 80.18,
      cities: [{ name: "Dhangadhi", zones: ["Campus Road", "Hasanpur", "Chatakpur"] }],
    },
  ],
};

// small random “jitter” so not all users same exact coordinate
function jitterCoord(base, maxDelta = 0.03) {
  const r = (Math.random() * 2 - 1) * maxDelta; // -delta..+delta
  return Number((base + r).toFixed(6));
}

export default function Checkout() {
  const location = useLocation();
  const isBuyNowMode = new URLSearchParams(location.search).get("mode") === "buy_now";

  // ---------------- Form ----------------
  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("+977");
  const [phone, setPhone] = useState("");

  const [province, setProvince] = useState("");
  const [city, setCity] = useState("");
  const [zone, setZone] = useState("");
  const [landmark, setLandmark] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [postalCode, setPostalCode] = useState("");

  const [saving, setSaving] = useState(false);
  const [loadingAddress, setLoadingAddress] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [savedAddress, setSavedAddress] = useState(null);

  // ---------------- Order Items ----------------
  const [orderItems, setOrderItems] = useState([]);
  const [loadingOrder, setLoadingOrder] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    const bump = () => setRefreshTick((t) => t + 1);
    window.addEventListener("cart:updated", bump);
    window.addEventListener("storage", bump);
    window.addEventListener("buy_now:updated", bump);
    return () => {
      window.removeEventListener("cart:updated", bump);
      window.removeEventListener("storage", bump);
      window.removeEventListener("buy_now:updated", bump);
    };
  }, []);

  // ---------------- Load address list (GET /addresses/) ----------------
  useEffect(() => {
    let cancelled = false;

    async function loadAddresses() {
      setLoadingAddress(true);
      setErrorMsg("");
      try {
        const list = await apiFetch("/addresses/");
        if (cancelled) return;

        const arr = Array.isArray(list) ? list : [];
        setSavedAddress(arr.length ? arr[0] : null); // newest first from backend
      } catch (e) {
        if (!cancelled) setErrorMsg(formatApiError(e));
      } finally {
        if (!cancelled) setLoadingAddress(false);
      }
    }

    loadAddresses();
    return () => {
      cancelled = true;
    };
  }, [refreshTick]);

  // ---------------- Load items: BUY_NOW or CART ----------------
  useEffect(() => {
    let cancelled = false;

    async function loadOrder() {
      setLoadingOrder(true);
      setErrorMsg("");

      // BUY NOW MODE
      if (isBuyNowMode) {
        const bn = readBuyNow();
        if (!bn) {
          if (!cancelled) setOrderItems([]);
          setLoadingOrder(false);
          return;
        }

        const it = bn.item;
        if (!cancelled) {
          setOrderItems([
            {
              id: `buy_now_${it.variant_id}`,
              variant_id: it.variant_id,
              quantity: it.quantity ?? 1,
              price: it.price ?? 0,
              product_name: it.product_name,
              image_url: it.image_url,
              size: it.size,
            },
          ]);
        }
        setLoadingOrder(false);
        return;
      }

      // CART MODE
      const localMap = readLocalMapByVariantId();
      try {
        const cart = await apiFetch("/cart/me");
        if (cancelled) return;

        const items = Array.isArray(cart?.items) ? cart.items : [];
        const enriched = items.map((it) => {
          const local = localMap.get(Number(it.variant_id));
          return {
            ...it,
            product_name: local?.product_name,
            image_url: local?.image_url,
            size: local?.size,
          };
        });

        setOrderItems(enriched);
      } catch (e) {
        if (!cancelled) {
          setOrderItems([]);
          setErrorMsg(formatApiError(e));
        }
      } finally {
        if (!cancelled) setLoadingOrder(false);
      }
    }

    loadOrder();
    return () => {
      cancelled = true;
    };
  }, [refreshTick, isBuyNowMode]);

  // ---------------- Totals ----------------
  const itemsCount = useMemo(
    () => orderItems.reduce((sum, it) => sum + Number(it.quantity || 0), 0),
    [orderItems]
  );

  const itemsTotal = useMemo(
    () => orderItems.reduce((sum, it) => sum + Number(it.price || 0) * Number(it.quantity || 0), 0),
    [orderItems]
  );

  const deliveryFee = 4.5;
  const total = Math.max(0, itemsTotal + (itemsCount > 0 ? deliveryFee : 0));

  // ---------------- Province/City/Zone derived lists ----------------
  const provinceObj = useMemo(
    () => NEPAL.provinces.find((p) => p.name === province) || null,
    [province]
  );

  const cityOptions = useMemo(() => provinceObj?.cities || [], [provinceObj]);

  const cityObj = useMemo(
    () => cityOptions.find((c) => c.name === city) || null,
    [cityOptions, city]
  );

  const zoneOptions = useMemo(() => cityObj?.zones || [], [cityObj]);

  // reset dependent selects
  useEffect(() => {
    setCity("");
    setZone("");
  }, [province]);

  useEffect(() => {
    setZone("");
  }, [city]);

  // ---------------- Save Address (POST /addresses/) ----------------
  async function saveAddress() {
    setErrorMsg("");

    if (!fullName.trim()) return setErrorMsg("Full name is required");
    if (phone.trim().length < 7) return setErrorMsg("Phone number is too short");
    if (!province) return setErrorMsg("Please select Province / Region");
    if (!city) return setErrorMsg("Please select City");
    if (!zone) return setErrorMsg("Please select Zone");
    if (!addressLine.trim()) return setErrorMsg("Please enter Address");

    const baseLat = provinceObj?.lat ?? 27.7172;
    const baseLng = provinceObj?.lng ?? 85.3240;

    // IMPORTANT: backend requires full_name and phone_number
    const payload = {
      full_name: fullName.trim(),
      phone_number: `${countryCode}${phone.trim()}`, // if backend wants digits only, change to phone.trim()
      region: province,
      line1: addressLine.trim(),
      line2: `${zone}, ${city}${landmark.trim() ? `, ${landmark.trim()}` : ""}`,
      postal_code: postalCode.trim() ? postalCode.trim() : null,
      country: "Nepal",
      latitude: jitterCoord(baseLat, 0.05),
      longitude: jitterCoord(baseLng, 0.05),
      is_default_shipping: true,
      is_default_billing: false,
    };

    setSaving(true);
    try {
      const saved = await apiFetch("/addresses/", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSavedAddress(saved);
      // reload list so UI always matches backend
      setRefreshTick((t) => t + 1);
    } catch (e) {
      setErrorMsg(formatApiError(e));
    } finally {
      setSaving(false);
    }
  }

  // ---------------- Proceed To Pay ----------------
  async function proceedToPay() {
    setErrorMsg("");
    if (!savedAddress) return setErrorMsg("Please save a shipping address to proceed.");
    if (itemsCount <= 0) return setErrorMsg("No items to checkout.");

    try {
      const payload = {
        mode: isBuyNowMode ? "BUY_NOW" : "CART",
        address_id: savedAddress.id,
        items: isBuyNowMode
          ? orderItems.map((x) => ({ variant_id: x.variant_id, quantity: x.quantity }))
          : null,
      };

      const res = await apiFetch("/order/checkout", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (res?.payment_url) window.location.href = res.payment_url;
      else alert("Order created. Implement payment redirect here.");
    } catch (e) {
      setErrorMsg(formatApiError(e));
    }
  }

  const canProceed =
    itemsCount > 0 &&
    fullName.trim().length > 1 &&
    phone.trim().length >= 7 &&
    !!savedAddress;

  return (
    <div className="checkout-page">
      <header className="ck-header">
        <div className="ck-wrap ck-headerRow">
          <div className="ck-brand">
            <span className="ck-brandName">James</span>
          </div>

          <nav className="ck-nav">
            <a href="#">Categories</a>
            <a href="#">Flash Sale</a>
          </nav>

          <div className="ck-search">
            <span className="ck-searchIcon" aria-hidden="true">
              🔎
            </span>
            <input placeholder="Search for products..." />
          </div>

          <div className="ck-actions">
            <button className="ck-iconBtn" aria-label="Cart">
              🛒
            </button>
            <button className="ck-iconBtn" aria-label="Notifications">
              🔔
            </button>
            <button className="ck-avatar" aria-label="Account">
              👤
            </button>
          </div>
        </div>
      </header>

      <main className="ck-wrap ck-main">
        <div className="ck-breadcrumb">
          <Link to="/">Home</Link>
          <span className="ck-sep">›</span>
          <a href="#">Cart</a>
          <span className="ck-sep">›</span>
          <span className="ck-current">Checkout</span>
          {isBuyNowMode && <span style={{ marginLeft: 8, opacity: 0.7 }}>(Buy Now)</span>}
        </div>

        <div className="ck-grid">
          {/* LEFT - ADDRESS */}
          <section className="ck-card ck-left">
            <div className="ck-cardHeader">
              <div className="ck-step">
                <span className="ck-stepDot">1</span>
                <h2 className="ck-h2">Delivery Information</h2>
              </div>
              <div className="ck-stepText">Step 1 of 2</div>
            </div>

            {loadingAddress && (
              <div className="ck-hint" style={{ marginBottom: 10 }}>
                Loading saved addresses…
              </div>
            )}

            {savedAddress && (
              <div className="ship-card">
                <div className="ship-head">
                  <div className="ship-title">Shipping Address</div>
                  <div className="ship-edit">EDIT</div>
                </div>

                <div className="ship-nameRow">
                  <span className="ship-name">
                    {savedAddress.full_name || fullName}
                  </span>
                  <span className="ship-phone">
                    {savedAddress.phone_number || `${countryCode} ${phone}`}
                  </span>
                </div>

                <div className="ship-addrRow">
                  <span className="ship-tag">HOME</span>
                  <span className="ship-addrText">
                    {savedAddress.line1}
                    {savedAddress.line2 ? `, ${savedAddress.line2}` : ""}
                    {savedAddress.region ? `, ${savedAddress.region}` : ""}
                    {savedAddress.postal_code ? `, ${savedAddress.postal_code}` : ""}
                    {savedAddress.country ? `, ${savedAddress.country}` : ""}
                  </span>
                </div>
              </div>
            )}

            {/* FORM */}
            <div className="ck-formGrid">
              <div className="ck-field">
                <label>Full Name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. James Gurung"
                />
              </div>

              <div className="ck-field">
                <label>Phone Number</label>
                <div className="ck-phoneRow">
                  <select
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    aria-label="Country code"
                  >
                    <option value="+977">+977</option>
                  </select>
                  <input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="98XXXXXXXX"
                    inputMode="numeric"
                  />
                </div>
              </div>
            </div>

            <div className="ck-formGrid" style={{ marginTop: 10 }}>
              <div className="ck-field">
                <label>Province / Region</label>
                <select value={province} onChange={(e) => setProvince(e.target.value)}>
                  <option value="">Please choose your province / region</option>
                  {NEPAL.provinces.map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="ck-field">
                <label>City</label>
                <select value={city} onChange={(e) => setCity(e.target.value)} disabled={!province}>
                  <option value="">Please choose your city</option>
                  {cityOptions.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="ck-field">
                <label>Zone</label>
                <select value={zone} onChange={(e) => setZone(e.target.value)} disabled={!city}>
                  <option value="">Please choose your zone</option>
                  {zoneOptions.map((z) => (
                    <option key={z} value={z}>
                      {z}
                    </option>
                  ))}
                </select>
              </div>

              <div className="ck-field">
                <label>Landmark (Optional)</label>
                <input
                  value={landmark}
                  onChange={(e) => setLandmark(e.target.value)}
                  placeholder="e.g. beside train station"
                />
              </div>

              <div className="ck-field ck-fieldFull">
                <label>Address</label>
                <input
                  value={addressLine}
                  onChange={(e) => setAddressLine(e.target.value)}
                  placeholder="Please enter your address"
                />
              </div>

              <div className="ck-field">
                <label>Postal Code (Optional)</label>
                <input
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  placeholder="44600"
                />
              </div>
            </div>

            {errorMsg && <div className="ck-error">{errorMsg}</div>}

            <div className="ck-footerRow">
              <button className="ck-primary" type="button" onClick={saveAddress} disabled={saving}>
                {saving ? "SAVING..." : "SAVE ADDRESS"}
              </button>
            </div>
          </section>

          {/* RIGHT - ORDER DETAIL + PAY */}
          <aside className="ck-card ck-right">
            <h3 className="ck-h3">Order Detail</h3>

            <div className="ck-lines">
              {loadingOrder && (
                <div className="ck-line">
                  <span>Loading items…</span>
                  <span />
                </div>
              )}

              {!loadingOrder && orderItems.length === 0 && (
                <div className="ck-line">
                  <span>No items in {isBuyNowMode ? "buy now" : "cart"}</span>
                  <span />
                </div>
              )}

              {!loadingOrder &&
                orderItems.map((it) => (
                  <div className="ck-line" key={it.id}>
                    <span>
                      {it.product_name ? it.product_name : `Variant #${it.variant_id}`}
                      {it.size ? ` (${it.size})` : ""} × {it.quantity}
                    </span>
                    <span>{money(Number(it.price) * Number(it.quantity))}</span>
                  </div>
                ))}

              <div className="ck-divider" />

              <div className="ck-line">
                <span>
                  Items Total ({itemsCount} item{itemsCount === 1 ? "" : "s"})
                </span>
                <span>{money(itemsTotal)}</span>
              </div>

              <div className="ck-line">
                <span>Delivery Fee</span>
                <span>{money(itemsCount > 0 ? deliveryFee : 0)}</span>
              </div>

              <div className="ck-divider" />

              <div className="ck-totalRow">
                <span className="ck-totalLabel">Total</span>
                <span className="ck-totalValue">{money(itemsCount > 0 ? total : 0)}</span>
              </div>

              <div className="ck-vat">VAT included where applicable</div>
            </div>

            <button className="ck-pay" type="button" disabled={!canProceed} onClick={proceedToPay}>
              PROCEED TO PAY
            </button>

            {!savedAddress && (
              <div className="ck-terms" style={{ marginTop: 12 }}>
                Please <b>save a shipping address</b> to proceed.
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
