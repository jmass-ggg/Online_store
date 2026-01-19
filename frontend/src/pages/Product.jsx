// Product.jsx (COPY + PASTE)
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Product.css";

const API_BASE = "http://127.0.0.1:8000";
const CART_KEY = "cart_items";

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
    // optional: let other components (navbar/cart badge) know
    window.dispatchEvent(new Event("cart:updated"));
  };

  // ------- load product -------
  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      setError("");
      setSelectedVariant(null);

      try {
        // ✅ requires backend route: GET /product/slug/{slug}
        const res = await fetch(
          `${API_BASE}/product/slug/${encodeURIComponent(slug)}`
        );
        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        if (!alive) return;

        setProduct(data);

        const img = data.image_url?.startsWith("http")
          ? data.image_url
          : `${API_BASE}${data.image_url || ""}`;

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

  // ✅ supports BOTH: `variants` OR `ProductVariants`
  const variants = useMemo(() => {
    if (!product) return [];
    return product.variants || product.ProductVariants || [];
  }, [product]);

  // ✅ unique sizes (one button per size)
  const sizes = useMemo(() => {
    const uniq = new Map();
    for (const v of variants) {
      const size = (v.size || "").trim();
      if (!size) continue;
      if (!uniq.has(size)) uniq.set(size, v);
    }
    return Array.from(uniq.values());
  }, [variants]);

  const displayPrice = useMemo(() => {
    const p =
      selectedVariant?.price ??
      product?.price ??
      product?.base_price ??
      0;
    const n = Number(p || 0);
    return Number.isFinite(n) ? n : 0;
  }, [selectedVariant, product]);

  // ------- actions -------
  const addToCart = ({ buyNow = false } = {}) => {
    if (!product) return;

    if (!selectedVariant) {
      showToast("Please select a size first.");
      return;
    }

    const item = {
      product_id: product.id,
      url_slug: product.url_slug,
      product_name: product.product_name,
      product_category: product.product_category,

      // ✅ store absolute image url so it always renders in cart
      image_url: activeImg,

      variant_id: selectedVariant.id,
      size: selectedVariant.size,
      color: selectedVariant.color || null,
      price: Number(
        selectedVariant.price ?? product.price ?? product.base_price ?? 0
      ),
      qty: 1,
    };

    const cart = getCart();

    // merge same product + same variant
    const idx = cart.findIndex(
      (x) => x.product_id === item.product_id && x.variant_id === item.variant_id
    );

    if (idx >= 0) cart[idx].qty += 1;
    else cart.push(item);

    saveCart(cart);

    if (buyNow) {
      showToast("Added! Redirecting to checkout...");
      setTimeout(() => navigate("/checkout"), 600); // change route if needed
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
      {/* Toast */}
      {toast && <div className="ptoast">{toast}</div>}

      <div className="pgrid">
        {/* LEFT: image */}
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

        {/* RIGHT: info */}
        <aside className="pright">
          <h1 className="ptitle">{product.product_name}</h1>
          <p className="pcat">{product.product_category}</p>

          <p className="pprice">${displayPrice.toFixed(0)}</p>

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
            {sizes.length === 0 && (
              <p className="pnote">
                No sizes available. (Add variants for this product)
              </p>
            )}

            {sizes.map((v) => (
              <button
                key={v.id}
                type="button"
                className={`psizeBtn ${
                  selectedVariant?.id === v.id ? "selected" : ""
                }`}
                disabled={Number(v.stock_quantity) <= 0}
                onClick={() => setSelectedVariant(v)}
                title={
                  Number(v.stock_quantity) <= 0
                    ? "Out of stock"
                    : `Select size ${v.size}`
                }
              >
                {v.size}
              </button>
            ))}
          </div>

          {/* Buttons */}
          <div className="pactions">
            <button
              className="pbtn pbtnPrimary"
              type="button"
              disabled={!selectedVariant}
              onClick={() => addToCart({ buyNow: true })}
            >
              Order Now
            </button>

            <button
              className="pbtn pbtnDark"
              type="button"
              disabled={!selectedVariant}
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
