import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Checkout.css";
import StoreTopBar from "./components/cart/StoreTopBar";
import { apiFetch, joinUrl } from "../api";

const BUY_NOW_KEY = "buy_now_item";
const CHECKOUT_CTX_KEY = "checkout_context";
const FALLBACK_IMAGE = "/shoes.jpg";

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

function sortByNewest(a, b) {
  const ta = Date.parse(a?.updated_at || a?.created_at || "") || 0;
  const tb = Date.parse(b?.updated_at || b?.created_at || "") || 0;
  return tb - ta;
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

function addressText(address) {
  if (!address) return "";
  return [
    address.line1,
    address.line2,
    address.region,
    address.postal_code,
    address.country,
  ]
    .filter(Boolean)
    .join(", ");
}

function readBuyNow() {
  try {
    const raw = JSON.parse(localStorage.getItem(BUY_NOW_KEY) || "null");
    if (!toId(raw?.item?.variant_id)) return null;
    return raw;
  } catch {
    return null;
  }
}

function readCheckoutContext() {
  try {
    const raw = JSON.parse(sessionStorage.getItem(CHECKOUT_CTX_KEY) || "null");
    if (!raw || typeof raw !== "object") return null;
    return raw;
  } catch {
    return null;
  }
}

function pickBestAddress(list) {
  const arr = Array.isArray(list) ? [...list] : [];
  if (!arr.length) return null;

  const defaultShipping = arr.find((item) => item?.is_default_shipping);
  if (defaultShipping) return defaultShipping;

  arr.sort(sortByNewest);
  return arr[0] || null;
}

function jitterCoord(base, maxDelta = 0.03) {
  const r = (Math.random() * 2 - 1) * maxDelta;
  return Number((base + r).toFixed(6));
}

function normalizeCartItemsForPayment(items) {
  const list = Array.isArray(items) ? items : [];

  return list.map((item, index) => ({
    key: `${toId(item?.product_variant?.variant_id)}_${index}`,
    variant_id: toId(item?.product_variant?.variant_id),
    quantity: Math.max(1, toNumber(item?.quantity, 1)),
    price: toNumber(item?.price, 0),
    product_name: String(item?.product?.product_name || "").trim(),
    product_category: String(item?.product?.product_category || "").trim(),
    size: String(item?.product_variant?.size || "").trim(),
    color: String(item?.product_variant?.color || "").trim(),
    image_url: String(item?.product?.image_url || "").trim(),
  }));
}

function makeBuyNowFallbackItem(buyNowData) {
  const item = buyNowData?.item;
  if (!toId(item?.variant_id)) return null;

  const quantity = Math.max(1, toNumber(item?.quantity, 1));
  const price = toNumber(item?.price, 0);

  return {
    cart_item_id: `buy_now_${toId(item.variant_id)}`,
    quantity,
    price,
    line_total: quantity * price,
    selected: true,
    product_variant: {
      variant_id: toId(item.variant_id),
      sku: String(item?.sku || "").trim(),
      color: String(item?.color || "").trim(),
      size: String(item?.size || "").trim(),
      price,
      stock_quantity: toNumber(item?.stock_quantity, 0),
      is_active: true,
    },
    product: {
      product_id: toId(item?.product_id),
      product_name: String(item?.product_name || "Selected Product").trim(),
      url_slug: String(item?.url_slug || "").trim(),
      product_category: String(item?.product_category || "").trim(),
      target_audience: String(item?.target_audience || "").trim(),
      description: String(item?.description || "").trim(),
      image_url: String(item?.image_url || "").trim(),
      status: "active",
      seller_id: toId(item?.seller_id),
    },
  };
}

function normalizeCheckoutResponse(raw, { mode, buyNowData, cartId } = {}) {
  if (!raw || typeof raw !== "object") return null;

  let items = [];

  if (Array.isArray(raw.items) && raw.items.length) {
    items = raw.items.map((item, index) => ({
      cart_item_id: toId(item?.cart_item_id || `${toId(item?.product_variant?.variant_id)}_${index}`),
      quantity: Math.max(1, toNumber(item?.quantity, 1)),
      price: toNumber(item?.price ?? item?.product_variant?.price, 0),
      line_total: toNumber(
        item?.line_total,
        toNumber(item?.price ?? item?.product_variant?.price, 0) *
          Math.max(1, toNumber(item?.quantity, 1))
      ),
      selected: item?.selected !== false,
      product_variant: {
        variant_id: toId(item?.product_variant?.variant_id),
        sku: String(item?.product_variant?.sku || "").trim(),
        color: String(item?.product_variant?.color || "").trim(),
        size: String(item?.product_variant?.size || "").trim(),
        price: toNumber(item?.product_variant?.price ?? item?.price, 0),
        stock_quantity: toNumber(item?.product_variant?.stock_quantity, 0),
        is_active: item?.product_variant?.is_active !== false,
      },
      product: {
        product_id: toId(item?.product?.product_id),
        product_name: String(item?.product?.product_name || "Product").trim(),
        url_slug: String(item?.product?.url_slug || "").trim(),
        product_category: String(item?.product?.product_category || "").trim(),
        target_audience: String(item?.product?.target_audience || "").trim(),
        description: String(item?.product?.description || "").trim(),
        image_url: String(item?.product?.image_url || "").trim(),
        status: String(item?.product?.status || "").trim(),
        seller_id: toId(item?.product?.seller_id),
      },
    }));
  } else if (mode === "BUY_NOW") {
    const fallback = makeBuyNowFallbackItem(buyNowData);

    if (fallback) {
      const quantity = Math.max(1, toNumber(raw?.quantity ?? fallback.quantity, 1));
      const unitPrice = toNumber(
        raw?.unit_price ??
          raw?.price ??
          raw?.variant?.price ??
          raw?.product_variant?.price ??
          fallback.price,
        fallback.price
      );

      items = [
        {
          ...fallback,
          quantity,
          price: unitPrice,
          line_total: toNumber(
            raw?.items_subtotal ?? raw?.subtotal,
            quantity * unitPrice
          ),
          product: {
            ...fallback.product,
            ...(raw?.product || {}),
          },
          product_variant: {
            ...fallback.product_variant,
            ...(raw?.variant || raw?.product_variant || {}),
            price: unitPrice,
          },
        },
      ];
    }
  }

  const subtotal = toNumber(
    raw?.subtotal ?? raw?.items_subtotal,
    items.reduce((sum, item) => sum + toNumber(item?.line_total, 0), 0)
  );

  const delivery_charge = toNumber(raw?.delivery_charge, 0);
  const total = toNumber(raw?.total ?? raw?.grand_total, subtotal + delivery_charge);

  return {
    mode,
    cart_id: toId(raw?.cart_id || cartId),
    buyer_id: toId(raw?.buyer_id),
    status: String(raw?.status || "").trim(),
    selected_count: toNumber(raw?.selected_count, items.length),
    subtotal,
    delivery_charge,
    total,
    address: raw?.address || null,
    delivery_breakdown: Array.isArray(raw?.delivery_breakdown) ? raw.delivery_breakdown : [],
    items,
  };
}

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
        { name: "Beni", zones: ["Birendra Chowk", "Campus Chowk", "Hospital Chowk"] },
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

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();

  const isBuyNowMode = new URLSearchParams(location.search).get("mode") === "buy_now";

  const [buyNowData, setBuyNowData] = useState(() => readBuyNow());
  const [checkoutContext, setCheckoutContext] = useState(() => readCheckoutContext());

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
  const [savingAddress, setSavingAddress] = useState(false);
  const [loadingCheckout, setLoadingCheckout] = useState(false);

  const [errorMsg, setErrorMsg] = useState("");
  const [savedAddress, setSavedAddress] = useState(null);
  const [isEditingAddress, setIsEditingAddress] = useState(false);
  const [checkoutData, setCheckoutData] = useState(null);
  const [search, setSearch] = useState("");

  const cartId = useMemo(() => {
    return toId(checkoutContext?.cart_id || checkoutData?.cart_id);
  }, [checkoutContext, checkoutData]);

  function handleSearchSubmit(query) {
    navigate(query ? `/products?search=${encodeURIComponent(query)}` : "/products");
  }

  useEffect(() => {
    const sync = () => {
      setBuyNowData(readBuyNow());
      setCheckoutContext(readCheckoutContext());
    };

    sync();

    window.addEventListener("buy_now:updated", sync);
    window.addEventListener("storage", sync);

    return () => {
      window.removeEventListener("buy_now:updated", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  function fillFormFromAddress(address) {
    if (!address) return;

    setFullName(address.full_name || "");
    setAddressLine(address.line1 || "");
    setPostalCode(address.postal_code || "");
    setProvince(address.region || "");

    const pn = String(address.phone_number || "");
    if (pn.startsWith("+977")) {
      setCountryCode("+977");
      setPhone(pn.slice(4));
    } else {
      setCountryCode("+977");
      setPhone(pn);
    }

    const parsed = parseLine2(address.line2);
    setZone(parsed.zone);
    setCity(parsed.city);
    setLandmark(parsed.landmark);
  }

  useEffect(() => {
    let cancelled = false;

    async function loadAddresses() {
      setLoadingAddress(true);
      setErrorMsg("");

      try {
        const list = await apiFetch("/addresses/");
        if (cancelled) return;

        const best = pickBestAddress(list);
        setSavedAddress(best || null);
        setIsEditingAddress(!best);

        if (best) {
          fillFormFromAddress(best);
        } else {
          setCheckoutData(null);
        }
      } catch (e) {
        if (!cancelled) {
          setSavedAddress(null);
          setIsEditingAddress(true);
          setCheckoutData(null);
          setErrorMsg(formatApiError(e));
        }
      } finally {
        if (!cancelled) setLoadingAddress(false);
      }
    }

    loadAddresses();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadCheckoutPreview() {
      if (!savedAddress?.id || isEditingAddress) {
        setCheckoutData(null);
        return;
      }

      if (isBuyNowMode && !toId(buyNowData?.item?.variant_id)) {
        setCheckoutData(null);
        return;
      }

      if (!isBuyNowMode && !cartId) {
        setCheckoutData(null);
        return;
      }

      setLoadingCheckout(true);
      setErrorMsg("");

      try {
        let raw;

        if (isBuyNowMode) {
          raw = await apiFetch("/checkout/checkout", {
            method: "POST",
            body: JSON.stringify({
              address_id: savedAddress.id,
              variant_id: buyNowData.item.variant_id,
              quantity: Math.max(1, toNumber(buyNowData.item.quantity, 1)),
            }),
          });
        } else {
          raw = await apiFetch(`/checkout/checkout/${cartId}`, {
            method: "POST",
            // If your backend needs address_id here, uncomment the next line:
            // body: JSON.stringify({ address_id: savedAddress.id }),
          });
        }

        if (cancelled) return;

        const normalized = normalizeCheckoutResponse(raw, {
          mode: isBuyNowMode ? "BUY_NOW" : "CART",
          buyNowData,
          cartId,
        });

        setCheckoutData(normalized);
      } catch (e) {
        if (!cancelled) {
          setCheckoutData(null);
          setErrorMsg(formatApiError(e));
        }
      } finally {
        if (!cancelled) setLoadingCheckout(false);
      }
    }

    loadCheckoutPreview();

    return () => {
      cancelled = true;
    };
  }, [
    isBuyNowMode,
    isEditingAddress,
    savedAddress?.id,
    buyNowData?.item?.variant_id,
    buyNowData?.item?.quantity,
    cartId,
  ]);

  const provinceObj = useMemo(() => {
    return NEPAL.provinces.find((p) => p.name === province) || null;
  }, [province]);

  const cityOptions = useMemo(() => provinceObj?.cities || [], [provinceObj]);

  const cityObj = useMemo(() => {
    return cityOptions.find((c) => c.name === city) || null;
  }, [cityOptions, city]);

  const zoneOptions = useMemo(() => cityObj?.zones || [], [cityObj]);

  const displayAddress = checkoutData?.address || savedAddress || null;

  const displayItems = useMemo(() => {
    if (Array.isArray(checkoutData?.items) && checkoutData.items.length) {
      return checkoutData.items;
    }

    if (isBuyNowMode) {
      const fallback = makeBuyNowFallbackItem(buyNowData);
      return fallback ? [fallback] : [];
    }

    return [];
  }, [checkoutData, isBuyNowMode, buyNowData]);

  const totalQuantity = useMemo(() => {
    return displayItems.reduce((sum, item) => sum + Math.max(1, toNumber(item?.quantity, 1)), 0);
  }, [displayItems]);

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
    setIsEditingAddress(true);
    setCheckoutData(null);
  }

  function cancelEdit() {
    setErrorMsg("");

    if (savedAddress) {
      fillFormFromAddress(savedAddress);
      setIsEditingAddress(false);
    }
  }

  async function saveAddress() {
    setErrorMsg("");

    if (!fullName.trim()) return setErrorMsg("Full name is required");
    if (phone.trim().length < 7) return setErrorMsg("Phone number is too short");
    if (!province) return setErrorMsg("Please select Province / Region");
    if (!city) return setErrorMsg("Please select City");
    if (!zone) return setErrorMsg("Please select Zone");
    if (!addressLine.trim()) return setErrorMsg("Please enter Address");

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

    setSavingAddress(true);

    try {
      const saved = await apiFetch("/addresses/", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSavedAddress(saved);
      fillFormFromAddress(saved);
      setIsEditingAddress(false);
    } catch (e) {
      setErrorMsg(formatApiError(e));
    } finally {
      setSavingAddress(false);
    }
  }

  function proceedToPayment() {
    setErrorMsg("");

    if (!checkoutData) {
      setErrorMsg("Checkout summary is not ready yet.");
      return;
    }

    sessionStorage.setItem(
      CHECKOUT_CTX_KEY,
      JSON.stringify({
        mode: isBuyNowMode ? "BUY_NOW" : "CART",
        address_id: toId(savedAddress?.id || checkoutData?.address?.id),
        cart_id: toId(checkoutData?.cart_id || cartId),
        variant_id: isBuyNowMode
          ? toId(displayItems?.[0]?.product_variant?.variant_id)
          : "",
        quantity: isBuyNowMode
          ? Math.max(1, toNumber(displayItems?.[0]?.quantity, 1))
          : 0,
        items: normalizeCartItemsForPayment(checkoutData?.items),
        checkout: checkoutData,
      })
    );

    navigate("/payment", {
      state: {
        checkout: checkoutData,
      },
    });
  }

  if (isBuyNowMode && !buyNowData?.item?.variant_id) {
    return (
      <div className="checkout-page">
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/products"
          profilePath="/login"
        />

        <main className="ck-wrap ck-main">
          <div className="ck-card">
            <h2 className="ck-h2">No item selected</h2>
            <div className="ck-hint">Please go back and click Order Now again.</div>
          </div>
        </main>
      </div>
    );
  }

  if (!isBuyNowMode && !cartId) {
    return (
      <div className="checkout-page">
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/products"
          profilePath="/login"
        />

        <main className="ck-wrap ck-main">
          <div className="ck-card">
            <h2 className="ck-h2">No cart selected</h2>
            <div className="ck-hint">Please go back to your cart and click checkout again.</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <StoreTopBar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearchSubmit}
        searchPlaceholder="Search footwear..."
        bagPath="/cart"
        wishlistPath="/products"
        profilePath="/login"
      />

      <main className="ck-wrap ck-main">
        <div className="ck-breadcrumb">
          <Link to="/">Home</Link>
          <span className="ck-sep">›</span>
          <span>Checkout</span>
          <span className="ck-buyNowFlag">
            {isBuyNowMode ? "(Buy Now)" : "(Cart Checkout)"}
          </span>
        </div>

        <div className="ck-grid">
          <section className="ck-card ck-left">
            <div className="ck-cardHeader">
              <h2 className="ck-h2">Delivery Information</h2>
            </div>

            {loadingAddress ? <div className="ck-hint">Loading address…</div> : null}

            {savedAddress && !isEditingAddress ? (
              <div className="ship-card">
                <div className="ship-head">
                  <div className="ship-title">Shipping Address</div>
                  <button type="button" className="ship-edit" onClick={startEdit}>
                    EDIT
                  </button>
                </div>

                <div className="ship-nameRow">
                  <span className="ship-name">
                    {displayAddress?.full_name || savedAddress.full_name}
                  </span>
                  <span className="ship-phone">
                    {displayAddress?.phone_number || savedAddress.phone_number}
                  </span>
                </div>

                <div className="ship-addrRow">
                  <span className="ship-tag">HOME</span>
                  <span className="ship-addrText">
                    {addressText(displayAddress || savedAddress)}
                  </span>
                </div>
              </div>
            ) : null}

            {(isEditingAddress || !savedAddress) && (
              <>
                <div className="ck-hint" style={{ marginBottom: 12 }}>
                  Add address first. After address is saved, checkout API will run automatically.
                </div>

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
                      <select value={countryCode} onChange={(e) => setCountryCode(e.target.value)}>
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
                    <select value={province} onChange={(e) => handleProvinceChange(e.target.value)}>
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
                      disabled={savingAddress}
                    >
                      CANCEL
                    </button>
                  ) : null}

                  <button
                    type="button"
                    className="ck-primary"
                    onClick={saveAddress}
                    disabled={savingAddress}
                  >
                    {savingAddress ? "SAVING..." : "SAVE ADDRESS"}
                  </button>
                </div>
              </>
            )}

            <div className="ck-itemsUnderAddress">
              <div className="ck-itemsHead">
                <div className="ck-itemsTitle">
                  Order Items ({displayItems.length})
                </div>
              </div>

              <div className="ck-itemsBody">
                {displayItems.length > 0 ? (
                  displayItems.map((item) => {
                    const itemImage = joinUrl(item?.product?.image_url || "") || FALLBACK_IMAGE;

                    return (
                      <div className="ck-itemRow" key={item.cart_item_id}>
                        <img
                          className="ck-itemImg"
                          src={itemImage}
                          alt={item?.product?.product_name || "Product"}
                          onError={(e) => {
                            e.currentTarget.src = FALLBACK_IMAGE;
                          }}
                        />

                        <div className="ck-itemInfo">
                          <div className="ck-itemName">
                            {item?.product?.product_name || "Product"}
                          </div>

                          <div className="ck-itemMeta">
                            {item?.product?.product_category ? (
                              <span>{item.product.product_category}</span>
                            ) : null}
                            <span>Size: {item?.product_variant?.size || "-"}</span>
                            <span>Color: {item?.product_variant?.color || "-"}</span>
                            <span>Qty: {Math.max(1, toNumber(item?.quantity, 1))}</span>
                            {item?.product_variant?.sku ? (
                              <span>SKU: {item.product_variant.sku}</span>
                            ) : null}
                          </div>
                        </div>

                        <div className="ck-itemPrice">
                          {money(item?.line_total)}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="ck-hint">
                    {loadingCheckout
                      ? "Loading selected items…"
                      : "No selected items found."}
                  </div>
                )}
              </div>
            </div>

            {!isEditingAddress && savedAddress && errorMsg ? (
              <div className="ck-error">{errorMsg}</div>
            ) : null}
          </section>

          <aside className="ck-card ck-right">
            <h3 className="ck-h3">Order Detail</h3>

            {!savedAddress || isEditingAddress ? (
              <div className="ck-hint">Save address first to get checkout summary.</div>
            ) : loadingCheckout ? (
              <div className="ck-hint">Loading checkout summary…</div>
            ) : checkoutData ? (
              <div className="ck-lines">
                <div className="ck-line">
                  <span>Items</span>
                  <span>{displayItems.length}</span>
                </div>

                <div className="ck-line">
                  <span>Total Quantity</span>
                  <span>{totalQuantity}</span>
                </div>

                <div className="ck-line">
                  <span>Subtotal</span>
                  <span>{money(checkoutData?.subtotal)}</span>
                </div>

                <div className="ck-line">
                  <span>Delivery Charge</span>
                  <span>{money(checkoutData?.delivery_charge)}</span>
                </div>

                <div className="ck-divider" />

                <div className="ck-totalRow">
                  <span className="ck-totalLabel">Grand Total</span>
                  <span className="ck-totalValue">{money(checkoutData?.total)}</span>
                </div>
              </div>
            ) : (
              <div className="ck-hint">Could not load checkout summary.</div>
            )}

            <button
              className="ck-pay"
              type="button"
              disabled={!checkoutData || loadingCheckout || isEditingAddress}
              onClick={proceedToPayment}
            >
              PROCEED TO PAYMENT
            </button>

            {!savedAddress ? (
              <div className="ck-terms">
                Please <b>save a shipping address</b> first.
              </div>
            ) : null}
          </aside>
        </div>
      </main>
    </div>
  );
}