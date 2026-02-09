import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);
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
        <img src={hero} alt="" loading="lazy" onError={(e) => (e.currentTarget.src = "/shoes.jpg")} />
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
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

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
      // ✅ relative paths (proxy handles backend)
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

  return (
    <div className="shoes-page">
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <a href="#" className="brand-logo">JAMES</a>
          </div>

          <nav className="top-nav">
            <a href="#">Men</a><a href="#">Women</a><a href="#">Kids</a><a href="#">Jordan</a>
            <a href="#">Collections</a><a href="#" className="sale">Sale</a>
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
            <button className="icon-btn" type="button" aria-label="Favorites">♡</button>
            <button className="icon-btn" type="button" aria-label="Bag">👜</button>
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
