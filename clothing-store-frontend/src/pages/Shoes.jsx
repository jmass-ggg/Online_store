import { useMemo, useState } from "react";
import "./Shoes.css";

export default function Shoes() {
  const [filtersHidden, setFiltersHidden] = useState(false);

  // You can replace image paths with your own later
  const products = useMemo(
    () => [
      {
        id: 1,
        tag: "Just In",
        title: "Nike Dunk Low Retro SE",
        category: "Men's Shoes",
        price: 120,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#777", "#777", "#777", "#777"],
        more: "+6",
      },
      {
        id: 2,
        tag: "Best Seller",
        title: "Nike Dunk Low Retro",
        category: "Men's Shoes",
        price: 111.97,
        oldPrice: 120,
        deal: "Extra 25% Off w/ code: STRONG",
        image: "/shoes.jpg",
        swatches: ["#eaeaea", "#777", "#777", "#777"],
        more: "+10",
      },
      {
        id: 3,
        tag: "Best Seller",
        title: "Nike Dunk Low GORE-TEX",
        category: "Men's Shoes",
        price: 155,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#7a4c2a", "#777", "#777"],
        more: null,
      },
      {
        id: 4,
        tag: "Just In",
        title: "Nike Dunk Low Premium",
        category: "Men's Shoes",
        price: 135,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#777", "#eaeaea"],
        more: "+4",
      },
      {
        id: 5,
        tag: "Best Seller",
        title: "Nike Dunk High Retro",
        category: "Men's Shoes",
        price: 140,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#777", "#777"],
        more: "+2",
      },
      {
        id: 6,
        tag: "Just In",
        title: "Nike Dunk Low Classic",
        category: "Men's Shoes",
        price: 125,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#7a4c2a", "#777"],
        more: "+3",
      },
      {
        id: 7,
        tag: "Best Seller",
        title: "Nike Dunk Low Street",
        category: "Men's Shoes",
        price: 130,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#777", "#eaeaea"],
        more: null,
      },
      {
        id: 8,
        tag: "Just In",
        title: "Nike Dunk Low Runner",
        category: "Men's Shoes",
        price: 118,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#7a4c2a", "#777", "#777"],
        more: null,
      },
      {
        id: 9,
        tag: "Best Seller",
        title: "Nike Dunk Low Sport",
        category: "Men's Shoes",
        price: 145,
        oldPrice: null,
        deal: null,
        image: "/shoes.jpg",
        swatches: ["#777", "#777", "#777"],
        more: "+5",
      },
    ],
    []
  );

  return (
    <div className="shoes-page">
      {/* Top Header */}
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
            <a href="#">Sport</a>
            <a href="#" className="sale">Sale</a>
          </nav>

          <div className="header-actions">
            <div className="search">
              <span className="search-icon" aria-hidden="true">🔍</span>
              <input type="text" placeholder="Search" />
            </div>
            <button className="icon-btn" type="button" aria-label="Favorites">♡</button>
            <button className="icon-btn" type="button" aria-label="Bag">👜</button>
          </div>
        </div>
      </header>

      {/* Promo Bar */}
      <div className="promo">
        <div className="wrap promo-row">
          <button className="chev" type="button" aria-label="Previous">‹</button>
          <a className="promo-link" href="#">Members: Free Shipping on Orders $50+</a>
          <button className="chev" type="button" aria-label="Next">›</button>
        </div>
      </div>

      {/* Main */}
      <main className="wrap main-wrap">
        <div className={`page ${filtersHidden ? "filters-hidden" : ""}`}>
          {/* Left Filters */}
          <aside className="filters">
            <h1 className="page-title">Mens Nike Dunk (16)</h1>

            <div className="pickup">
              <span>Pick Up Today</span>
              <label className="switch">
                <input type="checkbox" />
                <span className="slider"></span>
              </label>
            </div>

            <div className="filter-links">
              <a href="#">Low Top</a>
              <a href="#">High Top</a>
              <a href="#">Skateboarding</a>
              <a href="#">Nike By You</a>
            </div>

            <hr />

            <details className="filter-group" open>
              <summary>Gender (1)</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Men</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Sale & Offers</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Sale</label>
                <label className="chk"><input type="checkbox" /> Promo Codes</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Color</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Black</label>
                <label className="chk"><input type="checkbox" /> White</label>
                <label className="chk"><input type="checkbox" /> Blue</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Shop by Price</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> $0 - $50</label>
                <label className="chk"><input type="checkbox" /> $50 - $100</label>
                <label className="chk"><input type="checkbox" /> $100+</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Size</summary>
              <div className="filter-body sizes">
                <button className="size" type="button">7</button>
                <button className="size" type="button">8</button>
                <button className="size" type="button">9</button>
                <button className="size" type="button">10</button>
                <button className="size" type="button">11</button>
              </div>
            </details>

            <details className="filter-group">
              <summary>Brand</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Nike</label>
                <label className="chk"><input type="checkbox" /> Jordan</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Sports</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Lifestyle</label>
                <label className="chk"><input type="checkbox" /> Skate</label>
              </div>
            </details>

            <details className="filter-group">
              <summary>Best For</summary>
              <div className="filter-body">
                <label className="chk"><input type="checkbox" /> Everyday</label>
                <label className="chk"><input type="checkbox" /> Outdoor</label>
              </div>
            </details>
          </aside>

          {/* Right Content */}
          <section className="content">
            <div className="content-top">
              <button
                className="link-btn"
                type="button"
                onClick={() => setFiltersHidden((v) => !v)}
              >
                {filtersHidden ? "Show Filters" : "Hide Filters"}
              </button>

              <div className="sort">
                <span>Sort By</span>
                <select>
                  <option>Featured</option>
                  <option>Newest</option>
                  <option>Price: Low-High</option>
                  <option>Price: High-Low</option>
                </select>
              </div>
            </div>

            {/* Products (3 per row + scroll) */}
            <div className="grid">
              {products.map((p) => (
                <article className="card" key={p.id}>
                  <div className="card-img">
                    {/* Replace with your own image later */}
                    <img src={p.image} alt={p.title} loading="lazy" />
                    <button className="quick-add" type="button">Quick Add</button>
                  </div>

                  {(p.swatches?.length || p.more) && (
                    <div className="swatches">
                      {p.swatches?.map((c, idx) => (
                        <span
                          key={idx}
                          className="dot"
                          style={{ background: c }}
                          aria-hidden="true"
                        />
                      ))}
                      {p.more && <span className="more">{p.more}</span>}
                    </div>
                  )}

                  <div className="card-text">
                    <div className={`tag ${p.tag === "Just In" ? "justin" : "bestseller"}`}>
                      {p.tag}
                    </div>

                    <h3>{p.title}</h3>
                    <p className="sub">{p.category}</p>

                    <p className="price">
                      {p.oldPrice ? (
                        <>
                          <span className="sale-price">${p.price}</span>
                          <span className="old">${p.oldPrice}</span>
                        </>
                      ) : (
                        <>${p.price}</>
                      )}
                    </p>

                    {p.deal && <p className="deal">{p.deal}</p>}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
