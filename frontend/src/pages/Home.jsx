import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Home.css";

function isLoggedInNow() {
  const t1 = localStorage.getItem("access_token");
  const t2 = localStorage.getItem("auth_token");
  return Boolean(t1 || t2);
}

export default function Home() {
  const nav = useNavigate();

  const [isLoggedIn, setIsLoggedIn] = useState(() => isLoggedInNow());
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // header shadow on scroll
  useEffect(() => {
    const topbar = document.getElementById("topbar");
    const onScroll = () => {
      if (!topbar) return;
      topbar.classList.toggle("scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // sync login state across tabs + after login
  useEffect(() => {
    const sync = () => setIsLoggedIn(isLoggedInNow());
    window.addEventListener("storage", sync);
    window.addEventListener("auth:changed", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("auth:changed", sync);
    };
  }, []);

  // close dropdown on outside click / ESC
  useEffect(() => {
    const onDocDown = (e) => {
      if (!menuOpen) return;
      if (!menuRef.current) return;
      if (!menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    const onEsc = (e) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", onDocDown);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocDown);
      document.removeEventListener("keydown", onEsc);
    };
  }, [menuOpen]);

  // ✅ if later you store avatar_url
  const avatarUrl = useMemo(() => localStorage.getItem("avatar_url") || "", [isLoggedIn]);

  const initials = useMemo(() => {
    const name = localStorage.getItem("username") || "";
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "👤";
    const a = parts[0]?.[0] || "";
    const b = parts[1]?.[0] || "";
    return (a + b).toUpperCase();
  }, [isLoggedIn]);

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_token");
    localStorage.removeItem("refresh_token");
    setIsLoggedIn(false);
    setMenuOpen(false);
    window.dispatchEvent(new Event("auth:changed"));
    nav("/", { replace: true });
  }

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
          {!isLoggedIn ? (
            <>
              <button className="auth-btn auth-login" type="button" onClick={() => nav("/login")}>
                LOGIN
              </button>
              <button className="auth-btn auth-signup" type="button" onClick={() => nav("/register")}>
                Sign up
              </button>
            </>
          ) : (
            <div className="profileWrap" ref={menuRef}>
              <button
                type="button"
                className="profileBtn"
                aria-label="Profile menu"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((v) => !v)}
              >
                <span className="profileAvatar" aria-hidden="true">
                  {avatarUrl ? <img src={avatarUrl} alt="" /> : initials}
                </span>
              </button>

              {menuOpen && (
                <div className="profileMenu" role="menu">
                  <button
                    className="profileItem"
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false);
                      nav("/profile");
                    }}
                  >
                    Profile
                  </button>

                  <button
                    className="profileItem"
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false);
                      nav("/orders");
                    }}
                  >
                    My Orders
                  </button>

                  <div className="profileDivider" />

                  <button className="profileItem danger" type="button" role="menuitem" onClick={logout}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
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
