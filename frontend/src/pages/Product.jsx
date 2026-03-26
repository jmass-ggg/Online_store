import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import "./Product.css";
import "./Shoes.css";
import { apiFetch, joinUrl } from "../api";

const BUY_NOW_KEY = "buy_now_item";
const CART_KEY = "cart_items";
const FALLBACK_IMAGE = "/shoes.jpg";
const SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"];

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function toId(value) {
  return String(value ?? "").trim();
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

function getVariantId(variant) {
  return toId(variant?.variant_id ?? variant?.variantId ?? variant?.id);
}

function getProductId(product) {
  return toId(product?.product_id ?? product?.productId ?? product?.id);
}

function normalizeVariant(variant) {
  if (!variant || typeof variant !== "object") return null;

  return {
    ...variant,
    _variantId: getVariantId(variant),
    _price: toNumber(variant?.price),
    _stock: toNumber(
      variant?.stock_quantity ?? variant?.stock ?? variant?.quantity ?? 0
    ),
    _color: String(variant?.color || "").trim(),
    _size: String(variant?.size || "").trim(),
  };
}

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
  const nextVariantId = toId(
    nextItem?.variant_id ?? nextItem?.variantId ?? nextItem?.id
  );

  const idx = arr.findIndex((item) => {
    const itemVariantId = toId(item?.variant_id ?? item?.variantId ?? item?.id);
    return itemVariantId === nextVariantId;
  });

  if (idx >= 0) {
    const prevQty = toNumber(arr[idx]?.quantity, 1);
    const nextQty = prevQty + toNumber(nextItem?.quantity, 1);
    const stock = toNumber(nextItem?.stock ?? arr[idx]?.stock, 0);

    arr[idx] = {
      ...arr[idx],
      ...nextItem,
      id: nextVariantId,
      variant_id: nextVariantId,
      inStock: stock > 0,
      stock,
      quantity: stock > 0 ? Math.min(nextQty, stock) : nextQty,
      selected: true,
      updated_at: Date.now(),
    };
  } else {
    const stock = toNumber(nextItem?.stock, 0);

    arr.push({
      ...nextItem,
      id: nextVariantId,
      variant_id: nextVariantId,
      inStock: stock > 0,
      stock,
      selected: true,
      updated_at: Date.now(),
    });
  }

  localStorage.setItem(CART_KEY, JSON.stringify(arr));
}

function sizeRank(size) {
  const normalized = String(size || "").trim().toUpperCase();
  const known = SIZE_ORDER.indexOf(normalized);
  if (known >= 0) return known;

  const numeric = Number(normalized);
  if (Number.isFinite(numeric)) return 100 + numeric;

  return 1000;
}

export default function Product() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [activeImg, setActiveImg] = useState(FALLBACK_IMAGE);

  const [selectedColor, setSelectedColor] = useState("");
  const [selectedVariantId, setSelectedVariantId] = useState("");
  const [qty, setQty] = useState(1);

  const [shipOpen, setShipOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [toast, setToast] = useState("");

  const [search, setSearch] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);
  const toastTimeoutRef = useRef(null);

  function showToast(message) {
    setToast(message);
    window.clearTimeout(toastTimeoutRef.current);
    toastTimeoutRef.current = window.setTimeout(() => {
      setToast("");
    }, 2200);
  }

  const variants = useMemo(() => {
    if (!product) return [];
    const raw = product?.variants || product?.ProductVariants || [];
    if (!Array.isArray(raw)) return [];
    return raw.map(normalizeVariant).filter(Boolean);
  }, [product]);

  const colorOptions = useMemo(() => {
    const map = new Map();

    for (const variant of variants) {
      const color = variant?._color;
      if (!color) continue;

      if (!map.has(color)) {
        map.set(color, variant);
        continue;
      }

      const current = map.get(color);
      const nextInStock = variant._stock > 0;
      const currentInStock = current._stock > 0;

      if (nextInStock && !currentInStock) {
        map.set(color, variant);
      }
    }

    return Array.from(map.entries()).map(([color, variant]) => ({
      color,
      variant,
    }));
  }, [variants]);

  const filteredVariants = useMemo(() => {
    if (!selectedColor) return variants;

    const targetColor = String(selectedColor).trim().toLowerCase();

    return variants.filter(
      (variant) => variant._color.toLowerCase() === targetColor
    );
  }, [variants, selectedColor]);

  const sizeOptions = useMemo(() => {
    const map = new Map();

    for (const variant of filteredVariants) {
      const size = variant?._size;
      if (!size) continue;

      if (!map.has(size)) {
        map.set(size, variant);
        continue;
      }

      const current = map.get(size);
      const nextInStock = variant._stock > 0;
      const currentInStock = current._stock > 0;

      if (nextInStock && !currentInStock) {
        map.set(size, variant);
        continue;
      }

      if (nextInStock === currentInStock && variant._price < current._price) {
        map.set(size, variant);
      }
    }

    const result = Array.from(map.entries()).map(([size, variant]) => ({
      size,
      variant,
    }));

    result.sort((a, b) => {
      const rankA = sizeRank(a.size);
      const rankB = sizeRank(b.size);

      if (rankA !== rankB) return rankA - rankB;

      return a.size.localeCompare(b.size, undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });

    return result;
  }, [filteredVariants]);

  const defaultVariant = useMemo(() => {
    if (sizeOptions.length === 0) return null;
    return (
      sizeOptions.find((entry) => entry.variant._stock > 0)?.variant ||
      sizeOptions[0]?.variant ||
      null
    );
  }, [sizeOptions]);

  const selectedVariant = useMemo(() => {
    const wantedId = toId(selectedVariantId);
    if (!wantedId) return null;

    return (
      filteredVariants.find((variant) => variant._variantId === wantedId) ||
      variants.find((variant) => variant._variantId === wantedId) ||
      null
    );
  }, [filteredVariants, variants, selectedVariantId]);

  const chosenVariant = selectedVariant || defaultVariant || null;
  const displayPrice = chosenVariant?._price ?? 0;
  const stockMax = chosenVariant?._stock ?? 0;
  const outOfStock = stockMax <= 0;

  useEffect(() => {
    let alive = true;

    async function loadProduct() {
      setLoading(true);
      setError("");
      setProduct(null);
      setSelectedColor("");
      setSelectedVariantId("");
      setQty(1);

      try {
        const data = await apiFetch(`/product/slug/${encodeURIComponent(slug)}`);
        if (!alive) return;

        setProduct(data);
        setActiveImg(joinUrl(data?.image_url || "") || FALLBACK_IMAGE);
      } catch (err) {
        if (!alive) return;
        setError(err?.message || "Failed to load product");
      } finally {
        if (alive) setLoading(false);
      }
    }

    loadProduct();

    return () => {
      alive = false;
    };
  }, [slug]);

  useEffect(() => {
    if (!product) return;
    if (selectedColor) return;
    if (colorOptions.length === 0) return;

    const inStockColor = colorOptions.find((entry) => entry.variant._stock > 0);
    setSelectedColor((inStockColor || colorOptions[0]).color);
  }, [product, colorOptions, selectedColor]);

  useEffect(() => {
    setSelectedVariantId("");
    setQty(1);
  }, [selectedColor]);

  useEffect(() => {
    if (!chosenVariant) return;

    const max = chosenVariant._stock;
    setQty((currentQty) => {
      const safeQty = Math.max(1, toNumber(currentQty));
      return max > 0 ? Math.min(safeQty, max) : 1;
    });
  }, [chosenVariant?._variantId, chosenVariant?._stock]);

  useEffect(() => {
    function onDocMouseDown(event) {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    }

    function onEsc(event) {
      if (event.key === "Escape") setProfileOpen(false);
    }

    document.addEventListener("mousedown", onDocMouseDown);
    window.addEventListener("keydown", onEsc);

    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      window.removeEventListener("keydown", onEsc);
    };
  }, []);

  useEffect(() => {
    return () => {
      window.clearTimeout(toastTimeoutRef.current);
    };
  }, []);

  function go(path) {
    setProfileOpen(false);
    navigate(path);
  }

  function logout() {
    setProfileOpen(false);
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  }

  function getVariantOrToast() {
    if (!product) return null;

    const variant = chosenVariant;
    if (!variant) {
      showToast("No sizes available.");
      return null;
    }

    const variantId = getVariantId(variant);
    if (!variantId) {
      showToast("Invalid variant.");
      return null;
    }

    const stock = toNumber(variant._stock);
    if (stock <= 0) {
      showToast("This size is out of stock.");
      return null;
    }

    const safeQty = Math.max(1, Math.min(toNumber(qty), stock));
    if (safeQty !== qty) {
      setQty(safeQty);
    }

    return {
      variant,
      variantId,
      stock,
      safeQty,
    };
  }

  function decQty() {
    setQty((currentQty) => Math.max(1, toNumber(currentQty) - 1));
  }

  function incQty() {
    setQty((currentQty) => {
      const nextQty = toNumber(currentQty) + 1;
      return stockMax > 0 ? Math.min(stockMax, nextQty) : nextQty;
    });
  }

  function onQtyInput(event) {
    const nextQty = Math.max(1, toNumber(event.target.value));
    setQty(stockMax > 0 ? Math.min(stockMax, nextQty) : nextQty);
  }

  async function handleAddToCart() {
    const info = getVariantOrToast();
    if (!info) return;
    if (busy) return;

    setBusy(true);

    try {
      await apiFetch("/cart/items", {
        method: "POST",
        body: JSON.stringify({
          variant_id: info.variantId,
          quantity: info.safeQty,
        }),
      });

      upsertLocalCartItem({
        id: info.variantId,
        variant_id: info.variantId,
        inStock: info.stock > 0,
        stock: info.stock,
        quantity: info.safeQty,
        price: toNumber(info.variant._price),
        product_id: getProductId(product),
        product_name: product?.product_name || "",
        product_category: product?.product_category || "",
        url_slug: product?.url_slug || slug,
        image_url: activeImg,
        size: info.variant._size || "",
        color: info.variant._color || "",
      });

      window.dispatchEvent(new Event("cart:updated"));
      showToast(`Added ${info.safeQty} to cart ✅`);
    } catch (err) {
      showToast(err?.message || "Failed to add to cart");
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
        product_id: getProductId(product),
        product_name: product?.product_name || "",
        product_category: product?.product_category || "",
        url_slug: product?.url_slug || slug,
        image_url: activeImg,
        size: info.variant._size,
        color: info.variant._color,
        price: toNumber(info.variant._price),
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
    <div className="shoes-page">
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <Link to="/" className="brand-logo">
              JAMES
            </Link>
          </div>

          <nav className="top-nav">
            <a href="#">Men</a>
            <a href="#">Women</a>
            <a href="#">Kids</a>
            <a href="#">Jordan</a>
            <a href="#">Collections</a>
            <a href="#" className="sale">
              Sale
            </a>
          </nav>

          <div className="header-actions">
            <div className="search">
              <span className="search-icon" aria-hidden="true">
                🔍
              </span>
              <input
                type="text"
                placeholder="Search footwear..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <button
              className="icon-btn"
              type="button"
              aria-label="Favorites"
              onClick={() => navigate("/wishlist")}
              title="Wishlist"
            >
              ♡
            </button>

            <button
              className="icon-btn"
              type="button"
              aria-label="Bag"
              onClick={() => navigate("/cart")}
              title="Cart"
            >
              👜
            </button>

            <div className="profile-wrap" ref={profileRef}>
              <button
                className="profile-btn"
                type="button"
                aria-label="Account"
                aria-expanded={profileOpen}
                onClick={() => setProfileOpen((open) => !open)}
                title="Account"
              >
                <span className="profile-avatar">👤</span>
              </button>

              {profileOpen && (
                <div className="profile-menu" role="menu" aria-label="Account menu">
                  <button
                    className="profile-item"
                    type="button"
                    role="menuitem"
                    onClick={() => go("/account")}
                  >
                    <span className="pi-ico">🙂</span>
                    <span>Manage My Account</span>
                  </button>

                  <button
                    className="profile-item"
                    type="button"
                    role="menuitem"
                    onClick={() => go("/orders")}
                  >
                    <span className="pi-ico">🧾</span>
                    <span>My Orders</span>
                  </button>

                  <button
                    className="profile-item"
                    type="button"
                    role="menuitem"
                    onClick={() => go("/wishlist")}
                  >
                    <span className="pi-ico">♡</span>
                    <span>My Wishlist &amp; Followed Stores</span>
                  </button>

                  <button
                    className="profile-item"
                    type="button"
                    role="menuitem"
                    onClick={() => go("/reviews")}
                  >
                    <span className="pi-ico">⭐</span>
                    <span>My Reviews</span>
                  </button>

                  <button
                    className="profile-item"
                    type="button"
                    role="menuitem"
                    onClick={() => go("/returns")}
                  >
                    <span className="pi-ico">↩</span>
                    <span>My Returns &amp; Cancellations</span>
                  </button>

                  <div className="profile-divider" />

                  <button
                    className="profile-item danger"
                    type="button"
                    role="menuitem"
                    onClick={logout}
                  >
                    <span className="pi-ico">⎋</span>
                    <span>Log out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="pwrap">
        {toast && <div className="ptoast">{toast}</div>}

        <div className="pgrid">
          <div className="pleft">
            <div className="pbreadcrumb">
              Home / {product?.product_category || "Products"} / {product?.product_name}
            </div>

            <div className="pmain">
              <img
                src={activeImg}
                alt={product?.product_name || "Product image"}
                onError={(e) => {
                  e.currentTarget.src = FALLBACK_IMAGE;
                }}
              />
            </div>
          </div>

          <aside className="pright">
            <h1 className="ptitle">{product?.product_name}</h1>
            <p className="pcat">{product?.product_category}</p>
            <p className="pprice">{formatMoney(displayPrice)}</p>

            {colorOptions.length > 0 && (
              <div className="pcolorBlock">
                <div className="pcolorRowTop">
                  <span className="pcolorLabel">Color</span>
                  <span className="pcolorChosen">{selectedColor || "—"}</span>
                </div>

                <div className="pcolors">
                  {colorOptions.map(({ color }) => {
                    const isChosen =
                      String(selectedColor).toLowerCase() ===
                      String(color).toLowerCase();

                    return (
                      <button
                        key={color}
                        type="button"
                        className={`pcolorBtn ${isChosen ? "selected" : ""}`}
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

            <div className="psizes">
              {sizeOptions.map(({ size, variant }) => {
                const isChosen =
                  !!chosenVariant?._variantId &&
                  chosenVariant._variantId === variant._variantId;

                const isOut = variant._stock <= 0;

                return (
                  <button
                    key={variant._variantId || `${variant._color}-${variant._size}`}
                    type="button"
                    className={`psizeBtn ${isChosen ? "selected" : ""}`}
                    disabled={isOut || busy}
                    onClick={() => setSelectedVariantId(variant._variantId)}
                    title={isOut ? "Out of stock" : `Select size ${size}`}
                  >
                    {size}
                  </button>
                );
              })}
            </div>

            <div
              className="pqtyRow"
              style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 14 }}
            >
              <span style={{ fontWeight: 600 }}>Quantity</span>

              <div
                className="pqtyControls"
                style={{ display: "flex", alignItems: "center", gap: 10 }}
              >
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

            <div className="psection paccordion">
              <button
                type="button"
                className="paccHead"
                onClick={() => setShipOpen((open) => !open)}
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

        <div className="pdescBottom">
          <h2 className="pdescTitle">Description</h2>
          <p className="pdescTextBottom">
            {product?.description || "No description provided."}
          </p>
        </div>
      </div>
    </div>
  );
}