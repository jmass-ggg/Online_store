// src/pages/Product.jsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./Product.css";
import { apiFetch, joinUrl } from "../api";

const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";

function toNumber(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    toNumber(value)
  );
}

// ---------- local cart helpers (IMPORTANT for your Checkout.jsx enrichment) ----------
function readLocalCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(CART_KEY) || "[]");
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function upsertLocalCartItem(nextItem) {
  const arr = readLocalCart();
  const vid = Number(nextItem.variant_id);

  const idx = arr.findIndex(
    (x) => Number(x?.variant_id ?? x?.variantId ?? x?.id) === vid
  );

  if (idx >= 0) {
    const prevQty = toNumber(arr[idx]?.quantity);
    arr[idx] = {
      ...arr[idx],
      ...nextItem,
      quantity: prevQty + toNumber(nextItem.quantity),
      updated_at: Date.now(),
    };
  } else {
    arr.push({ ...nextItem, updated_at: Date.now() });
  }

  localStorage.setItem(CART_KEY, JSON.stringify(arr));
}

// ---------- size sort ----------
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

  const [selectedColor, setSelectedColor] = useState("");
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

  // ---------- variants ----------
  const variants = useMemo(() => {
    if (!product) return [];
    const v = product.variants || product.ProductVariants || [];
    return Array.isArray(v) ? v : [];
  }, [product]);

  // unique colors (pick a representative variant per color)
  const colorOptions = useMemo(() => {
    const map = new Map();

    for (const v of variants) {
      const color = String(v?.color || "").trim();
      if (!color) continue;

      if (!map.has(color)) map.set(color, v);
      else {
        const cur = map.get(color);
        const vStock = toNumber(v.stock_quantity);
        const cStock = toNumber(cur.stock_quantity);
        if (vStock > 0 && cStock <= 0) map.set(color, v);
      }
    }

    return Array.from(map.entries()).map(([color, variant]) => ({ color, variant }));
  }, [variants]);

  // variants filtered by selected color
  const filteredVariants = useMemo(() => {
    if (!selectedColor) return variants;
    const pick = String(selectedColor).trim().toLowerCase();
    return variants.filter(
      (v) => String(v?.color || "").trim().toLowerCase() === pick
    );
  }, [variants, selectedColor]);

  // size options depend on filtered variants
  const sizeOptions = useMemo(() => {
    const map = new Map();

    for (const v of filteredVariants) {
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
  }, [filteredVariants]);

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

  const outOfStock = stockMax <= 0;

  // ---------- load product ----------
  useEffect(() => {
    let alive = true;

    async function load() {
      setLoading(true);
      setError("");
      setProduct(null);
      setSelectedVariant(null);
      setSelectedColor("");
      setQty(1);

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

  // pick default color after load (prefer in-stock)
  useEffect(() => {
    if (!product) return;
    if (selectedColor) return;
    if (colorOptions.length === 0) return;

    const inStockColor = colorOptions.find((x) => toNumber(x.variant.stock_quantity) > 0);
    setSelectedColor((inStockColor || colorOptions[0]).color);
  }, [product, colorOptions, selectedColor]);

  // when color changes, reset variant so defaultVariant applies for that color
  useEffect(() => {
    if (!product) return;
    setSelectedVariant(null);
  }, [selectedColor, product]);

  // keep qty within stock when variant changes
  useEffect(() => {
    if (!chosenVariant) return;
    const max = toNumber(chosenVariant.stock_quantity);
    setQty((q) => {
      const next = Math.max(1, toNumber(q));
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

  // qty controls
  const decQty = () => setQty((q) => Math.max(1, toNumber(q) - 1));
  const incQty = () => setQty((q) => (stockMax > 0 ? Math.min(stockMax, toNumber(q) + 1) : toNumber(q) + 1));
  const onQtyInput = (e) => {
    const n = Math.max(1, toNumber(e.target.value));
    setQty(stockMax > 0 ? Math.min(stockMax, n) : n);
  };

  // ✅ WORKING Add to Cart: hits backend + updates localStorage(cart_items)
  async function handleAddToCart() {
    const info = getVariantOrToast();
    if (!info) return;

    if (busy) return;
    setBusy(true);

    try {
      // backend API you shared: POST /cart/items
      await apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({ variant_id: info.variantId, quantity: info.safeQty }),
      });

      // IMPORTANT: Checkout.jsx uses localStorage cart_items to show name/image/size
      upsertLocalCartItem({
        variant_id: info.variantId,
        quantity: info.safeQty,
        price: toNumber(info.v.price),
        product_id: product.id,
        product_name: product.product_name,
        product_category: product.product_category,
        url_slug: product.url_slug,
        image_url: activeImg,
        size: info.v.size,
        color: info.v.color,
      });

      window.dispatchEvent(new Event("cart:updated"));
      showToast(`Added ${info.safeQty} to cart ✅`);
    } catch (e) {
      showToast(e?.message || "Failed to add to cart");
    } finally {
      setBusy(false);
    }
  }

  function handleOrderNow() {
    const info = getVariantOrToast();
    if (!info) return;

    const payload = {
      mode: "BUY_NOW",
      created_at: Date.now(),
      item: {
        variant_id: info.variantId,
        quantity: info.safeQty,
        product_id: product.id,
        product_name: product.product_name,
        product_category: product.product_category,
        url_slug: product.url_slug,
        image_url: activeImg,
        size: info.v.size,
        color: info.v.color,
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

          {/* Color */}
          {colorOptions.length > 0 && (
            <div className="pcolorBlock">
              <div className="pcolorRowTop">
                <span className="pcolorLabel">Color</span>
                <span className="pcolorChosen">{selectedColor || "—"}</span>
              </div>

              <div className="pcolors">
                {colorOptions.map(({ color }) => {
                  const chosen =
                    String(selectedColor).toLowerCase() === String(color).toLowerCase();
                  return (
                    <button
                      key={color}
                      type="button"
                      className={`pcolorBtn ${chosen ? "selected" : ""}`}
                      onClick={() => setSelectedColor(color)}
                      disabled={busy}
                      title={`Select color ${color}`}
                    >
                      {color}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

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

          {/* Quantity */}
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
              <span style={{ opacity: 0.7, fontSize: 13 }}>({stockMax} available)</span>
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
                <p>14 Days Free Returns</p>
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Description */}
      <div className="pdescBottom">
        <h2 className="pdescTitle">Description</h2>
        <p className="pdescTextBottom">
          {product.description ? product.description : "No description provided."}
        </p>
      </div>
    </div>
  );
}
