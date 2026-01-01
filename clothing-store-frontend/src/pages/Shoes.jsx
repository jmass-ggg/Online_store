import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom"; // ✅ add
import "./Shoes.css";

const API_BASE = "http://127.0.0.1:8000";
const FOOTWEAR_CATEGORY = "Footwear";

export default function Shoes() {
  const [filtersHidden, setFiltersHidden] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  const mappedProducts = useMemo(() => {
    return products.map((p) => {
      const image =
        p.image_url?.startsWith("http")
          ? p.image_url
          : `${API_BASE}${p.image_url || ""}`;

      return {
        id: p.id,
        url_slug: p.url_slug, // ✅ add
        tag: "Just In",
        title: p.product_name,
        category: p.product_category,
        price: p.price ?? p.base_price ?? 0,
        image,
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

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchProducts({ q: search }), 350);
    return () => clearTimeout(t);
  }, [search]);

  // demo handlers (wire these to your real API later)
  const handleAddToCart = (p) => {
    console.log("Add to cart:", p);
    alert(`Added to cart: ${p.title}`);
  };

  const handleOrderNow = (p) => {
    console.log("Order now:", p);
    alert(`Ordering now: ${p.title}`);
  };

  return (
    <div className="shoes-page">
      {/* Header */}
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <a href="#" className="brand-logo">
              JAMES
            </a>
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
            <button className="icon-btn" type="button" aria-label="Favorites">
              ♡
            </button>
            <button className="icon-btn" type="button" aria-label="Bag">
              👜
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="wrap main-wrap">
        <div className={`page ${filtersHidden ? "filters-hidden" : ""}`}>
          {/* Filters */}
          <aside className="filters">
            <h1 className="page-title">Footwear</h1>
          </aside>

          {/* Content */}
          <section className="content">
            <div className="content-top">
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

            <div className="grid">
              {mappedProducts.map((p) => (
                <article className="card" key={p.id}>
                  {/* ✅ CLICK IMAGE -> PRODUCT PAGE */}
                  <Link
                    to={`/product/${p.url_slug}`}
                    className="card-img"
                    style={{ textDecoration: "none" }}
                  >
                    <img
                      src={p.image}
                      alt={p.title}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.src = "/shoes.jpg";
                      }}
                    />
                  </Link>

                  <div className="card-text">
                    <div className="tag justin">{p.tag}</div>
                    <h3 title={p.title}>{p.title}</h3>
                    <p className="sub">{p.category}</p>
                    <p className="price">${p.price}</p>

                    {/* Two buttons */}
                    <div className="actions">
                      <button
                        className="btn btn-primary"
                        type="button"
                        onClick={() => handleOrderNow(p)}
                      >
                        Order Now
                      </button>
                      <button
                        className="btn btn-outline"
                        type="button"
                        onClick={() => handleAddToCart(p)}
                      >
                        Add to Cart
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {!loading && !error && mappedProducts.length === 0 && (
              <p className="state">No footwear products found.</p>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
