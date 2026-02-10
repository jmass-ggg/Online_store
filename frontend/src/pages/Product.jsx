import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Product.css";
import { apiFetch, joinUrl } from "../api";

const BUY_NOW_KEY = "buy_now_item";

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    toNumber(value)
  );
}

const SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"];
function sizeRank(size) {
  const s = String(size || "").trim().toUpperCase();
  const idx = SIZE_ORDER.indexOf(s);
  if (idx >= 0) return idx;
  const num = Number(s);
  if (Number.isFinite(num)) return 100 + num;
  return 1000;
}

export default function Product() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [activeImg, setActiveImg] = useState("/shoes.jpg");
  const [selectedVariant, setSelectedVariant] = useState(null);

  const [qty, setQty] = useState(1);

  const [shipOpen, setShipOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [toast, setToast] = useState("");
  const showToast = (msg) => {
    setToast(msg);
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(""), 2200);
  };

  // ---------- Variants ----------
  const variants = useMemo(() => {
    if (!product) return [];
    const v = product.variants || product.ProductVariants || [];
    return Array.isArray(v) ? v : [];
  }, [product]);

  const sizeOptions = useMemo(() => {
    const map = new Map();
    for (const v of variants) {
      const size = String(v?.size || "").trim();
      if (!size) continue;

      if (!map.has(size)) map.set(size, v);
      else {
        const cur = map.get(size);
        const vStock = toNumber(v.stock_quantity);
        const cStock = toNumber(cur.stock_quantity);
        const vIn = vStock > 0;
        const cIn = cStock > 0;

        if (vIn && !cIn) map.set(size, v);
        else if (vIn === cIn && toNumber(v.price) < toNumber(cur.price)) map.set(size, v);
      }
    }

    const arr = Array.from(map.entries()).map(([size, variant]) => ({ size, variant }));
    arr.sort((a, b) => {
      const ra = sizeRank(a.size);
      const rb = sizeRank(b.size);
      if (ra !== rb) return ra - rb;
      return a.size.localeCompare(b.size, undefined, { numeric: true, sensitivity: "base" });
    });
    return arr;
  }, [variants]);

  const defaultVariant = useMemo(() => {
    if (sizeOptions.length === 0) return null;
    const inStock = sizeOptions.find((x) => toNumber(x.variant.stock_quantity) > 0);
    return (inStock || sizeOptions[0]).variant;
  }, [sizeOptions]);

  const chosenVariant = selectedVariant || defaultVariant;

  const displayPrice = useMemo(() => toNumber(chosenVariant?.price ?? 0), [chosenVariant]);

  const stockMax = useMemo(() => {
    const s = toNumber(chosenVariant?.stock_quantity);
    return s > 0 ? s : 0;
  }, [chosenVariant]);

  // ---------- Load product ----------
  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      setError("");
      setProduct(null);
      setSelectedVariant(null);

      try {
        const data = await apiFetch(`/product/slug/${encodeURIComponent(slug)}`);
        if (!alive) return;

        setProduct(data);
        setActiveImg(joinUrl(data.image_url || "") || "/shoes.jpg");
      } catch (e) {
        if (!alive) return;
        setError(e?.message || "Failed to load product");
      } finally {
        if (alive) setLoading(false);
      }
    }

    load();
    return () => {
      alive = false;
    };
  }, [slug]);

  // set default size once loaded
  useEffect(() => {
    if (!product) return;
    if (selectedVariant) return;
    if (defaultVariant) setSelectedVariant(defaultVariant);
  }, [product, defaultVariant, selectedVariant]);

  // ✅ keep qty valid when size changes (if stock smaller)
  useEffect(() => {
    if (!chosenVariant) return;
    const max = toNumber(chosenVariant.stock_quantity);
    setQty((q) => {
      const next = Math.max(1, q);
      if (max > 0) return Math.min(next, max);
      return 1;
    });
  }, [chosenVariant?.id]);

  function getVariantOrToast() {
    if (!product) return null;
    const v = chosenVariant;

    if (!v) return (showToast("No sizes available."), null);

    const variantId = Number(v.id);
    if (!Number.isFinite(variantId)) return (showToast("Invalid variant."), null);

    const stock = toNumber(v.stock_quantity);
    if (stock <= 0) return (showToast("This size is out of stock."), null);

    const safeQty = Math.max(1, Math.min(toNumber(qty), stock));
    if (safeQty !== qty) setQty(safeQty);

    return { v, variantId, stock, safeQty };
  }

  // ✅ Quantity controls
  const decQty = () => setQty((q) => Math.max(1, q - 1));
  const incQty = () => setQty((q) => (stockMax > 0 ? Math.min(stockMax, q + 1) : q + 1));
  const onQtyInput = (e) => {
    const raw = e.target.value;
    const n = Math.max(1, toNumber(raw));
    setQty(stockMax > 0 ? Math.min(stockMax, n) : n);
  };

  // ✅ Add to Cart: backend cart (adds qty)
  async function handleAddToCart() {
    const info = getVariantOrToast();
    if (!info) return;

    if (busy) return;
    setBusy(true);
    try {
      await apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({ variant_id: info.variantId, quantity: info.safeQty }),
      });

      window.dispatchEvent(new Event("cart:updated"));
      showToast(`Added ${info.safeQty} to cart ✅`);
    } catch (e) {
      showToast(e?.message || "Failed to add to cart");
    } finally {
      setBusy(false);
    }
  }

  // ✅ Order Now: buy-now checkout item (replaces previous buy-now item)
  function handleOrderNow() {
    const info = getVariantOrToast();
    if (!info) return;

    const payload = {
      mode: "BUY_NOW",
      created_at: Date.now(),
      item: {
        variant_id: info.variantId,
        quantity: info.safeQty,

        // display info for checkout (no extra request needed)
        product_id: product.id,
        product_name: product.product_name,
        product_category: product.product_category,
        url_slug: product.url_slug,
        image_url: activeImg,
        size: info.v.size,
        price: toNumber(info.v.price),
      },
    };

    localStorage.setItem(BUY_NOW_KEY, JSON.stringify(payload));
    window.dispatchEvent(new Event("buy_now:updated"));
    navigate("/checkout?mode=buy_now");
  }

  if (loading) return <div className="pwrap">Loading...</div>;
  if (error) return <div className="pwrap error">{error}</div>;
  if (!product) return null;

  const outOfStock = stockMax <= 0;

  return (
    <div className="pwrap">
      {toast && <div className="ptoast">{toast}</div>}

      <div className="pgrid">
        <div className="pleft">
          <div className="pbreadcrumb">
            Home / {product.product_category || "Products"} / {product.product_name}
          </div>

          <div className="pmain">
            <img
              src={activeImg}
              alt={product.product_name}
              onError={(e) => (e.currentTarget.src = "/shoes.jpg")}
            />
          </div>
        </div>

        <aside className="pright">
          <h1 className="ptitle">{product.product_name}</h1>
          <p className="pcat">{product.product_category}</p>
          <p className="pprice">{formatMoney(displayPrice)}</p>

          {/* Sizes */}
          <div className="psizes">
            {sizeOptions.map(({ size, variant }) => {
              const chosen = chosenVariant?.id === variant.id;
              const out = toNumber(variant.stock_quantity) <= 0;

              return (
                <button
                  key={variant.id}
                  type="button"
                  className={`psizeBtn ${chosen ? "selected" : ""}`}
                  disabled={out || busy}
                  onClick={() => setSelectedVariant(variant)}
                  title={out ? "Out of stock" : `Select size ${size}`}
                >
                  {size}
                </button>
              );
            })}
          </div>

          {/* ✅ Quantity */}
          <div className="pqtyRow" style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 14 }}>
            <span style={{ fontWeight: 600 }}>Quantity</span>

            <div className="pqtyControls" style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                type="button"
                onClick={decQty}
                disabled={busy || qty <= 1}
                className="pqtyBtn"
                aria-label="Decrease quantity"
              >
                −
              </button>

              <input
                type="number"
                min={1}
                max={stockMax || undefined}
                value={qty}
                onChange={onQtyInput}
                disabled={busy || outOfStock}
                className="pqtyInput"
                style={{ width: 60, textAlign: "center" }}
              />

              <button
                type="button"
                onClick={incQty}
                disabled={busy || outOfStock || (stockMax > 0 && qty >= stockMax)}
                className="pqtyBtn"
                aria-label="Increase quantity"
              >
                +
              </button>
            </div>

            {stockMax > 0 && (
              <span style={{ opacity: 0.7, fontSize: 13 }}>
                ({stockMax} available)
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="pactions" style={{ marginTop: 14 }}>
            <button
              className="pbtn pbtnPrimary"
              type="button"
              disabled={!chosenVariant || busy || outOfStock}
              onClick={handleOrderNow}
            >
              {busy ? "PLEASE WAIT..." : "Order Now"}
            </button>

            <button
              className="pbtn pbtnDark"
              type="button"
              disabled={!chosenVariant || busy || outOfStock}
              onClick={handleAddToCart}
            >
              {busy ? "PLEASE WAIT..." : "Add to Cart"}
            </button>
          </div>

          {/* Shipping & Returns */}
          <div className="psection paccordion">
            <button type="button" className="paccHead" onClick={() => setShipOpen((v) => !v)}>
              <span>Shipping &amp; Returns</span>
              <span className={`pchev ${shipOpen ? "open" : ""}`}>⌃</span>
            </button>
            {shipOpen && (
              <div className="paccBody">
                <p> free 15-day returns.</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
