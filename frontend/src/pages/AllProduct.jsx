// src/pages/AllProduct.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./AllProduct.css";
import { apiFetch, joinUrl } from "../api";

const PAGE_SIZE = 12;
const CART_KEY = "cart_items";

function money(n) {
  const num = Number(n || 0);
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
}

function safeJsonParse(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function normalizeProduct(p) {
  return {
    id: p?.id ?? makeId(),
    name: p?.product_name ?? "Untitled Product",
    slug: p?.url_slug ?? String(p?.id ?? makeId()),
    category: p?.product_category ?? "Other",
    price: Number(p?.default_price ?? 0),
    image: joinUrl(p?.image_url || ""),
    status: p?.status ?? "active",
  };
}

export default function AllProduct() {
  const navigate = useNavigate();
  const gridRef = useRef(null);

  const [products, setProducts] = useState([]);
  const [hasMore, setHasMore] = useState(true);

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [errorHint, setErrorHint] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [serverCategory, setServerCategory] = useState("All");
  const [sortBy, setSortBy] = useState("newest");

  const [cartCount, setCartCount] = useState(0);
  const [toasts, setToasts] = useState([]);

  // cart count
  useEffect(() => {
    const cart = safeJsonParse(localStorage.getItem(CART_KEY), []);
    const total = (Array.isArray(cart) ? cart : []).reduce(
      (acc, item) => acc + (item.quantity || 0),
      0
    );
    setCartCount(total);
  }, []);

  async function fetchProducts({ reset }) {
    try {
      setErrorHint("");
      if (reset) setLoading(true);

      const skip = reset ? 0 : products.length;

      // ✅ FastAPI route you confirmed: /product/
      let path = `/product/?skip=${skip}&limit=${PAGE_SIZE}`;
      if (serverCategory !== "All") path += `&category=${encodeURIComponent(serverCategory)}`;

      const data = await apiFetch(path);
      const list = Array.isArray(data) ? data : data?.items ?? [];
      const normalized = list.map(normalizeProduct);

      setProducts((prev) => (reset ? normalized : [...prev, ...normalized]));
      setHasMore(normalized.length === PAGE_SIZE);
    } catch (e) {
      setProducts([]);
      setHasMore(false);
      setErrorHint(e?.message || "Failed to load products");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }

  // initial + category change
  useEffect(() => {
    fetchProducts({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverCategory]);

  const categories = useMemo(() => {
    const set = new Set(products.map((p) => p.category).filter(Boolean));
    return ["All", ...Array.from(set)];
  }, [products]);

  const filteredProducts = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    let list = products;

    if (q) {
      list = list.filter((p) => {
        const name = (p.name || "").toLowerCase();
        const cat = (p.category || "").toLowerCase();
        return name.includes(q) || cat.includes(q);
      });
    }

    if (sortBy === "price-low") return [...list].sort((a, b) => a.price - b.price);
    if (sortBy === "price-high") return [...list].sort((a, b) => b.price - a.price);
    return list; // newest = backend order
  }, [products, searchQuery, sortBy]);

  const resultCountText = useMemo(
    () => `Showing ${filteredProducts.length} items`,
    [filteredProducts.length]
  );

  function showToast(message) {
    const id = makeId();
    setToasts((prev) => [...prev, { id, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 2400);
  }

  function addToCart(product) {
    const cart = safeJsonParse(localStorage.getItem(CART_KEY), []);
    const list = Array.isArray(cart) ? cart : [];

    const existing = list.find((i) => String(i.id) === String(product.id));
    if (existing) existing.quantity = (existing.quantity || 1) + 1;
    else {
      list.push({
        id: product.id,
        productName: product.name,
        price: product.price,
        imageUrl: product.image,
        quantity: 1,
        inStock: product.status === "active",
      });
    }

    localStorage.setItem(CART_KEY, JSON.stringify(list));
    setCartCount(list.reduce((acc, item) => acc + (item.quantity || 0), 0));
    showToast(`${product.name} added to cart`);
  }

  function openProduct(p) {
    navigate(`/product/${p.slug}`);
  }

  function goCart() {
    navigate("/cart");
  }

  function scrollToGrid() {
    gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function loadMore() {
    if (!hasMore || loadingMore || loading) return;
    setLoadingMore(true);
    await fetchProducts({ reset: false });
  }

  return (
    <div className="ap">
      {/* NAV */}
      <nav className="apNav">
        <div className="apNavLeft">
          <button className="apBrand" onClick={() => navigate("/")} type="button">
            JAMES
          </button>
          <div className="apLinks">
            <button type="button" onClick={scrollToGrid}>New Arrivals</button>
            <button type="button" onClick={scrollToGrid}>Best Sellers</button>
            <button type="button" onClick={scrollToGrid}>Collections</button>
          </div>
        </div>

        <button className="apCartBtn" type="button" onClick={goCart} aria-label="Open cart">
          👜 <span className="apCartCount">{cartCount}</span>
        </button>
      </nav>

      <main>
        {/* HERO */}
        <section className="apHero">
          <h1 className="apHeroTitle">JAMES</h1>
          <p className="apHeroSub">
            Curated essentials for the modern lifestyle. Minimal design, maximal impact.
          </p>

          <div className="apSearchWrap">
            <span className="apSearchIcon" aria-hidden="true">🔎</span>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for products, categories, or styles..."
              aria-label="Search products"
            />
          </div>

          {errorHint ? <div className="apHint">{errorHint}</div> : null}
        </section>

        {/* CATEGORIES */}
        <section className="apCats">
          <h3>Shop by Category</h3>
          <div className="apCatGrid">
            {categories.slice(0, 12).map((cat) => (
              <button
                key={cat}
                type="button"
                className={`apCatTile ${serverCategory === cat ? "active" : ""}`}
                onClick={() => {
                  setServerCategory(cat);
                  scrollToGrid();
                }}
              >
                {cat.toUpperCase()}
              </button>
            ))}
          </div>
        </section>

        {/* PRODUCT GRID */}
        <section className="apFeed" ref={gridRef}>
          <div className="apFeedHead">
            <div>
              <h2>Just For You</h2>
              <p>{resultCountText}</p>
            </div>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              aria-label="Sort products"
            >
              <option value="newest">Newest Arrivals</option>
              <option value="price-low">Price: Low to High</option>
              <option value="price-high">Price: High to Low</option>
            </select>
          </div>

          {!loading && filteredProducts.length === 0 ? (
            <div className="apEmpty">
              <h4>No results found</h4>
              <p>Try adjusting your search.</p>
            </div>
          ) : (
            <div className="apGrid">
              {loading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="apCard skeletonCard">
                      <div className="skeletonMedia" />
                      <div className="skeletonText" />
                      <div className="skeletonText w70" />
                      <div className="skeletonText w50" />
                    </div>
                  ))
                : filteredProducts.map((p) => (
                    <article key={p.id} className="apCard">
                      <div
                        className="apMedia"
                        onClick={() => openProduct(p)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") openProduct(p);
                        }}
                      >
                        <img src={p.image} alt={p.name} />
                        <button
                          type="button"
                          className="apAdd"
                          onClick={(e) => {
                            e.stopPropagation();
                            addToCart(p);
                          }}
                        >
                          Add to Cart
                        </button>
                      </div>

                      <div className="apInfo">
                        <div className="apCat">{p.category}</div>
                        <button type="button" className="apName" onClick={() => openProduct(p)}>
                          {p.name}
                        </button>
                        <div className="apPriceRow">
                          <div className="apPrice">{money(p.price)}</div>
                        </div>
                      </div>
                    </article>
                  ))}
            </div>
          )}

          <div className="apLoadMoreWrap">
            <button
              className="apLoadMore"
              type="button"
              onClick={loadMore}
              disabled={!hasMore || loading || loadingMore}
            >
              {loadingMore ? "Loading..." : hasMore ? "Load More Products" : "No More Products"}
            </button>
          </div>
        </section>
      </main>

      {/* TOASTS */}
      <div className="apToastWrap" aria-live="polite" aria-atomic="true">
        {toasts.map((t) => (
          <div key={t.id} className="apToast">{t.message}</div>
        ))}
      </div>
    </div>
  );
}
