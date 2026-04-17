import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Shoes.css";
import { apiFetch, joinUrl } from "../api";

function toNumber(value) {
  if (value === null || value === undefined) return 0;
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

function getPrimaryImage(images = []) {
  if (!Array.isArray(images) || images.length === 0) return "";

  const sorted = [...images].sort((a, b) => {
    if (a?.is_primary && !b?.is_primary) return -1;
    if (!a?.is_primary && b?.is_primary) return 1;
    return (a?.sort_order ?? 9999) - (b?.sort_order ?? 9999);
  });

  return sorted[0]?.image_url || "";
}

function getAllImages(images = []) {
  if (!Array.isArray(images)) return [];

  return [...images]
    .sort((a, b) => {
      if (a?.is_primary && !b?.is_primary) return -1;
      if (!a?.is_primary && b?.is_primary) return 1;
      return (a?.sort_order ?? 9999) - (b?.sort_order ?? 9999);
    })
    .map((img) => joinUrl(img.image_url))
    .filter(Boolean);
}

function getDefaultPrice(product) {
  if (product.default_price) return product.default_price;

  if (Array.isArray(product.variants) && product.variants.length > 0) {
    const active = product.variants.filter((v) => v.is_active);
    if (active.length > 0) return active[0].price;
  }

  return "0.00";
}

function ProductCard({ product }) {
  const hero =
    (Array.isArray(product.images) && product.images[0]) ||
    product.image ||
    "/shoes.jpg";

  return (
    <article className="plp-card">
      <Link
        to={`/product/${product.url_slug}`}
        className="plp-hit"
        aria-label={product.title}
      />

      <div className="plp-media">
        <img
          src={hero}
          alt={product.title}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = "/shoes.jpg";
          }}
        />
      </div>

      <div className="plp-info">
        <h3 className="plp-title" title={product.title}>
          {product.title}
        </h3>

        <div className="plp-bottomRow">
          <div className="plp-price">{formatMoney(product.price)}</div>
        </div>
      </div>
    </article>
  );
}

function ProductGrid({ products }) {
  return (
    <div className="plp-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

export default function CategoryProducts({
  category,
  pageTitle,
  className = "",
}) {
  const navigate = useNavigate();
  const profileRef = useRef(null);

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);

  const mappedProducts = useMemo(() => {
    return products.map((p) => {
      const primaryImage = joinUrl(getPrimaryImage(p.images));
      const allImages = getAllImages(p.images);
      const price = getDefaultPrice(p);

      return {
        id: p.id,
        url_slug: p.url_slug,
        title: p.product_name,
        price,
        image: primaryImage,
        images: allImages,
      };
    });
  }, [products]);

  async function fetchProducts({ q = "" } = {}) {
    setLoading(true);
    setError("");

    try {
      const url = q.trim()
        ? `/product/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`
        : `/product/?category=${encodeURIComponent(category)}`;

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
  }, [category]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts({ q: search });
    }, 350);

    return () => clearTimeout(timer);
  }, [search, category]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(e.target)) {
        setProfileOpen(false);
      }
    }

    function handleEsc(e) {
      if (e.key === "Escape") setProfileOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleEsc);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleEsc);
    };
  }, []);

  function go(path) {
    setProfileOpen(false);
    navigate(path);
  }

  function logout() {
    setProfileOpen(false);
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_token");
    localStorage.removeItem("refresh_token");
    navigate("/login");
  }

  return (
    <div className={`shoes-page ${className}`}>
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <Link to="/" className="brand-logo">
              JAMES
            </Link>
          </div>

          <nav className="top-nav">
            <Link to="/shoes">Shoes</Link>
            <Link to="/clothes">Clothes</Link>
            <Link to="/jewellery">Jewellery</Link>
            <Link to="/accessories">Accessories</Link>
          </nav>

          <div className="header-actions">
            <div className="search">
              <span className="search-icon" aria-hidden="true">
                🔍
              </span>
              <input
                type="text"
                placeholder={`Search ${pageTitle.toLowerCase()}...`}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <button
              className="icon-btn"
              type="button"
              aria-label="Wishlist"
              onClick={() => navigate("/wishlist")}
            >
              ♡
            </button>

            <button
              className="icon-btn"
              type="button"
              aria-label="Cart"
              onClick={() => navigate("/cart")}
            >
              👜
            </button>

            <div className="profile-wrap" ref={profileRef}>
              <button
                className="profile-btn"
                type="button"
                aria-label="Account"
                aria-expanded={profileOpen}
                onClick={() => setProfileOpen((prev) => !prev)}
              >
                <span className="profile-avatar">👤</span>
              </button>

              {profileOpen && (
                <div className="profile-menu" role="menu" aria-label="Account menu">
                  <button
                    className="profile-item"
                    type="button"
                    onClick={() => go("/account")}
                  >
                    Manage My Account
                  </button>

                  <button
                    className="profile-item"
                    type="button"
                    onClick={() => go("/orders")}
                  >
                    My Orders
                  </button>

                  <div className="profile-divider" />

                  <button
                    className="profile-item danger"
                    type="button"
                    onClick={logout}
                  >
                    Log out
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
            <h1 className="page-title">{pageTitle}</h1>
            
          </div>

          {loading && <p className="state">Loading products...</p>}
          {error && <p className="state error">{error}</p>}

          {!loading && !error && mappedProducts.length > 0 && (
            <ProductGrid products={mappedProducts} />
          )}

          {!loading && !error && mappedProducts.length === 0 && (
            <p className="state">No {pageTitle.toLowerCase()} products found.</p>
          )}
        </section>
      </main>
    </div>
  );
}