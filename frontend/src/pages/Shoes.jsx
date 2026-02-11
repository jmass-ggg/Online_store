import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Shoes.css";
import { apiFetch, joinUrl } from "../api";

const FOOTWEAR_CATEGORY = "Footwear";

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

function ProductCard({ p }) {
  const [activeIdx, setActiveIdx] = useState(0);

  const images = (p.images?.length ? p.images : [p.image]).filter(Boolean);
  const thumbs = images.slice(0, 5);
  const extraCount = Math.max(0, images.length - thumbs.length);
  const hero = images[activeIdx] || images[0] || "/shoes.jpg";

  return (
    <article className="plp-card">
      <Link to={`/product/${p.url_slug}`} className="plp-hit" aria-label={p.title} />

      <div className="plp-media" aria-hidden="true">
        <img
          src={hero}
          alt=""
          loading="lazy"
          onError={(e) => (e.currentTarget.src = "/shoes.jpg")}
        />
      </div>

      {thumbs.length > 1 && (
        <div className="plp-thumbs" aria-hidden="true">
          {thumbs.map((src, idx) => (
            <button
              key={`${src}-${idx}`}
              className={`plp-thumb ${idx === activeIdx ? "is-active" : ""}`}
              type="button"
              onMouseEnter={() => setActiveIdx(idx)}
              onFocus={() => setActiveIdx(idx)}
              tabIndex={-1}
            >
              <img src={src} alt="" loading="lazy" onError={(e) => (e.currentTarget.src = "/shoes.jpg")} />
            </button>
          ))}
          {extraCount > 0 && <span className="plp-more">+{extraCount}</span>}
        </div>
      )}

      <div className="plp-info">
        <div className="plp-title" title={p.title}>{p.title}</div>
        <div className="plp-meta">Men&apos;s Shoes</div>
        <div className="plp-price">{formatMoney(p.price)}</div>
      </div>
    </article>
  );
}

function ProductGrid({ products }) {
  return <div className="plp-grid">{products.map((p) => <ProductCard key={p.id} p={p} />)}</div>;
}

export default function Shoes() {
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  // ✅ profile dropdown state
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  const mappedProducts = useMemo(() => {
    return products.map((p) => {
      const image = joinUrl(p.image_url || "");

      const rawImages =
        (Array.isArray(p.images) && p.images) ||
        (Array.isArray(p.image_urls) && p.image_urls) ||
        [];

      const images = rawImages.length ? rawImages.map((u) => joinUrl(u)) : [image].filter(Boolean);
      const price = p.default_price ?? p.defaultPrice ?? p.price ?? p.base_price ?? "0.00";

      return {
        id: p.id,
        url_slug: p.url_slug,
        title: p.product_name,
        price,
        image,
        images,
      };
    });
  }, [products]);

  async function fetchProducts({ q = "" } = {}) {
    setLoading(true);
    setError("");

    try {
      const url = q.trim()
        ? `/product/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(FOOTWEAR_CATEGORY)}`
        : `/product/?category=${encodeURIComponent(FOOTWEAR_CATEGORY)}`;

      const data = await apiFetch(url);
      setProducts(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.message || "Something went wrong");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchProducts({ q: search }), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // ✅ close dropdown on outside click + ESC
  useEffect(() => {
    function onDocMouseDown(e) {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(e.target)) setProfileOpen(false);
    }
    function onEsc(e) {
      if (e.key === "Escape") setProfileOpen(false);
    }

    document.addEventListener("mousedown", onDocMouseDown);
    window.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      window.removeEventListener("keydown", onEsc);
    };
  }, []);

  function go(path) {
    setProfileOpen(false);
    navigate(path);
  }

  function logout() {
    setProfileOpen(false);
    // ✅ adjust these keys to match your auth
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  }

  return (
    <div className="shoes-page">
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <Link to="/" className="brand-logo">JAMES</Link>
          </div>

          <nav className="top-nav">
            <a href="#">Men</a>
            <a href="#">Women</a>
            <a href="#">Kids</a>
            <a href="#">Jordan</a>
            <a href="#">Collections</a>
            <a href="#" className="sale">Sale</a>
          </nav>

          <div className="header-actions">
            <div className="search">
              <span className="search-icon" aria-hidden="true">🔍</span>
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
              onClick={() => navigate("/checkout")}
              title="Cart / Checkout"
            >
              👜
            </button>

            {/* ✅ Profile dropdown */}
            <div className="profile-wrap" ref={profileRef}>
              <button
                className="profile-btn"
                type="button"
                aria-label="Account"
                aria-expanded={profileOpen}
                onClick={() => setProfileOpen((v) => !v)}
                title="Account"
              >
                <span className="profile-avatar">👤</span>
              </button>

              {profileOpen && (
                <div className="profile-menu" role="menu" aria-label="Account menu">
                  <button className="profile-item" type="button" role="menuitem" onClick={() => go("/account")}>
                    <span className="pi-ico">🙂</span>
                    <span>Manage My Account</span>
                  </button>

                  <button className="profile-item" type="button" role="menuitem" onClick={() => go("/orders")}>
                    <span className="pi-ico">🧾</span>
                    <span>My Orders</span>
                  </button>

                  <button className="profile-item" type="button" role="menuitem" onClick={() => go("/wishlist")}>
                    <span className="pi-ico">♡</span>
                    <span>My Wishlist &amp; Followed Stores</span>
                  </button>

                  <button className="profile-item" type="button" role="menuitem" onClick={() => go("/reviews")}>
                    <span className="pi-ico">⭐</span>
                    <span>My Reviews</span>
                  </button>

                  <button className="profile-item" type="button" role="menuitem" onClick={() => go("/returns")}>
                    <span className="pi-ico">↩</span>
                    <span>My Returns &amp; Cancellations</span>
                  </button>

                  <div className="profile-divider" />

                  <button className="profile-item danger" type="button" role="menuitem" onClick={logout}>
                    <span className="pi-ico">⎋</span>
                    <span>Log out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="wrap main-wrap">
        <section className="content">
          <div className="content-top">
            <h1 className="page-title">Footwear</h1>
          </div>

          {loading && <p className="state">Loading...</p>}
          {error && <p className="state error">{error}</p>}

          <ProductGrid products={mappedProducts} />

          {!loading && !error && mappedProducts.length === 0 && (
            <p className="state">No footwear products found.</p>
          )}
        </section>
      </main>
    </div>
  );
}
