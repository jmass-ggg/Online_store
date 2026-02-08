// Product.jsx (UPDATED — redirects to checkout immediately on "Order Now")
// COPY + PASTE
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Product.css";

// ✅ Use env if available (Vite): VITE_API_BASE="https://xxxx.ngrok.app"
const API_BASE = import.meta?.env?.VITE_API_BASE || "http://127.0.0.1:8000";
const CART_KEY = "cart_items";

function joinUrl(base, path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  const b = base.endsWith("/") ? base.slice(0, -1) : base;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

function toNumber(value) {
  if (value === null || value === undefined) return 0;
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const n = Number(String(value).trim());
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  const n = toNumber(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(n);
}

const SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"];
function sizeRank(size) {
  const s = String(size || "").trim().toUpperCase();
  const idx = SIZE_ORDER.indexOf(s);
  if (idx >= 0) return idx;

  const num = Number(s); // numeric sizes: 6, 7.5, 10, etc.
  if (Number.isFinite(num)) return 100 + num;

  return 1000;
}

export default function Product() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [activeImg, setActiveImg] = useState("/shoes.jpg");
  const [selectedVariant, setSelectedVariant] = useState(null);

  const [shipOpen, setShipOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // toast
  const [toast, setToast] = useState("");
  const showToast = (msg) => {
    setToast(msg);
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(""), 2200);
  };

  // ------- cart helpers -------
  const getCart = () => {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
    } catch {
      return [];
    }
  };

  const saveCart = (items) => {
    localStorage.setItem(CART_KEY, JSON.stringify(items));
    window.dispatchEvent(new Event("cart:updated"));
  };

  // ✅ supports BOTH: `variants` OR `ProductVariants`
  const variants = useMemo(() => {
    if (!product) return [];
    const v = product.variants || product.ProductVariants || [];
    return Array.isArray(v) ? v : [];
  }, [product]);

  // ✅ build ONE option per size (prefer in-stock, then lowest price)
  const sizeOptions = useMemo(() => {
    const map = new Map(); // size -> variant

    for (const v of variants) {
      const size = String(v?.size || "").trim();
      if (!size) continue;

      const stock = toNumber(v.stock_quantity);
      const price = toNumber(v.price);

      if (!map.has(size)) {
        map.set(size, v);
        continue;
      }

      const cur = map.get(size);
      const curStock = toNumber(cur.stock_quantity);
      const curPrice = toNumber(cur.price);

      const vIn = stock > 0;
      const cIn = curStock > 0;

      if (vIn && !cIn) map.set(size, v);
      else if (vIn === cIn && price < curPrice) map.set(size, v);
    }

    const arr = Array.from(map.entries()).map(([size, variant]) => ({
      size,
      variant,
    }));

    arr.sort((a, b) => {
      const ra = sizeRank(a.size);
      const rb = sizeRank(b.size);
      if (ra !== rb) return ra - rb;
      return a.size.localeCompare(b.size, undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });

    return arr;
  }, [variants]);

  // ✅ default variant: first in-stock option, else first option, else null
  const defaultVariant = useMemo(() => {
    if (sizeOptions.length === 0) return null;
    const inStock = sizeOptions.find(
      (x) => toNumber(x.variant.stock_quantity) > 0
    );
    return (inStock || sizeOptions[0]).variant;
  }, [sizeOptions]);

  // ✅ display price: selectedVariant → defaultVariant → 0
  const displayPrice = useMemo(() => {
    const p = selectedVariant?.price ?? defaultVariant?.price ?? 0;
    return toNumber(p);
  }, [selectedVariant, defaultVariant]);

  // ------- load product -------
  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      setError("");
      setProduct(null);
      setSelectedVariant(null);

      try {
        const res = await fetch(
          `${API_BASE}/product/slug/${encodeURIComponent(slug)}`
        );
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (!alive) return;

        setProduct(data);

        const img = joinUrl(API_BASE, data.image_url || "");
        setActiveImg(img || "/shoes.jpg");
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

  // ✅ auto-select default so price is never $0
  useEffect(() => {
    if (!product) return;
    if (selectedVariant) return;
    if (defaultVariant) setSelectedVariant(defaultVariant);
  }, [product, defaultVariant, selectedVariant]);

  // ------- actions -------
  const addToCart = ({ goCheckout = false } = {}) => {
    if (!product) return;

    const v = selectedVariant || defaultVariant;

    if (!v) {
      showToast("No sizes available.");
      return;
    }
    if (toNumber(v.stock_quantity) <= 0) {
      showToast("This size is out of stock.");
      return;
    }

    const item = {
      product_id: product.id,
      url_slug: product.url_slug,
      product_name: product.product_name,
      product_category: product.product_category,
      image_url: activeImg,
      variant_id: v.id,
      size: v.size,
      color: v.color || null,
      price: toNumber(v.price),
      qty: 1,
    };

    const cart = getCart();
    const idx = cart.findIndex(
      (x) => x.product_id === item.product_id && x.variant_id === item.variant_id
    );
    if (idx >= 0) cart[idx].qty += 1;
    else cart.push(item);

    saveCart(cart);

    // ✅ IMPORTANT: go to checkout immediately when "Order Now"
    if (goCheckout) {
      navigate("/checkout");
      return;
    }

    showToast("Added to bag ✅");
  };

  const handleFavorite = () => {
    if (!product) return;
    showToast(`Saved to favorites: ${product.product_name}`);
  };

  // ------- render states -------
  if (loading) return <div className="pwrap">Loading...</div>;
  if (error) return <div className="pwrap error">{error}</div>;
  if (!product) return null;

  return (
    <div className="pwrap">
      {toast && <div className="ptoast">{toast}</div>}

      <div className="pgrid">
        {/* LEFT */}
        <div className="pleft">
          <div className="pbreadcrumb">
            Home / {product.product_category || "Products"} /{" "}
            {product.product_name}
          </div>

          <div className="pmain">
            <img
              src={activeImg}
              alt={product.product_name}
              onError={(e) => {
                e.currentTarget.src = "/shoes.jpg";
              }}
            />
          </div>
        </div>

        {/* RIGHT */}
        <aside className="pright">
          <h1 className="ptitle">{product.product_name}</h1>
          <p className="pcat">{product.product_category}</p>

          <p className="pprice">{formatMoney(displayPrice)}</p>

          <div className="psizeRow">
            <span className="psizeLabel">
              Select Size{" "}
              {(selectedVariant || defaultVariant)?.size ? (
                <span className="psizeChosen">
                  ({(selectedVariant || defaultVariant).size})
                </span>
              ) : null}
            </span>

            <button
              className="psizeGuide"
              type="button"
              onClick={() => showToast("Size guide coming soon")}
            >
              Size Guide
            </button>
          </div>

          <div className="psizes">
            {sizeOptions.length === 0 && (
              <p className="pnote">
                No sizes available. (Add variants for this product)
              </p>
            )}

            {sizeOptions.map(({ size, variant }) => {
              const chosen =
                (selectedVariant || defaultVariant)?.id === variant.id;
              const out = toNumber(variant.stock_quantity) <= 0;

              return (
                <button
                  key={variant.id}
                  type="button"
                  className={`psizeBtn ${chosen ? "selected" : ""}`}
                  disabled={out}
                  onClick={() => setSelectedVariant(variant)}
                  title={out ? "Out of stock" : `Select size ${size}`}
                >
                  {size}
                </button>
              );
            })}
          </div>

          <div className="pactions">
            {/* ✅ goes to checkout */}
            <button
              className="pbtn pbtnPrimary"
              type="button"
              disabled={!selectedVariant && !defaultVariant}
              onClick={() => addToCart({ goCheckout: true })}
            >
              Order Now
            </button>

            <button
              className="pbtn pbtnDark"
              type="button"
              disabled={!selectedVariant && !defaultVariant}
              onClick={() => addToCart({ goCheckout: false })}
            >
              Add to Cart
            </button>
          </div>

          <button className="pfav" type="button" onClick={handleFavorite}>
            Favorite ♡
          </button>

          {/* Bottom sections */}
          <div className="psection pship">
            <h3 className="psectionTitle">Shipping</h3>
            <p className="psectionText">
              You'll see our shipping options at checkout.
            </p>

            <div className="ppickup">
              <div className="ppickupTitle">Free Pickup</div>
              <button
                type="button"
                className="plink"
                onClick={() => showToast("Find a Store coming soon")}
              >
                Find a Store
              </button>
            </div>
          </div>

          <div className="psection pdesc">
            <p className="pdescText">
              {product.description ||
                "Inspired by the original AJ1, this edition maintains the iconic look you love."}
            </p>

            <ul className="pbullets">
              <li>
                Shown:{" "}
                {(selectedVariant || defaultVariant)?.color
                  ? (selectedVariant || defaultVariant).color
                  : "—"}
              </li>
              <li>Style: {(selectedVariant || defaultVariant)?.sku || "—"}</li>
            </ul>

            <button
              type="button"
              className="plink pdetails"
              onClick={() => showToast("Product details coming soon")}
            >
              View Product Details
            </button>
          </div>

          <div className="psection paccordion">
            <button
              type="button"
              className="paccHead"
              onClick={() => setShipOpen((v) => !v)}
            >
              <span>Shipping &amp; Returns</span>
              <span className={`pchev ${shipOpen ? "open" : ""}`}>⌃</span>
            </button>

            {shipOpen && (
              <div className="paccBody">
                <p>
                  Free standard shipping on orders $50+ and free 60-day returns.{" "}
                  <button
                    type="button"
                    className="plinkInline"
                    onClick={() => showToast("Learn more coming soon")}
                  >
                    Learn more.
                  </button>
                </p>
                <p className="plinkInline">Return policy exclusions apply.</p>
                <p className="plinkInline">
                  Pick-up available at select stores.
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
