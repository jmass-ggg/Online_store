import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Product.css";
import { apiFetch, joinUrl } from "../api";

const CART_KEY = "cart_items";

function toNumber(value) {
  if (value === null || value === undefined) return 0;
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const n = Number(String(value).trim());
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  const n = toNumber(value);
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
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

  const [shipOpen, setShipOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [toast, setToast] = useState("");
  const showToast = (msg) => {
    setToast(msg);
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(() => setToast(""), 2200);
  };

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

  const displayPrice = useMemo(() => {
    const p = selectedVariant?.price ?? defaultVariant?.price ?? 0;
    return toNumber(p);
  }, [selectedVariant, defaultVariant]);

  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      setError("");
      setProduct(null);
      setSelectedVariant(null);

      try {
        // ✅ relative path so Vite proxy works on ngrok
        const data = await apiFetch(`/product/slug/${encodeURIComponent(slug)}`);
        if (!alive) return;

        setProduct(data);

        // If backend returns "/uploads/..", keep it relative so it loads from ngrok origin
        const img = joinUrl(data.image_url || "");
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

  useEffect(() => {
    if (!product) return;
    if (selectedVariant) return;
    if (defaultVariant) setSelectedVariant(defaultVariant);
  }, [product, defaultVariant, selectedVariant]);

  const addToCart = ({ goCheckout = false } = {}) => {
    if (!product) return;

    const v = selectedVariant || defaultVariant;
    if (!v) return showToast("No sizes available.");
    if (toNumber(v.stock_quantity) <= 0) return showToast("This size is out of stock.");

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
    const idx = cart.findIndex((x) => x.product_id === item.product_id && x.variant_id === item.variant_id);
    if (idx >= 0) cart[idx].qty += 1;
    else cart.push(item);

    saveCart(cart);

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
              onError={(e) => (e.currentTarget.src = "/shoes.jpg")}
            />
          </div>
        </div>

        <aside className="pright">
          <h1 className="ptitle">{product.product_name}</h1>
          <p className="pcat">{product.product_category}</p>
          <p className="pprice">{formatMoney(displayPrice)}</p>

          <div className="psizeRow">
            <span className="psizeLabel">
              Select Size{" "}
              {(selectedVariant || defaultVariant)?.size ? (
                <span className="psizeChosen">({(selectedVariant || defaultVariant).size})</span>
              ) : null}
            </span>

            <button className="psizeGuide" type="button" onClick={() => showToast("Size guide coming soon")}>
              Size Guide
            </button>
          </div>

          <div className="psizes">
            {sizeOptions.length === 0 && <p className="pnote">No sizes available.</p>}

            {sizeOptions.map(({ size, variant }) => {
              const chosen = (selectedVariant || defaultVariant)?.id === variant.id;
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

          <div className="psection pship">
            <h3 className="psectionTitle">Shipping</h3>
            <p className="psectionText">You'll see our shipping options at checkout.</p>
          </div>

          <div className="psection pdesc">
            <p className="pdescText">
              {product.description ||
                "Inspired by the original AJ1, this edition maintains the iconic look you love."}
            </p>

            <ul className="pbullets">
              <li>
                Shown:{" "}
                {(selectedVariant || defaultVariant)?.color ? (selectedVariant || defaultVariant).color : "—"}
              </li>
              <li>Style: {(selectedVariant || defaultVariant)?.sku || "—"}</li>
            </ul>
          </div>

          <div className="psection paccordion">
            <button type="button" className="paccHead" onClick={() => setShipOpen((v) => !v)}>
              <span>Shipping &amp; Returns</span>
              <span className={`pchev ${shipOpen ? "open" : ""}`}>⌃</span>
            </button>

            {shipOpen && (
              <div className="paccBody">
                <p>Free standard shipping on orders $50+ and free 60-day returns.</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
