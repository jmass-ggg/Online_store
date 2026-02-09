import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "./Checkout.css";
import { apiFetch } from "../api";

const CART_KEY = "cart_items";

function money(n) {
  const v = Number(n || 0);
  return v.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function readCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY) || "[]");
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

// ---- Google Maps loader ----
function loadGoogleMaps(apiKey) {
  if (window.google?.maps?.places) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-google-maps='1']");
    if (existing) {
      existing.addEventListener("load", resolve);
      existing.addEventListener("error", reject);
      return;
    }

    const s = document.createElement("script");
    s.dataset.googleMaps = "1";
    s.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    s.async = true;
    s.defer = true;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Failed to load Google Maps script"));
    document.head.appendChild(s);
  });
}

// ---- Parse Place into backend fields ----
function parsePlace(place) {
  const comps = place?.address_components || [];

  const getLong = (type) =>
    comps.find((c) => c.types?.includes(type))?.long_name || "";
  const getShort = (type) =>
    comps.find((c) => c.types?.includes(type))?.short_name || "";

  const streetNumber = getLong("street_number");
  const route = getLong("route");

  const sublocality =
    getLong("sublocality") ||
    getLong("sublocality_level_1") ||
    getLong("neighborhood");

  const locality = getLong("locality") || getLong("postal_town");
  const admin2 = getLong("administrative_area_level_2");
  const admin1 = getLong("administrative_area_level_1"); // Province/Region
  const postal = getLong("postal_code");

  const country = getLong("country") || "Nepal";
  const countryCode = (getShort("country") || "").toLowerCase();

  const lat = place?.geometry?.location?.lat?.();
  const lng = place?.geometry?.location?.lng?.();

  const line1 =
    [streetNumber, route].filter(Boolean).join(" ") ||
    place?.formatted_address ||
    "";

  const line2 = [sublocality, locality, admin2].filter(Boolean).join(", ") || null;
  const region = admin1 || "Bagmati";

  return {
    region,
    line1,
    line2,
    postal_code: postal || null,
    country,
    country_code: countryCode,
    latitude: typeof lat === "number" ? lat : null,
    longitude: typeof lng === "number" ? lng : null,
    formatted_address: place?.formatted_address || line1,
  };
}

export default function Checkout() {
  // --- Form ---
  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("+977");
  const [phone, setPhone] = useState("");

  const [addressQuery, setAddressQuery] = useState("");
  const [addr, setAddr] = useState(null);

  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [savedAddress, setSavedAddress] = useState(null);

  const addressInputRef = useRef(null);

  // --- Cart ---
  const [cart, setCart] = useState(() => readCart());

  useEffect(() => {
    const onUpdate = () => setCart(readCart());
    window.addEventListener("cart:updated", onUpdate);
    window.addEventListener("storage", onUpdate);
    return () => {
      window.removeEventListener("cart:updated", onUpdate);
      window.removeEventListener("storage", onUpdate);
    };
  }, []);

  const itemsCount = useMemo(
    () => cart.reduce((sum, x) => sum + Number(x.qty || 0), 0),
    [cart]
  );

  const itemsTotal = useMemo(
    () => cart.reduce((sum, x) => sum + Number(x.price || 0) * Number(x.qty || 0), 0),
    [cart]
  );

  const deliveryFee = 4.5;
  const total = Math.max(0, itemsTotal + deliveryFee);

  // --- Google Places Autocomplete ---
  useEffect(() => {
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      setErrorMsg("Missing VITE_GOOGLE_MAPS_API_KEY in frontend/.env");
      return;
    }

    let autocomplete;

    loadGoogleMaps(apiKey)
      .then(() => {
        if (!addressInputRef.current) return;

        autocomplete = new window.google.maps.places.Autocomplete(
          addressInputRef.current,
          {
            componentRestrictions: { country: "np" }, // Nepal only
            fields: ["address_components", "formatted_address", "geometry"],
          }
        );

        autocomplete.addListener("place_changed", () => {
          const place = autocomplete.getPlace();
          const parsed = parsePlace(place);

          if (parsed.country_code && parsed.country_code !== "np") {
            setErrorMsg("Service available only in Nepal");
            setAddr(null);
            return;
          }

          if (!parsed.latitude || !parsed.longitude) {
            setErrorMsg("Please select an address from the suggestions dropdown.");
            setAddr(null);
            return;
          }

          setErrorMsg("");
          setAddr(parsed);
          setAddressQuery(parsed.formatted_address);
        });
      })
      .catch((e) => setErrorMsg(e.message));

    return () => {
      autocomplete = null;
    };
  }, []);

  const mapEmbedSrc = useMemo(() => {
    if (addr?.latitude && addr?.longitude) {
      return `https://www.google.com/maps?q=${addr.latitude},${addr.longitude}&z=15&output=embed`;
    }
    const q = encodeURIComponent((addressQuery || "Kathmandu, Nepal").trim());
    return `https://www.google.com/maps?q=${q}&output=embed`;
  }, [addr, addressQuery]);

  async function saveAddress() {
    setErrorMsg("");

    if (!fullName.trim()) return setErrorMsg("Full name is required");
    if (phone.trim().length < 7) return setErrorMsg("Phone number is too short");

    if (!addr?.latitude || !addr?.longitude) {
      return setErrorMsg("Select an address from the Google suggestions list.");
    }

    setSaving(true);
    try {
      const payload = {
        region: addr.region,
        line1: addr.line1,
        line2: addr.line2,
        postal_code: addr.postal_code,
        country: addr.country || "Nepal",
        latitude: addr.latitude,
        longitude: addr.longitude,
        is_default_shipping: true,
        is_default_billing: false,
      };

      // ✅ backend router prefix is /addresses
      const saved = await apiFetch("/addresses/", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setSavedAddress(saved);
    } catch (e) {
      setErrorMsg(e?.message || "Failed to save address");
    } finally {
      setSaving(false);
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
            <span className="ck-searchIcon" aria-hidden="true">🔎</span>
            <input placeholder="Search for products..." />
          </div>

          <div className="ck-actions">
            <button className="ck-iconBtn" aria-label="Cart">🛒</button>
            <button className="ck-iconBtn" aria-label="Notifications">🔔</button>
            <button className="ck-avatar" aria-label="Account">👤</button>
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
        </div>

        <div className="ck-grid">
          <section className="ck-card ck-left">
            <div className="ck-cardHeader">
              <div className="ck-step">
                <span className="ck-stepDot">1</span>
                <h2 className="ck-h2">Delivery Information</h2>
              </div>
              <div className="ck-stepText">Step 1 of 2</div>
            </div>

            {savedAddress && (
              <div className="ship-card">
                <div className="ship-head">
                  <div className="ship-title">Shipping Address</div>
                  <div className="ship-edit">EDIT</div>
                </div>

                <div className="ship-nameRow">
                  <span className="ship-name">{fullName}</span>
                  <span className="ship-phone">{countryCode} {phone}</span>
                </div>

                <div className="ship-addrRow">
                  <span className="ship-tag">HOME</span>
                  <span className="ship-addrText">
                    {savedAddress.line1}
                    {savedAddress.region ? `, ${savedAddress.region}` : ""}
                    {savedAddress.postal_code ? `, ${savedAddress.postal_code}` : ""}
                    {savedAddress.country ? `, ${savedAddress.country}` : ""}
                  </span>
                </div>
              </div>
            )}

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

            <div className="ck-field ck-fieldFull">
              <label>Delivery Address</label>
              <div className="ck-addressRow">
                <span className="ck-pin" aria-hidden="true">📍</span>
                <input
                  ref={addressInputRef}
                  value={addressQuery}
                  onChange={(e) => {
                    setAddressQuery(e.target.value);
                    setAddr(null); // force selecting from dropdown
                  }}
                  placeholder="Start typing address (Nepal)..."
                />
              </div>
            </div>

            {errorMsg && <div className="ck-error">{errorMsg}</div>}

            <div className="ck-map">
              <iframe
                title="Map"
                src={mapEmbedSrc}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>

            <div className="ck-footerRow">
              <button
                className="ck-primary"
                type="button"
                onClick={saveAddress}
                disabled={saving || addressQuery.trim().length < 6}
              >
                {saving ? "SAVING..." : "SAVE ADDRESS"}
              </button>
            </div>
          </section>

          <aside className="ck-card ck-right">
            <h3 className="ck-h3">Order Detail</h3>

            <div className="ck-lines">
              <div className="ck-line">
                <span>Items Total ({itemsCount} item{itemsCount === 1 ? "" : "s"})</span>
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

            <button className="ck-pay" type="button" disabled={!canProceed}>
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
