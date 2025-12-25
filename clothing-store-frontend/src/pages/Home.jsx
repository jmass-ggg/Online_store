import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home.css";

export default function Home() {
  const nav = useNavigate();

  useEffect(() => {
    const topbar = document.getElementById("topbar");

    function onScroll() {
      if (!topbar) return;
      topbar.classList.toggle("scrolled", window.scrollY > 8);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="frame">
      {/* HEADER */}
      <header className="topbar" id="topbar">
        <nav className="nav" aria-label="Primary">
          <button className="nav-btn" type="button">Catalog</button>
          <button className="nav-btn" type="button">About Us</button>
          <button className="nav-btn" type="button">Contact Us</button>
        </nav>

        <div className="logo-wrap">
          <Link className="logo" to="/" aria-label="Home">
            JAMES
          </Link>
        </div>

        <div className="actions" role="group" aria-label="Quick actions">
          <button className="auth-btn auth-login" type="button" onClick={() => nav("/login")}>
            LOGIN
          </button>

          <button className="auth-btn auth-signup" type="button" onClick={() => nav("/register")}>
            Sign up
          </button>
        </div>
      </header>

      {/* HERO */}
      <main className="hero">
        <div className="shop-block">
          <div className="barcode" aria-hidden="true"></div>

          <h1>
            Your Ultimate Defense
            <br />
            Against the Coldest Chill
          </h1>

          <p>
            Built for winter. Designed for everyday. Warmth that looks as sharp
            as it feels.
          </p>

          <div className="btn-row">
            <button className="btn">Shop now ///</button>
            <button className="btn btn-outline">Learn more</button>
          </div>
        </div>
      </main>

      {/* SPOTLIGHT */}
      <section className="spotlight">
        <h2 className="spotlight-title">SPOTLIGHT</h2>
        <p className="spotlight-sub">
          Classic silhouettes and cutting-edge innovation to build your game
          from the ground up.
        </p>

        <div className="spotlight-grid">
  {/* ✅ SHOES -> goes to /shoes */}
  <Link to="/shoes" className="spotlight-item spotlight-link">
    <span className="spotlight-img">
      <img src="/shoes.jpg" alt="Shoes" />
    </span>
    <span className="spotlight-label">Shoes</span>
  </Link>

  <div className="spotlight-item">
    <span className="spotlight-img">
      <img src="/clothes.jpg" alt="Clothes" />
    </span>
    <span className="spotlight-label">Clothes</span>
  </div>

  <div className="spotlight-item">
    <span className="spotlight-img">
      <img src="/jewellery.jpg" alt="Jewellery" />
    </span>
    <span className="spotlight-label">Jewellery</span>
  </div>

  <div className="spotlight-item">
    <span className="spotlight-img">
      <img src="/accessories.jpg" alt="Accessories" />
    </span>
    <span className="spotlight-label">Accessories</span>
  </div>
</div>
      </section>
    </div>
  );
}
