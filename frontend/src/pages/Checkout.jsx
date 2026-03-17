import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Checkout.css";
import { apiFetch, joinUrl } from "../api";

const CART_KEY = "cart_items";
const BUY_NOW_KEY = "buy_now_item";
const CHECKOUT_CTX_KEY = "checkout_context";

function money(n) {
  return `Rs. ${Number(n || 0).toLocaleString("en-NP", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
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
    if (Number.isFinite(vid)) {
      map.set(vid, x);
    }
  }

  return map;
}

function readBuyNow() {
  try {
    const raw = JSON.parse(localStorage.getItem(BUY_NOW_KEY) || "null");
    if (!raw?.item?.variant_id) return null;
    return raw;
  } catch {
    return null;
  }
}

function parseLine2(line2) {
  const s = String(line2 || "").trim();
  if (!s) return { zone: "", city: "", landmark: "" };

  const parts = s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

  return {
    zone: parts[0] || "",
    city: parts[1] || "",
    landmark: parts.slice(2).join(", ") || "",
  };
}

function jitterCoord(base, maxDelta = 0.03) {
  const r = (Math.random() * 2 - 1) * maxDelta;
  return Number((base + r).toFixed(6));
}

const NEPAL = {
  provinces: [
    {
      name: "Koshi Province",
      lat: 26.67,
      lng: 87.27,
      cities: [
        {
          name: "Biratnagar",
          zones: ["Main Road", "Traffic Chowk", "Bargachhi"],
        },
        {
          name: "Dharan",
          zones: ["Bhanuchowk", "Putali Line", "Siddha Kali"],
        },
      ],
    },
    {
      name: "Madhesh Province",
      lat: 26.72,
      lng: 85.92,
      cities: [
        {
          name: "Janakpur",
          zones: ["Ramanand Chowk", "Mills Area", "Kuwa"],
        },
        {
          name: "Birgunj",
          zones: ["Ghantaghar", "Adarshanagar", "Dryport"],
        },
      ],
    },
    {
      name: "Bagmati Province",
      lat: 27.72,
      lng: 85.32,
      cities: [
        {
          name: "Kathmandu",
          zones: ["New Baneshwor", "Koteshwor", "Kalanki", "Boudha"],
        },
        {
          name: "Lalitpur",
          zones: ["Jawalakhel", "Patan", "Satdobato"],
        },
        {
          name: "Bhaktapur",
          zones: ["Suryabinayak", "Thimi", "Durbar Square"],
        },
      ],
    },
    {
      name: "Gandaki Province",
      lat: 28.21,
      lng: 83.99,
      cities: [
        {
          name: "Pokhara",
          zones: ["Lakeside", "Chipledhunga", "Bagar"],
        },
        {
          name: "Beni",
          zones: ["Birendra Chowk", "Campus Chowk", "Hospital Chowk"],
        },
      ],
    },
    {
      name: "Lumbini Province",
      lat: 27.53,
      lng: 83.45,
      cities: [
        {
          name: "Butwal",
          zones: ["Traffic Chowk", "Golpark", "Kalikanagar"],
        },
        {
          name: "Bhairahawa",
          zones: ["Siddharthnagar", "Buspark", "Airport Area"],
        },
      ],
    },
    {
      name: "Karnali Province",
      lat: 28.6,
      lng: 81.6,
      cities: [
        {
          name: "Birendranagar",
          zones: ["Yarichowk", "Mangalgadhi", "Airport Area"],
        },
      ],
    },
    {
      name: "Sudurpashchim Province",
      lat: 28.95,
      lng: 80.18,
      cities: [
        {
          name: "Dhangadhi",
          zones: ["Campus Road", "Hasanpur", "Chatakpur"],
        },
      ],
    },
  ],
};

function CheckoutHeader() {
  const navigate = useNavigate();

  return (
    <header className="ck-header">
      <div className="ck-wrap">
        <div className="ck-headerRow">
          <Link to="/" className="ck-brand">
            <span className="ck-brandName">JAMES</span>
          </Link>

          <nav className="ck-nav">
            <Link to="/products">Categories</Link>
            <Link to="/products">Flash Sale</Link>
          </nav>

          <div className="ck-search">
            <span className="ck-searchIcon">🔎</span>
            <input type="text" placeholder="Search for products..." />
          </div>

          <div className="ck-actions">
            <button
              type="button"
              className="ck-iconBtn"
              onClick={() => navigate("/cart")}
              aria-label="Cart"
              title="Cart"
            >
              🛒
            </button>

            <button
              type="button"
              className="ck-iconBtn"
              aria-label="Notifications"
              title="Notifications"
            >
              🔔
            </button>

            <button
              type="button"
              className="ck-avatar"
              onClick={() => navigate("/login")}
              aria-label="Profile"
              title="Profile"
            >
              👤
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();

  const isBuyNowMode =
    new URLSearchParams(location.search).get("mode") === "buy_now";

  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("+977");
  const [phone, setPhone] = useState("");
  const [province, setProvince] = useState("");
  const [city, setCity] = useState("");
  const [zone, setZone] = useState("");
  const [landmark, setLandmark] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [postalCode, setPostalCode] = useState("");

  const [loadingAddress, setLoadingAddress] = useState(false);
  const [loadingOrder, setLoadingOrder] = useState(false);
  const [saving, setSaving] = useState(false);

  const [savedAddress, setSavedAddress] = useState(null);
  const [isEditingAddress, setIsEditingAddress] = useState(false);
  const [orderItems, setOrderItems] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    const bump = () => setRefreshTick((t) => t + 1);

    window.addEventListener("cart:updated", bump);
    window.addEventListener("buy_now:updated", bump);
    window.addEventListener("storage", bump);

    return () => {
      window.removeEventListener("cart:updated", bump);
      window.removeEventListener("buy_now:updated", bump);
      window.removeEventListener("storage", bump);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadAddresses() {
      setLoadingAddress(true);
      setErrorMsg("");

      try {
        const list = await apiFetch("/addresses/");
        if (cancelled) return;

        const arr = Array.isArray(list) ? [...list] : [];
        arr.sort((a, b) => Number(b?.id || 0) - Number(a?.id || 0));

        const newest = arr[0] || null;
        setSavedAddress(newest);
        setIsEditingAddress(!newest);

        if (newest) {
          const pn = String(newest.phone_number || "");

          setFullName(newest.full_name || "");
          setProvince(newest.region || "");
          setAddressLine(newest.line1 || "");
          setPostalCode(newest.postal_code || "");

          if (pn.startsWith("+977")) {
            setCountryCode("+977");
            setPhone(pn.slice(4));
          } else {
            setPhone(pn);
          }

          const parsed = parseLine2(newest.line2);
          setZone(parsed.zone);
          setCity(parsed.city);
          setLandmark(parsed.landmark);
        }
      } catch (e) {
        if (!cancelled) {
          setErrorMsg(formatApiError(e));
        }
      } finally {
        if (!cancelled) {
          setLoadingAddress(false);
        }
      }
    }

    loadAddresses();

    return () => {
      cancelled = true;
    };
  }, [refreshTick]);

  useEffect(() => {
    let cancelled = false;

    async function loadOrder() {
      setLoadingOrder(true);
      setErrorMsg("");

      if (isBuyNowMode) {
        const bn = readBuyNow();

        if (!bn) {
          if (!cancelled) {
            setOrderItems([]);
            setLoadingOrder(false);
          }
          return;
        }

        const it = bn.item;

        if (!cancelled) {
          setOrderItems([
            {
              id: `buy_now_${it.variant_id}`,
              variant_id: Number(it.variant_id),
              quantity: Number(it.quantity ?? 1),
              price: Number(it.price ?? 0),
              product_name: it.product_name,
              image_url: it.image_url,
              size: it.size,
              color: it.color,
            },
          ]);
          setLoadingOrder(false);
        }

        return;
      }

      const localMap = readLocalMapByVariantId();

      try {
        const cart = await apiFetch("/cart/me");
        if (cancelled) return;

        const items = Array.isArray(cart?.items) ? cart.items : [];

        const enriched = items.map((it) => {
          const local = localMap.get(Number(it.variant_id));

          return {
            ...it,
            id: it.id ?? `cart_${it.variant_id}`,
            variant_id: Number(it.variant_id),
            quantity: Number(it.quantity ?? 1),
            price: Number(it.price ?? local?.price ?? 0),
            product_name: local?.product_name || it.product_name,
            image_url: local?.image_url || it.image_url,
            size: local?.size || it.size,
            color: local?.color || it.color,
          };
        });

        setOrderItems(enriched);
      } catch (e) {
        if (!cancelled) {
          setOrderItems([]);
          setErrorMsg(formatApiError(e));
        }
      } finally {
        if (!cancelled) {
          setLoadingOrder(false);
        }
      }
    }

    loadOrder();

    return () => {
      cancelled = true;
    };
  }, [refreshTick, isBuyNowMode]);

  const itemsCount = useMemo(() => {
    return orderItems.reduce((sum, it) => sum + Number(it.quantity || 0), 0);
  }, [orderItems]);

  const itemsTotal = useMemo(() => {
    return orderItems.reduce(
      (sum, it) => sum + Number(it.price || 0) * Number(it.quantity || 0),
      0
    );
  }, [orderItems]);

  const deliveryFee = 100;
  const total = Math.max(0, itemsTotal + (itemsCount > 0 ? deliveryFee : 0));

  const provinceObj = useMemo(() => {
    return NEPAL.provinces.find((p) => p.name === province) || null;
  }, [province]);

  const cityOptions = useMemo(() => provinceObj?.cities || [], [provinceObj]);

  const cityObj = useMemo(() => {
    return cityOptions.find((c) => c.name === city) || null;
  }, [cityOptions, city]);

  const zoneOptions = useMemo(() => cityObj?.zones || [], [cityObj]);

  function handleProvinceChange(value) {
    setProvince(value);
    setCity("");
    setZone("");
  }

  function handleCityChange(value) {
    setCity(value);
    setZone("");
  }

  function startEdit() {
    setErrorMsg("");

    if (!savedAddress) {
      setIsEditingAddress(true);
      return;
    }

    setFullName(savedAddress.full_name || "");

    const pn = String(savedAddress.phone_number || "");
    if (pn.startsWith("+977")) {
      setCountryCode("+977");
      setPhone(pn.slice(4));
    } else {
      setPhone(pn);
    }

    setProvince(savedAddress.region || "");
    setAddressLine(savedAddress.line1 || "");
    setPostalCode(savedAddress.postal_code || "");

    const parsed = parseLine2(savedAddress.line2);
    setZone(parsed.zone);
    setCity(parsed.city);
    setLandmark(parsed.landmark);

    setIsEditingAddress(true);
  }

  function cancelEdit() {
    setErrorMsg("");
    if (savedAddress) setIsEditingAddress(false);
  }

  async function saveAddress() {
    setErrorMsg("");

    if (!fullName.trim()) {
      setErrorMsg("Full name is required");
      return;
    }

    if (phone.trim().length < 7) {
      setErrorMsg("Phone number is too short");
      return;
    }

    if (!province) {
      setErrorMsg("Please select Province / Region");
      return;
    }

    if (!city) {
      setErrorMsg("Please select City");
      return;
    }

    if (!zone) {
      setErrorMsg("Please select Zone");
      return;
    }

    if (!addressLine.trim()) {
      setErrorMsg("Please enter Address");
      return;
    }

    const pObj = NEPAL.provinces.find((p) => p.name === province) || null;
    const baseLat = pObj?.lat ?? 27.7172;
    const baseLng = pObj?.lng ?? 85.324;

    const payload = {
      full_name: fullName.trim(),
      phone_number: `${countryCode}${phone.trim()}`,
      region: province,
      line1: addressLine.trim(),
      line2: `${zone}, ${city}${landmark.trim() ? `, ${landmark.trim()}` : ""}`,
      postal_code: postalCode.trim() || null,
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
      setIsEditingAddress(false);
      setRefreshTick((t) => t + 1);
    } catch (e) {
      setErrorMsg(formatApiError(e));
    } finally {
      setSaving(false);
    }
  }

  function proceedToPayment() {
    setErrorMsg("");

    if (!savedAddress?.id) {
      setErrorMsg("Please save a shipping address to proceed.");
      return;
    }

    if (itemsCount <= 0) {
      setErrorMsg("No items to checkout.");
      return;
    }

    const checkoutContext = {
      mode: isBuyNowMode ? "BUY_NOW" : "CART",
      address_id: Number(savedAddress.id),
      address: savedAddress,
      items: orderItems.map((x) => ({
        variant_id: Number(x.variant_id),
        quantity: Number(x.quantity),
        price: Number(x.price),
        product_name: x.product_name,
        image_url: x.image_url,
        size: x.size,
        color: x.color,
      })),
      totals: {
        itemsCount,
        itemsTotal,
        deliveryFee: itemsCount > 0 ? deliveryFee : 0,
        total: itemsCount > 0 ? total : 0,
      },
    };

    sessionStorage.setItem(CHECKOUT_CTX_KEY, JSON.stringify(checkoutContext));
    navigate("/payment");
  }

  const canProceed = itemsCount > 0 && !!savedAddress;

  return (
    <div className="checkout-page">
      <CheckoutHeader />

      <main className="ck-wrap ck-main">
        <div className="ck-breadcrumb">
          <Link to="/">Home</Link>
          <span className="ck-sep">›</span>
          <span>Checkout</span>
          {isBuyNowMode ? (
            <span className="ck-buyNowFlag">(Buy Now)</span>
          ) : null}
        </div>

        <div className="ck-grid">
          <section className="ck-card ck-left">
            <div className="ck-cardHeader">
              <h2 className="ck-h2">Delivery Information</h2>
            </div>

            {loadingAddress ? (
              <div className="ck-hint">Loading address…</div>
            ) : null}

            {savedAddress && !isEditingAddress ? (
              <div className="ship-card">
                <div className="ship-head">
                  <div className="ship-title">Shipping Address</div>
                  <button
                    type="button"
                    className="ship-edit"
                    onClick={startEdit}
                  >
                    EDIT
                  </button>
                </div>

                <div className="ship-nameRow">
                  <span className="ship-name">{savedAddress.full_name}</span>
                  <span className="ship-phone">{savedAddress.phone_number}</span>
                </div>

                <div className="ship-addrRow">
                  <span className="ship-tag">HOME</span>
                  <span className="ship-addrText">
                    {savedAddress.line1}
                    {savedAddress.line2 ? `, ${savedAddress.line2}` : ""}
                    {savedAddress.region ? `, ${savedAddress.region}` : ""}
                    {savedAddress.postal_code
                      ? `, ${savedAddress.postal_code}`
                      : ""}
                    {savedAddress.country ? `, ${savedAddress.country}` : ""}
                  </span>
                </div>
              </div>
            ) : null}

            {(isEditingAddress || !savedAddress) && (
              <>
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
                      >
                        <option value="+977">+977</option>
                      </select>

                      <input
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="98XXXXXXXX"
                      />
                    </div>
                  </div>
                </div>

                <div className="ck-formGrid" style={{ marginTop: 10 }}>
                  <div className="ck-field">
                    <label>Province / Region</label>
                    <select
                      value={province}
                      onChange={(e) => handleProvinceChange(e.target.value)}
                    >
                      <option value="">
                        Please choose your province / region
                      </option>
                      {NEPAL.provinces.map((p) => (
                        <option key={p.name} value={p.name}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="ck-field">
                    <label>City</label>
                    <select
                      value={city}
                      onChange={(e) => handleCityChange(e.target.value)}
                      disabled={!province}
                    >
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
                    <select
                      value={zone}
                      onChange={(e) => setZone(e.target.value)}
                      disabled={!city}
                    >
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

                {errorMsg ? <div className="ck-error">{errorMsg}</div> : null}

                <div className="ck-footerRow" style={{ gap: 10 }}>
                  {savedAddress ? (
                    <button
                      type="button"
                      className="ck-secondary"
                      onClick={cancelEdit}
                      disabled={saving}
                    >
                      CANCEL
                    </button>
                  ) : null}

                  <button
                    type="button"
                    className="ck-primary"
                    onClick={saveAddress}
                    disabled={saving}
                  >
                    {saving ? "SAVING..." : "SAVE ADDRESS"}
                  </button>
                </div>
              </>
            )}

            <div className="ck-itemsUnderAddress">
              <div className="ck-itemsHead">
                <div className="ck-itemsTitle">Order Items</div>
              </div>

              <div className="ck-itemsBody">
                {loadingOrder ? (
                  <div className="ck-hint">Loading items…</div>
                ) : null}

                {!loadingOrder && orderItems.length === 0 ? (
                  <div className="ck-hint">No items to show.</div>
                ) : null}

                {!loadingOrder &&
                  orderItems.map((it) => {
                    const src = joinUrl(it.image_url || "") || "/shoes.jpg";

                    return (
                      <div className="ck-itemRow" key={it.id}>
                        <img
                          className="ck-itemImg"
                          src={src}
                          alt={it.product_name || "Product"}
                          onError={(e) => {
                            e.currentTarget.src = "/shoes.jpg";
                          }}
                        />

                        <div className="ck-itemInfo">
                          <div className="ck-itemName">
                            {it.product_name || `Variant #${it.variant_id}`}
                          </div>

                          <div className="ck-itemMeta">
                            {it.size ? <span>Size: {it.size}</span> : null}
                            {it.color ? <span>Color: {it.color}</span> : null}
                            <span>Qty: {it.quantity}</span>
                          </div>
                        </div>

                        <div className="ck-itemPrice">
                          {money(Number(it.price) * Number(it.quantity))}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            {!isEditingAddress && savedAddress && errorMsg ? (
              <div className="ck-error">{errorMsg}</div>
            ) : null}
          </section>

          <aside className="ck-card ck-right">
            <h3 className="ck-h3">Order Detail</h3>

            <div className="ck-lines">
              {orderItems.map((it) => (
                <div className="ck-line" key={`summary_${it.id}`}>
                  <span>
                    {it.product_name || `Variant #${it.variant_id}`}{" "}
                    {it.size ? `(${it.size})` : ""} × {it.quantity}
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
                <span className="ck-totalValue">
                  {money(itemsCount > 0 ? total : 0)}
                </span>
              </div>
            </div>

            <button
              className="ck-pay"
              type="button"
              disabled={!canProceed}
              onClick={proceedToPayment}
            >
              PROCEED TO PAYMENT
            </button>

            {!savedAddress ? (
              <div className="ck-terms">
                Please <b>save a shipping address</b> to proceed.
              </div>
            ) : null}
          </aside>
        </div>
      </main>
    </div>
  );
}