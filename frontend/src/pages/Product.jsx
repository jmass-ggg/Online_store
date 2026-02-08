// Product.jsx (COPY + PASTE)
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
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  const n = toNumber(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(n);
}

function pickDefaultVariant(list) {
  if (!Array.isArray(list) || list.length === 0) return null;
  // ✅ default: first IN-STOCK variant, otherwise first variant
  const inStock = list.find((v) => toNumber(v?.stock_quantity) > 0);
  return inStock || list[0] || null;
}

export default function Product() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [activeImg, setActiveImg] = useState("/shoes.jpg");
  const [selectedVariant, setSelectedVariant] = useState(null);

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

        // image
        const img = joinUrl(API_BASE, data.image_url || "");
        setActiveImg(img || "/shoes.jpg");

        // ✅ IMPORTANT: set default variant so price is NOT $0
        const list = data.variants || data.ProductVariants || [];
        setSelectedVariant(pickDefaultVariant(list));
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

  // normalize variants
  const variants = useMemo(() => {
    if (!product) return [];
    const list = product.variants || product.ProductVariants || [];
    return Array.isArray(list) ? list : [];
  }, [product]);

  // ✅ One button per size (prefer in-stock variant for same size)
  const sizeOptions = useMemo(() => {
    const bySize = new Map();

    for (const v of variants) {
      const size = (v?.size || "").trim();
      if (!size) continue;

      const curr = bySize.get(size);
      const vStock = toNumber(v?.stock_quantity);
      const currStock = toNumber(curr?.stock_quantity);

      // prefer in-stock over out-of-stock; otherwise keep first
      if (!curr) bySize.set(size, v);
      else if (currStock <= 0 && vStock > 0) bySize.set(size, v);
    }

    // stable sort like Nike (alphabetical / numeric friendly)
    return Array.from(bySize.entries())
      .sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))
      .map(([, v]) => v);
  }, [variants]);

  // ✅ price always comes from variant
  const displayPrice = useMemo(() => {
    return toNumber(selectedVariant?.price);
  }, [selectedVariant]);

  // ------- actions -------
  const addToCart = ({ buyNow = false } = {}) => {
    if (!product) return;

    if (!selectedVariant) {
      showToast("Please select a size first.");
      return;
    }

    if (toNumber(selectedVariant.stock_quantity) <= 0) {
      showToast("This size is out of stock.");
      return;
    }

    const item = {
      product_id: product.id,
      url_slug: product.url_slug,
      product_name: product.product_name,
      product_category: product.product_category,
      image_url: activeImg,

      variant_id: selectedVariant.id,
      size: selectedVariant.size,
      color: selectedVariant.color || null,
      price: toNumber(selectedVariant.price),
      qty: 1,
    };

    const cart = getCart();

    const idx = cart.findIndex(
      (x) => x.product_id === item.product_id && x.variant_id === item.variant_id
    );

    if (idx >= 0) cart[idx].qty += 1;
    else cart.push(item);

    saveCart(cart);

    if (buyNow) {
      showToast("Added! Redirecting to checkout...");
      setTimeout(() => navigate("/checkout"), 600);
    } else {
      showToast("Added to bag ✅");
    }
  };

  const handleFavorite = () => {
    if (!product) return;
    showToast(`Saved to favorites: ${product.product_name}`);
  };

  const openSizeGuide = () => showToast("Size guide coming soon");

  // ------- render states -------
  if (loading) return <div className="pwrap">Loading...</div>;
  if (error) return <div className="pwrap error">{error}</div>;
  if (!product) return null;

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
              onError={(e) => {
                e.currentTarget.src = "/shoes.jpg";
              }}
            />
          </div>
        </div>

        <aside className="pright">
          <h1 className="ptitle">{product.product_name}</h1>
          <p className="pcat">{product.product_category}</p>

          {/* ✅ FIXED: always shows variant price (default selected on load) */}
          <p className="pprice">{formatMoney(displayPrice)}</p>

          <div className="psizeRow">
            <span className="psizeLabel">
              Select Size{" "}
              {selectedVariant?.size ? (
                <span className="psizeChosen">({selectedVariant.size})</span>
              ) : null}
            </span>

            <button className="psizeGuide" type="button" onClick={openSizeGuide}>
              Size Guide
            </button>
          </div>

          <div className="psizes">
            {sizeOptions.length === 0 && (
              <p className="pnote">
                No sizes available. (Add variants for this product)
              </p>
            )}

            {sizeOptions.map((v) => {
              const out = toNumber(v.stock_quantity) <= 0;
              const isSel = selectedVariant?.id === v.id;

              return (
                <button
                  key={v.id}
                  type="button"
                  className={`psizeBtn ${isSel ? "selected" : ""}`}
                  disabled={out}
                  onClick={() => setSelectedVariant(v)}
                  title={out ? "Out of stock" : `Select size ${v.size}`}
                >
                  {v.size}
                </button>
              );
            })}
          </div>

          <div className="pactions">
            <button
              className="pbtn pbtnPrimary"
              type="button"
              disabled={!selectedVariant || toNumber(selectedVariant?.stock_quantity) <= 0}
              onClick={() => addToCart({ buyNow: true })}
            >
              Order Now
            </button>

            <button
              className="pbtn pbtnDark"
              type="button"
              disabled={!selectedVariant || toNumber(selectedVariant?.stock_quantity) <= 0}
              onClick={() => addToCart({ buyNow: false })}
            >
              Add to Cart
            </button>
          </div>

          <button className="pfav" type="button" onClick={handleFavorite}>
            Favorite ♡
          </button>

          <div className="pinfo">
            <div className="pinfoRow">
              <span>Delivery</span>
              <span>Free</span>
            </div>
            <div className="pinfoRow">
              <span>Returns</span>
              <span>30 days</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
