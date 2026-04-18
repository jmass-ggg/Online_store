import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch, joinUrl } from "../api";
import StoreTopBar from "./components/cart/StoreTopBar";
import "./Product.css";

const FALLBACK_IMAGE = "/shoes.jpg";
const BUY_NOW_KEY = "buy_now_item";

function toNumber(value) {
  if (value === null || value === undefined || value === "") return 0;
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  const n = toNumber(value);
  return new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2,
  }).format(n);
}

function sortImages(images = []) {
  if (!Array.isArray(images)) return [];

  return [...images].sort((a, b) => {
    if (a?.is_primary && !b?.is_primary) return -1;
    if (!a?.is_primary && b?.is_primary) return 1;
    return (a?.sort_order ?? 9999) - (b?.sort_order ?? 9999);
  });
}

function normalizeImages(images = []) {
  return sortImages(images)
    .map((img) => ({
      id: String(img?.id || ""),
      url: joinUrl(img?.image_url || ""),
      isPrimary: !!img?.is_primary,
      sortOrder: img?.sort_order ?? 9999,
    }))
    .filter((img) => img.url);
}

function normalizeVariants(variants = []) {
  if (!Array.isArray(variants)) return [];

  return variants
    .filter((v) => v?.is_active)
    .map((v) => ({
      id: String(v?.id || "").trim(),
      sku: String(v?.sku || "").trim(),
      size: String(v?.size || "").trim(),
      color: String(v?.color || "").trim(),
      price: toNumber(v?.price),
      stock: toNumber(v?.stock_quantity),
      stock_quantity: toNumber(v?.stock_quantity),
      isActive: !!v?.is_active,
    }));
}

function upsertLocalCartItem(item) {
  try {
    const raw = localStorage.getItem("cart_items");
    const parsed = JSON.parse(raw || "[]");
    const current = Array.isArray(parsed) ? parsed : [];

    const index = current.findIndex((entry) => entry.variant_id === item.variant_id);

    if (index >= 0) {
      current[index] = {
        ...current[index],
        ...item,
        quantity: current[index].quantity + item.quantity,
      };
    } else {
      current.push(item);
    }

    localStorage.setItem("cart_items", JSON.stringify(current));
  } catch {
    localStorage.setItem("cart_items", JSON.stringify([item]));
  }
}

export default function Product() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const toastTimeoutRef = useRef(null);

  const [search, setSearch] = useState("");
  const [product, setProduct] = useState(null);
  const [activeImg, setActiveImg] = useState(FALLBACK_IMAGE);
  const [selectedVariantId, setSelectedVariantId] = useState("");
  const [qty, setQty] = useState(1);
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [shipOpen, setShipOpen] = useState(true);
  const [error, setError] = useState("");

  function showToast(message) {
    setToast(message);
    window.clearTimeout(toastTimeoutRef.current);
    toastTimeoutRef.current = window.setTimeout(() => {
      setToast("");
    }, 2200);
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    const q = search.trim();
    if (!q) return;
    navigate(`/products?q=${encodeURIComponent(q)}`);
  }

  const images = useMemo(() => normalizeImages(product?.images || []), [product]);
  const variants = useMemo(() => normalizeVariants(product?.variants || []), [product]);

  const sizeOptions = useMemo(() => {
    return [...variants].sort((a, b) => {
      if (a.stock > 0 && b.stock <= 0) return -1;
      if (a.stock <= 0 && b.stock > 0) return 1;
      return String(a.size).localeCompare(String(b.size), undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });
  }, [variants]);

  const chosenVariant = useMemo(() => {
    return sizeOptions.find((variant) => variant.id === selectedVariantId) || null;
  }, [sizeOptions, selectedVariantId]);

  const displayPrice = chosenVariant?.price ?? sizeOptions[0]?.price ?? 0;
  const stockMax = chosenVariant?.stock ?? 0;
  const outOfStock = !!chosenVariant && stockMax <= 0;

  useEffect(() => {
    let alive = true;

    async function loadProduct() {
      setLoading(true);
      setError("");

      try {
        const data = await apiFetch(`/product/slug/${encodeURIComponent(slug)}`);
        if (!alive) return;

        setProduct(data);

        const sortedImages = normalizeImages(data?.images || []);
        setActiveImg(sortedImages[0]?.url || FALLBACK_IMAGE);

        const normalizedVariants = normalizeVariants(data?.variants || []);
        const firstInStock = normalizedVariants.find((v) => v.stock > 0);
        const firstAny = normalizedVariants[0];

        setSelectedVariantId(firstInStock?.id || firstAny?.id || "");
        setQty(1);
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
    if (!chosenVariant) return;

    setQty((current) => {
      const safeQty = Math.max(1, toNumber(current));
      return chosenVariant.stock > 0 ? Math.min(safeQty, chosenVariant.stock) : 1;
    });
  }, [chosenVariant?.id, chosenVariant?.stock]);

  useEffect(() => {
    return () => {
      window.clearTimeout(toastTimeoutRef.current);
    };
  }, []);

  function getVariantOrToast() {
    if (!product) return null;

    if (!chosenVariant) {
      showToast("Please select a size.");
      return null;
    }

    if (!chosenVariant.id) {
      showToast("Invalid variant.");
      return null;
    }

    if (chosenVariant.stock <= 0) {
      showToast("This size is out of stock.");
      return null;
    }

    const safeQty = Math.max(1, Math.min(toNumber(qty), chosenVariant.stock));
    if (safeQty !== qty) setQty(safeQty);

    return {
      variant: chosenVariant,
      variantId: String(chosenVariant.id).trim(),
      stock: chosenVariant.stock,
      safeQty,
    };
  }

  function decQty() {
    setQty((current) => Math.max(1, toNumber(current) - 1));
  }

  function incQty() {
    setQty((current) => {
      const next = toNumber(current) + 1;
      return stockMax > 0 ? Math.min(next, stockMax) : next;
    });
  }

  function onQtyInput(event) {
    const nextQty = Math.max(1, toNumber(event.target.value));
    setQty(stockMax > 0 ? Math.min(stockMax, nextQty) : nextQty);
  }

  async function handleAddToCart() {
    const info = getVariantOrToast();
    if (!info || busy) return;

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
        product_id: product?.id,
        product_name: product?.product_name || "",
        product_category: product?.product_category || "",
        url_slug: product?.url_slug || slug,
        image_url: activeImg,
        size: info.variant.size || "",
        color: info.variant.color || "",
        price: info.variant.price,
        stock: info.stock,
        stock_quantity: info.stock,
        sku: info.variant.sku || "",
        inStock: info.stock > 0,
        quantity: info.safeQty,
      });

      window.dispatchEvent(new Event("cart:updated"));
      showToast(`Added ${info.safeQty} to cart`);
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
        product_id: String(product?.id || "").trim(),
        product_name: product?.product_name || "",
        product_category: product?.product_category || "",
        url_slug: product?.url_slug || slug || "",
        image_url: activeImg,
        size: info.variant.size || "",
        color: info.variant.color || "",
        price: info.variant.price,
        sku: info.variant.sku || "",
        stock_quantity: info.stock,
      },
    };

    localStorage.removeItem("buy_now_payload");
    localStorage.setItem(BUY_NOW_KEY, JSON.stringify(payload));
    window.dispatchEvent(new Event("buy_now:updated"));

    console.log("BUY_NOW SAVED:", payload);

    navigate("/checkout?mode=buy_now");
  }

  if (loading) {
    return (
      <div className="productPage">
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/wishlist"
          profilePath="/login"
        />
        <main className="pwrap">
          <div className="pstate">Loading...</div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="productPage">
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/wishlist"
          profilePath="/login"
        />
        <main className="pwrap">
          <div className="pstate perror">{error}</div>
        </main>
      </div>
    );
  }

  if (!product) return null;

  return (
    <div className="productPage">
      <StoreTopBar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearchSubmit}
        searchPlaceholder="Search footwear..."
        bagPath="/cart"
        wishlistPath="/wishlist"
        profilePath="/login"
      />

      <main className="pwrap">
        {toast && <div className="ptoast">{toast}</div>}

        <div className="pgrid">
          <section className="pleft">
            <div className="pbreadcrumb">
              Home / {product?.product_category || "Products"} / {product?.product_name}
            </div>

            <div className="pgallery">
              <div className="pthumbs">
                {images.map((img, index) => {
                  const isActive = activeImg === img.url;

                  return (
                    <button
                      key={img.id || `${img.url}-${index}`}
                      type="button"
                      className={`pthumb ${isActive ? "active" : ""}`}
                      onClick={() => setActiveImg(img.url)}
                      aria-label={`View image ${index + 1}`}
                    >
                      <img
                        src={img.url}
                        alt={`${product?.product_name || "Product"} ${index + 1}`}
                        onError={(e) => {
                          e.currentTarget.src = FALLBACK_IMAGE;
                        }}
                      />
                    </button>
                  );
                })}
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
          </section>

          <aside className="pright">
            <div className="pinfoTop">
              <h1 className="ptitle">{product?.product_name}</h1>
              <p className="paudience">
                {product?.target_audience ? `${product.target_audience}'s ` : ""}
                {product?.product_category}
              </p>
              <p className="pprice">{formatMoney(displayPrice)}</p>
              {chosenVariant?.id ? (
                <p className="pnote">Variant ID: {chosenVariant.id}</p>
              ) : null}
            </div>

            <div className="psizeBlock">
              <div className="poptionTop">
                <span className="poptionLabel">Select Size</span>
                <span className="poptionChosen">
                  {chosenVariant?.size || "Choose one"}
                </span>
              </div>

              <div className="psizes">
                {sizeOptions.map((variant) => {
                  const isChosen = chosenVariant?.id === variant.id;
                  const isOut = variant.stock <= 0;

                  return (
                    <button
                      key={variant.id}
                      type="button"
                      className={`psizeBtn ${isChosen ? "selected" : ""}`}
                      disabled={isOut || busy}
                      onClick={() => setSelectedVariantId(variant.id)}
                      title={isOut ? "Out of stock" : `Select size ${variant.size}`}
                    >
                      {variant.size}
                    </button>
                  );
                })}
              </div>

              {sizeOptions.length === 0 && (
                <p className="pnote">No sizes available.</p>
              )}
            </div>

            <div className="pqtyRow">
              <span className="pqtyLabel">Quantity</span>

              <div className="pqtyControls">
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

              {stockMax > 0 ? (
                <span className="pstockNote">{stockMax} available</span>
              ) : (
                <span className="pstockNote out">Out of stock</span>
              )}
            </div>

            <div className="pactions">
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
                  <p>Orders are usually processed within 1–2 business days.</p>
                </div>
              )}
            </div>
          </aside>
        </div>

        <section className="pdescBottom">
          <h2 className="pdescTitle">Description</h2>
          <p className="pdescTextBottom">
            {product?.description || "No description provided."}
          </p>
        </section>
      </main>
    </div>
  );
}