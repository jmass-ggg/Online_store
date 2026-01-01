// Shoes.jsx (React)
import { useEffect, useMemo, useState } from "react";
import "./Shoes.css";

const API_BASE = "http://127.0.0.1:8000";
const FOOTWEAR_CATEGORY = "Footwear"; // ✅ must match your enum exactly

export default function Shoes() {
  const [filtersHidden, setFiltersHidden] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");

  const mappedProducts = useMemo(() => {
    return products.map((p) => {
      // backend returns "/uploads/xxxx.jpg" -> make it absolute
      const image =
        p.image_url && p.image_url.startsWith("http")
          ? p.image_url
          : `${API_BASE}${p.image_url || ""}`;

      return {
        id: p.id,
        title: p.product_name,
        category: p.product_category,
        price: p.price ?? p.base_price ?? 0,
        image,
      };
    });
  }, [products]);

  async function fetchProducts(q = "") {
    setLoading(true);
    setError("");

    try {
      const url = q.trim()
        ? `${API_BASE}/product/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(FOOTWEAR_CATEGORY)}`
        : `${API_BASE}/product/?category=${encodeURIComponent(FOOTWEAR_CATEGORY)}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error(await res.text());

      setProducts(await res.json());
    } catch (e) {
      setProducts([]);
      setError(e?.message || "Failed to load products");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchProducts("");
  }, []);

  useEffect(() => {
    const t = setTimeout(() => fetchProducts(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  return (
    <div className="shoes-page">
      <header className="top-header">
        <div className="wrap header-row">
          <div className="brand">
            <a href="#" className="brand-logo">JAMES</a>
          </div>

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
          </div>
        </div>
      </header>

      <main className="wrap main-wrap">
        <div className={`page ${filtersHidden ? "filters-hidden" : ""}`}>
          <aside className="filters">
            <h1 className="page-title">Footwear</h1>
          </aside>

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

            {loading && <p>Loading...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}

            <div className="grid">
              {mappedProducts.map((p) => (
                <article className="card" key={p.id}>
                  <div className="card-img">
                    <img
                      src={p.image}
                      alt={p.title}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.src = "/shoes.jpg";
                      }}
                    />
                  </div>
                  <div className="card-text">
                    <h3>{p.title}</h3>
                    <p className="sub">{p.category}</p>
                    <p className="price">${p.price}</p>
                  </div>
                </article>
              ))}
            </div>

            {!loading && !error && mappedProducts.length === 0 && (
              <p>No footwear products found.</p>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
