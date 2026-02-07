import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import "./Shoes.css";

const API_BASE = "http://127.0.0.1:8000";
const FOOTWEAR_CATEGORY = "Footwear";

function normalizeUrl(u) {
  if (!u) return "";
  return u.startsWith("http") ? u : `${API_BASE}${u}`;
}

function ProductCard({ p }) {
  const images = (p.images?.length ? p.images : [p.image]).filter(Boolean);
  const thumbs = images.slice(0, 5);
  const extraCount = Math.max(0, images.length - thumbs.length);

  const [activeIdx, setActiveIdx] = useState(0);
  const hero = images[activeIdx] || images[0];

  return (
    <article className="plp-card">
      {/* Entire card clickable (Nike-like) */}
      <Link to={`/product/${p.url_slug}`} className="plp-hit" aria-label={p.title} />

      {/* Media */}
      <div className="plp-media" aria-hidden="true">
        <img
          src={hero}
          alt=""
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = "/shoes.jpg";
          }}
        />
      </div>

      {/* Thumbnails */}
      <div className="plp-thumbs" onClick={(e) => e.stopPropagation()}>
        {thumbs.map((src, i) => (
          <button
            key={src + i}
            type="button"
            className={`plp-thumb ${i === activeIdx ? "is-active" : ""}`}
            onMouseEnter={() => setActiveIdx(i)}
            onFocus={() => setActiveIdx(i)}
            onClick={(e) => {
              e.preventDefault();
              setActiveIdx(i);
            }}
            aria-label={`Preview image ${i + 1}`}
          >
            <img src={src} alt="" />
          </button>
        ))}

        {extraCount > 0 && <span className="plp-more">+{extraCount}</span>}
      </div>

      {/* Info */}
      <div className="plp-info">
        <div className="plp-badge">{p.tag}</div>
        <div className="plp-title" title={p.title}>
          {p.title}
        </div>

        {/* Optional line (you can customize this text later) */}
        <div className="plp-meta">Men&apos;s Shoes</div>

        <div className="plp-price">${p.price}</div>

        {/* Optional special line like Nike */}
        {/* <div className="plp-special">See Price in Bag</div> */}
      </div>
    </article>
  );
}

function ProductGrid({ products }) {
  return (
    <div className="plp-grid">
      {products.map((p) => (
        <ProductCard key={p.id} p={p} />
      ))}
    </div>
  );
}

export default function Shoes() {
  const [filtersHidden, setFiltersHidden] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  const mappedProducts = useMemo(() => {
    return products.map((p) => {
      const image = normalizeUrl(p.image_url || "");
      // If your backend ever returns multiple images, these will work automatically:
      const rawImages =
        (Array.isArray(p.images) && p.images) ||
        (Array.isArray(p.image_urls) && p.image_urls) ||
        [];

      const images = rawImages.length ? rawImages.map(normalizeUrl) : [image];

      return {
        id: p.id,
        url_slug: p.url_slug,
        tag: "Just In",
        title: p.product_name,
        price: p.price ?? p.base_price ?? 0,
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
        ? `${API_BASE}/product/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(
            FOOTWEAR_CATEGORY
          )}`
        : `${API_BASE}/product/?category=${encodeURIComponent(FOOTWEAR_CATEGORY)}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error(await res.text());
      setProducts(await res.json());
    } catch (e) {
      setError(e?.message || "Something went wrong");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchProducts(); }, []);
  useEffect(() => {
    const t = setTimeout(() => fetchProducts({ q: search }), 350);
    return () => clearTimeout(t);
  }, [search]);

  return (
    <div className="shoes-page">
      {/* Header unchanged */}
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <a href="#" className="brand-logo">JAMES</a>
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
            <button className="icon-btn" type="button" aria-label="Favorites">♡</button>
            <button className="icon-btn" type="button" aria-label="Bag">👜</button>
          </div>
        </div>
      </header>

      <main className="wrap main-wrap">
        <div className={`page ${filtersHidden ? "filters-hidden" : ""}`}>
          <aside className="filters" aria-label="Filters" />

          <section className="content">
            <div className="content-top">
              <h1 className="page-title">Footwear</h1>
              <button
                className="link-btn"
                type="button"
                onClick={() => setFiltersHidden((v) => !v)}
              >
                {filtersHidden ? "Show Filters" : "Hide Filters"}
              </button>
            </div>

            {loading && <p className="state">Loading...</p>}
            {error && <p className="state error">{error}</p>}

            <ProductGrid products={mappedProducts} />

            {!loading && !error && mappedProducts.length === 0 && (
              <p className="state">No footwear products found.</p>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
