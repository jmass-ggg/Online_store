import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import "./Checkout.css";

function money(n) {
  const v = Number(n || 0);
  return v.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export default function Checkout() {
  // --- Form state ---
  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("+880");
  const [phone, setPhone] = useState("");
  const [addressQuery, setAddressQuery] = useState("");
  const [selectedAddress, setSelectedAddress] = useState("");

  const [promo, setPromo] = useState("");
  const [promoApplied, setPromoApplied] = useState(false);

  const itemsTotal = 128.0;
  const deliveryFee = 4.5;

  const discount = useMemo(() => {
    if (!promoApplied) return 0;
    if (promo.trim().toUpperCase() === "SAVE10") return 10;
    // unknown code: no discount
    return 0;
  }, [promo, promoApplied]);

  const total = Math.max(0, itemsTotal + deliveryFee - discount);

  const canProceed =
    fullName.trim().length > 1 &&
    phone.trim().length >= 7 &&
    (selectedAddress || "").trim().length > 6;

  const mapQuery = encodeURIComponent(
    (selectedAddress || addressQuery || "Dhaka, Bangladesh").trim(),
  );

  const mapEmbedSrc = `https://www.google.com/maps?q=${mapQuery}&output=embed`;

  function applyPromo() {
    setPromoApplied(true);
  }

  function saveAddress() {
    const v = addressQuery.trim();
    if (v.length < 6) return;
    setSelectedAddress(v);
  }

  function clearAddress() {
    setSelectedAddress("");
    setAddressQuery("");
  }

  return (
    <div className="checkout-page">
      {}
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

      {}
      <main className="ck-wrap ck-main">
        {/* Breadcrumb */}
        <div className="ck-breadcrumb">
          <Link to="/">Home</Link>
          <span className="ck-sep">›</span>
          <a href="#">Cart</a>
          <span className="ck-sep">›</span>
          <span className="ck-current">Checkout</span>
        </div>

        <div className="ck-grid">
          {/* Left: Delivery Information */}
          <section className="ck-card ck-left">
            <div className="ck-cardHeader">
              <div className="ck-step">
                <span className="ck-stepDot">1</span>
                <h2 className="ck-h2">Delivery Information</h2>
              </div>
              <div className="ck-stepText">Step 1 of 2</div>
            </div>

            <div className="ck-formGrid">
              <div className="ck-field">
                <label>Full Name</label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. John Doe"
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
                    <option value="+91">+977</option>
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
                <span className="ck-pin" aria-hidden="true">
                  📍
                </span>
                <input
                  value={addressQuery}
                  onChange={(e) => setAddressQuery(e.target.value)}
                  placeholder="Search your delivery address on the map..."
                />
                
              </div>
              {selectedAddress ? (
                <div className="ck-selected">
                  <div className="ck-selectedLabel">CURRENT SELECTION</div>
                  <div className="ck-selectedRow">
                    <div className="ck-selectedText">{selectedAddress}</div>
                    <button
                      className="ck-link"
                      type="button"
                      onClick={clearAddress}
                    >
                      Change
                    </button>
                  </div>
                </div>
              ) : (
                <div className="ck-hint">
                  Tip: type an address and click <b>Save</b>. The map updates to
                  that location.
                </div>
              )}
            </div>

            {/* Map */}
            <div className="ck-map">
              <iframe
                title="Map"
                src={mapEmbedSrc}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
              <div className="ck-mapControls" aria-hidden="true">
                <div className="ck-ctrlBtn">⦿</div>
                <div className="ck-ctrlStack">
                  <div className="ck-ctrlBtn">+</div>
                  <div className="ck-ctrlBtn">−</div>
                </div>
              </div>
            </div>

            <div className="ck-footerRow">
              <button
                className="ck-primary"
                type="button"
                onClick={saveAddress}
                disabled={addressQuery.trim().length < 6}
              >
                SAVE ADDRESS
              </button>
            </div>
          </section>

          {/* Right: Order Summary */}
          <aside className="ck-card ck-right">
            <h3 className="ck-h3">Order Detail</h3>

            {/* <div className="ck-promo">
              <input
                value={promo}
                onChange={(e) => setPromo(e.target.value)}
                placeholder="Promo Code"
              />
              <button className="ck-outline" type="button" onClick={applyPromo}>
                APPLY
              </button>
            </div> */}

            <div className="ck-lines">
              <div className="ck-line">
                <span>Items Total (3 items)</span>
                <span>{money(itemsTotal)}</span>
              </div>
              <div className="ck-line">
                <span>Delivery Fee</span>
                <span>{money(deliveryFee)}</span>
              </div>
              <div className={`ck-line ${discount > 0 ? "ck-discount" : ""}`}>
                <span>Discount</span>
                <span>{discount > 0 ? `-${money(discount)}` : money(0)}</span>
              </div>

              <div className="ck-divider" />

              <div className="ck-totalRow">
                <span className="ck-totalLabel">Total</span>
                <span className="ck-totalValue">{money(total)}</span>
              </div>

              <div className="ck-vat">VAT included where applicable</div>
            </div>

            <button className="ck-pay" type="button" disabled={!canProceed}>
              PROCEED TO PAY
            </button>

            <div className="ck-terms">
              By placing your order, you agree to our{" "}
              <a href="#">Terms of Service</a> and{" "}
              <a href="#">Privacy Policy</a>.
            </div>

            <div className="ck-secure">
              <span className="ck-shield" aria-hidden="true">
                ✅
              </span>
              <div>
                <div className="ck-secureTitle">Secure Checkout</div>
                <div className="ck-secureText">
                  Your data is protected by industry-standard encryption.
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <footer className="ck-footer">
        <div className="ck-wrap ck-footerRow2">
          <div className="ck-footerBrand">👜 ShopModern</div>
          <div className="ck-footerLinks">
            <a href="#">Support</a>
            <a href="#">Return Policy</a>
            <a href="#">Shipping Info</a>
          </div>
          <div className="ck-footerBtns">
            <button className="ck-footBtn" aria-label="Payments">
              💳
            </button>
            <button className="ck-footBtn" aria-label="Wallet">
              👛
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
