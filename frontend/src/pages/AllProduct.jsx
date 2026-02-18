import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./AllProduct.css";

/**
 * Backend:
 * - Default: /api/products?skip=0&limit=12
 * - You can set VITE_API_URL in .env (example: VITE_API_URL=http://localhost:8000)
 */
const API_BASE = import.meta.env.VITE_API_URL || "";
const PRODUCTS_ENDPOINT = `${API_BASE}/api/products`;
const PAGE_SIZE = 12;

const CART_KEY = "cart_items";

function money(n) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    Number(n || 0)
  );
}

function safeJsonParse(value, fallback) {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function normalizeProduct(p) {
  const id = p.id ?? p._id ?? crypto.randomUUID();
  const name = p.product_name ?? p.name ?? p.title ?? "Untitled Product";
  const price = Number(p.price ?? p.current_price ?? 0);
  const oldPrice = Number(p.old_price ?? p.previous_price ?? 0);
  const image =
    p.image_url ??
    p.image ??
    (Array.isArray(p.images) ? p.images?.[0] : null) ??
    "https://via.placeholder.com/800x800?text=Product";
  const slug = p.url_slug ?? p.slug ?? String(id);
  const category = p.product_category ?? p.category ?? "Other";
  const createdAt = p.created_at ?? p.date ?? null;

  return {
    id,
    name,
    price,
    oldPrice,
    image,
    slug,
    category,
    createdAt,
    spotlight: Boolean(p.spotlight),
  };
}

function discountPercent(price, oldPrice) {
  if (!oldPrice || oldPrice <= price) return 0;
  return Math.round(((oldPrice - price) / oldPrice) * 100);
}

// Fallback demo products (only used if API fails)
const DEMO_PRODUCTS = [
  {
    id: "1",
    name: "Signature Minimal Tee",
    price: 45,
    oldPrice: 60,
    image:
      "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
    slug: "signature-minimal-tee",
    category: "Apparel",
    spotlight: true,
    createdAt: "2023-11-01",
  },
  {
    id: "2",
    name: "Aluminum Desk Lamp",
    price: 120,
    oldPrice: 0,
    image:
      "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",
    slug: "aluminum-desk-lamp",
    category: "Lifestyle",
    spotlight: true,
    createdAt: "2023-11-05",
  },
  {
    id: "3",
    name: "Cognac Leather Wallet",
    price: 85,
    oldPrice: 95,
    image:
      "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=900&q=80",
    slug: "cognac-leather-wallet",
    category: "Accessories",
    spotlight: true,
    createdAt: "2023-10-20",
  },
  {
    id: "4",
    name: "Nylon Weekender Bag",
    price: 180,
    oldPrice: 210,
    image:
      "https://images.unsplash.com/photo-1547949003-9792a18a2601?auto=format&fit=crop&w=900&q=80",
    slug: "nylon-weekender-bag",
    category: "Accessories",
    spotlight: true,
    createdAt: "2023-11-12",
  },
  {
    id: "5",
    name: "Merino Wool Beanie",
    price: 35,
    oldPrice: 0,
    image:
      "https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?auto=format&fit=crop&w=900&q=80",
    slug: "merino-wool-beanie",
    category: "Apparel",
    spotlight: true,
    createdAt: "2023-11-02",
  },
  {
    id: "6",
    name: "Hardcover Journal",
    price: 32,
    oldPrice: 40,
    image:
      "https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=900&q=80",
    slug: "hardcover-journal",
    category: "Stationery",
    spotlight: true,
    createdAt: "2023-11-14",
  },
  {
    id: "7",
    name: "Stainless Water Bottle",
    price: 40,
    oldPrice: 0,
    image:
      "https://images.unsplash.com/photo-1602143399827-bd95951c3455?auto=format&fit=crop&w=900&q=80",
    slug: "stainless-water-bottle",
    category: "Lifestyle",
    spotlight: true,
    createdAt: "2023-11-15",
  },
  {
    id: "8",
    name: "Matte Black Pen",
    price: 22,
    oldPrice: 0,
    image:
      "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&w=900&q=80",
    slug: "matte-black-pen",
    category: "Stationery",
    spotlight: false,
    createdAt: "2023-11-04",
  },
];

export default function AllProduct() {
  const navigate = useNavigate();
  const gridRef = useRef(null);

  // Data state
  const [products, setProducts] = useState([]);
  const [hasMore, setHasMore] = useState(true);

  // UI state
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [errorHint, setErrorHint] = useState("");

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [currentCategory, setCurrentCategory] = useState("All");
  const [sortBy, setSortBy] = useState("newest"); // newest | price-low | price-high

  // Cart + toast
  const [cartCount, setCartCount] = useState(0);
  const [toasts, setToasts] = useState([]);

  // Initial load
  useEffect(() => {
    let alive = true;

    async function loadInitial() {
      setLoading(true);
      setErrorHint("");
      try {
        const url = new URL(PRODUCTS_ENDPOINT, window.location.origin);
        url.searchParams.set("skip", "0");
        url.searchParams.set("limit", String(PAGE_SIZE));

        const res = await fetch(url.toString(), { credentials: "include" });
        if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);

        const data = await res.json();
        const list = Array.isArray(data) ? data : data.items ?? data.products ?? [];
        const normalized = list.map(normalizeProduct);

        if (!alive) return;

        setProducts(normalized);
        setHasMore(normalized.length >= PAGE_SIZE);
      } catch (e) {
        if (!alive) return;
        setProducts(DEMO_PRODUCTS);
        setHasMore(false);
        setErrorHint("Using demo products (API not reachable). Set VITE_API_URL or verify /api/products.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    loadInitial();
    return () => {
      alive = false;
    };
  }, []);

  // Cart count from localStorage
  useEffect(() => {
    const cart = safeJsonParse(localStorage.getItem(CART_KEY), []);
    const total = (Array.isArray(cart) ? cart : []).reduce((acc, item) => acc + (item.quantity || 0), 0);
    setCartCount(total);
  }, []);

  const categories = useMemo(() => {
    const set = new Set(products.map((p) => p.category).filter(Boolean));
    return ["All", ...Array.from(set)];
  }, [products]);

  const spotlight = useMemo(() => {
    const flagged = products.filter((p) => p.spotlight);
    if (flagged.length >= 6) return flagged.slice(0, 8);
    return products.slice(0, 8);
  }, [products]);

  const filteredProducts = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();

    let list = products;

    if (currentCategory !== "All") {
      list = list.filter((p) => p.category === currentCategory);
    }

    if (q) {
      list = list.filter((p) => {
        const name = (p.name || "").toLowerCase();
        const cat = (p.category || "").toLowerCase();
        return name.includes(q) || cat.includes(q);
      });
    }

    // sort
    if (sortBy === "price-low") {
      list = [...list].sort((a, b) => a.price - b.price);
    } else if (sortBy === "price-high") {
      list = [...list].sort((a, b) => b.price - a.price);
    } else {
      // newest
      list = [...list].sort((a, b) => {
        const da = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const db = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return db - da;
      });
    }

    return list;
  }, [products, currentCategory, searchQuery, sortBy]);

  const resultCountText = useMemo(() => {
    if (!searchQuery && currentCategory === "All") return `Showing ${filteredProducts.length} items`;
    return `Showing ${filteredProducts.length} items (filtered)`;
  }, [filteredProducts.length, searchQuery, currentCategory]);

  function showToast(message) {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, message }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2800);
  }

  function addToCart(product) {
    const cart = safeJsonParse(localStorage.getItem(CART_KEY), []);
    const list = Array.isArray(cart) ? cart : [];

    const existing = list.find((i) => String(i.id) === String(product.id));
    if (existing) {
      existing.quantity = (existing.quantity || 1) + 1;
    } else {
      // Store in a shape that works with your Cart page
      list.push({
        id: product.id,
        productName: product.name,
        price: product.price,
        oldPrice: product.oldPrice || 0,
        imageUrl: product.image,
        url_slug: product.slug,
        product_category: product.category,
        quantity: 1,
        inStock: true,
      });
    }

    localStorage.setItem(CART_KEY, JSON.stringify(list));
    const total = list.reduce((acc, item) => acc + (item.quantity || 0), 0);
    setCartCount(total);
    showToast(`${product.name} added to cart!`);
  }

  function openProduct(p) {
    navigate(`/product/${p.slug}`);
  }

  function goCart() {
    navigate("/cart");
  }

  function resetFilters() {
    setCurrentCategory("All");
    setSearchQuery("");
    setSortBy("newest");
  }

  async function loadMore() {
    if (!hasMore || loadingMore) return;

    setLoadingMore(true);
    try {
      const url = new URL(PRODUCTS_ENDPOINT, window.location.origin);
      url.searchParams.set("skip", String(products.length));
      url.searchParams.set("limit", String(PAGE_SIZE));

      const res = await fetch(url.toString(), { credentials: "include" });
      if (!res.ok) throw new Error(`Fetch more failed: ${res.status}`);

      const data = await res.json();
      const list = Array.isArray(data) ? data : data.items ?? data.products ?? [];
      const normalized = list.map(normalizeProduct);

      setProducts((prev) => [...prev, ...normalized]);
      setHasMore(normalized.length >= PAGE_SIZE);
    } catch {
      setHasMore(false);
    } finally {
      setLoadingMore(false);
    }
  }

  function scrollToGrid() {
    gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
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
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M3 6h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M16 10a4 4 0 0 1-8 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="apCartCount">{cartCount}</span>
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
            <span className="apSearchIcon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2.5" />
                <path d="m21 21-4.3-4.3" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              </svg>
            </span>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for products, categories, or styles..."
              aria-label="Search products"
            />
          </div>

          {errorHint ? <div className="apHint">{errorHint}</div> : null}
        </section>

        {/* SPOTLIGHT */}
        <section className="apSpotlight">
          <div className="apSectionHead">
            <div>
              <h2>Spotlight</h2>
              <p>Hand-picked favorites of the week</p>
            </div>
            <button className="apLink" type="button" onClick={scrollToGrid}>
              View All
            </button>
          </div>

          <div className="apSpotRow">
            {loading ? (
              Array.from({ length: 7 }).map((_, i) => (
                <div key={i} className="apSpotItem skeletonBox" />
              ))
            ) : (
              spotlight.map((p) => (
                <button
                  key={p.id}
                  className="apSpotItem"
                  type="button"
                  onClick={() => openProduct(p)}
                  aria-label={`Open ${p.name}`}
                >
                  <div className="apSpotImg">
                    <img src={p.image} alt={p.name} />
                  </div>
                  <div className="apSpotName" title={p.name}>{p.name}</div>
                  <div className="apSpotPrice">{money(p.price)}</div>
                </button>
              ))
            )}
          </div>
        </section>

        {/* CATEGORIES */}
        <section className="apCats">
          <h3>Shop by Category</h3>
          <div className="apCatGrid">
            {categories.slice(0, 12).map((cat) => (
              <button
                key={cat}
                type="button"
                className={`apCatTile ${currentCategory === cat ? "active" : ""}`}
                onClick={() => {
                  setCurrentCategory(cat);
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

          {/* Empty state */}
          {!loading && filteredProducts.length === 0 ? (
            <div className="apEmpty">
              <div className="apEmptyIcon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
                  <path d="m21 21-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <h4>No results found</h4>
              <p>Try adjusting your search or filters to find what you're looking for.</p>
              <button className="apClear" type="button" onClick={resetFilters}>
                Clear all filters
              </button>
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
                : filteredProducts.map((p) => {
                    const off = discountPercent(p.price, p.oldPrice);
                    return (
                      <article key={p.id} className="apCard">
                        <button
                          type="button"
                          className="apMedia"
                          onClick={() => openProduct(p)}
                          aria-label={`Open ${p.name}`}
                        >
                          <img src={p.image} alt={p.name} />
                          {off > 0 ? <span className="apBadge">-{off}%</span> : null}
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
                        </button>

                        <div className="apInfo">
                          <div className="apCat">{p.category}</div>
                          <button type="button" className="apName" onClick={() => openProduct(p)}>
                            {p.name}
                          </button>

                          <div className="apPriceRow">
                            <div className="apPrice">{money(p.price)}</div>
                            {p.oldPrice && p.oldPrice > p.price ? (
                              <div className="apOld">{money(p.oldPrice)}</div>
                            ) : null}
                          </div>
                        </div>
                      </article>
                    );
                  })}
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

      {/* FOOTER */}
      <footer className="apFooter">
        <div className="apFootGrid">
          <div>
            <div className="apFootBrand">JAMES</div>
            <p className="apFootText">
              Defining the standard of modern retail through thoughtful design and premium quality.
            </p>
          </div>

          <div>
            <div className="apFootTitle">Shop</div>
            <ul>
              <li><button type="button" onClick={scrollToGrid}>New Arrivals</button></li>
              <li><button type="button" onClick={scrollToGrid}>Best Sellers</button></li>
              <li><button type="button" onClick={scrollToGrid}>Gift Cards</button></li>
            </ul>
          </div>

          <div>
            <div className="apFootTitle">Support</div>
            <ul>
              <li><button type="button">Order Tracking</button></li>
              <li><button type="button">Shipping Policy</button></li>
              <li><button type="button">Returns & Exchanges</button></li>
            </ul>
          </div>

          <div>
            <div className="apFootTitle">Connect</div>
            <div className="apSocial">
              <button type="button">IG</button>
              <button type="button">TW</button>
            </div>
          </div>
        </div>

        <div className="apCopy">
          © {new Date().getFullYear()} JAMES. All rights reserved.
        </div>
      </footer>

      {/* TOASTS */}
      <div className="apToastWrap" aria-live="polite" aria-atomic="true">
        {toasts.map((t) => (
          <div key={t.id} className="apToast">
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}
