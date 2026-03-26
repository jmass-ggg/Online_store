import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./StoreTopBar.css";

const DEFAULT_NAV_LINKS = [
  { label: "Men", to: "/products?group=men" },
  { label: "Women", to: "/products?group=women" },
  { label: "Kids", to: "/products?group=kids" },
  { label: "Jordan", to: "/products?group=jordan" },
  { label: "Collections", to: "/products" },
  { label: "Sale", to: "/products?sale=true", className: "sale" },
];

export default function StoreTopBar({
  searchValue,
  onSearchChange,
  onSearchSubmit,
  searchPlaceholder = "Search footwear...",
  showSearch = true,
  bagPath = "/cart",
  wishlistPath = "/products",
  profilePath = "/login",
  navLinks = DEFAULT_NAV_LINKS,
}) {
  const navigate = useNavigate();
  const profileRef = useRef(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [internalSearch, setInternalSearch] = useState("");

  const isControlled =
    typeof searchValue === "string" && typeof onSearchChange === "function";

  const search = isControlled ? searchValue : internalSearch;

  function setSearch(nextValue) {
    if (isControlled) {
      onSearchChange(nextValue);
      return;
    }
    setInternalSearch(nextValue);
  }

  useEffect(() => {
    function handleClickOutside(event) {
      if (!profileRef.current) return;
      if (!profileRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  function go(path) {
    setMenuOpen(false);
    if (!path) return;
    navigate(path);
  }

  function handleLogout() {
    setMenuOpen(false);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("token");
    navigate("/login");
  }

  function handleSubmit(event) {
    event.preventDefault();
    const q = String(search || "").trim();

    if (typeof onSearchSubmit === "function") {
      onSearchSubmit(q);
      return;
    }

    navigate(q ? `/products?search=${encodeURIComponent(q)}` : "/products");
  }

  return (
    <header className="store-topbar">
      <div className="store-wrap store-headerRow">
        <div className="store-brandWrap">
          <Link to="/" className="store-brandLogo">
            JAMES
          </Link>
        </div>

        <nav className="store-nav" aria-label="Main navigation">
          {navLinks.map((item) => (
            <Link
              key={`${item.label}-${item.to}`}
              to={item.to}
              className={item.className || ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="store-actions">
          {showSearch ? (
            <form className="store-search" onSubmit={handleSubmit}>
              <span className="store-searchIcon" aria-hidden="true">
                🔍
              </span>
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </form>
          ) : null}

          <button
            type="button"
            className="store-iconBtn"
            aria-label="Wishlist"
            title="Wishlist"
            onClick={() => go(wishlistPath)}
          >
            ♡
          </button>

          <button
            type="button"
            className="store-iconBtn"
            aria-label="Bag"
            title="Bag"
            onClick={() => go(bagPath)}
          >
            👜
          </button>

          <div className="store-profileWrap" ref={profileRef}>
            <button
              type="button"
              className="store-profileBtn"
              aria-label="Account"
              aria-expanded={menuOpen}
              title="Account"
              onClick={() => setMenuOpen((prev) => !prev)}
            >
              <span className="store-profileAvatar">👤</span>
            </button>

            {menuOpen ? (
              <div className="store-profileMenu" role="menu" aria-label="Account menu">
                <button
                  type="button"
                  className="store-profileItem"
                  role="menuitem"
                  onClick={() => go(profilePath)}
                >
                  <span className="store-piIco">🙂</span>
                  <span>My Account</span>
                </button>

                <button
                  type="button"
                  className="store-profileItem"
                  role="menuitem"
                  onClick={() => go(bagPath)}
                >
                  <span className="store-piIco">👜</span>
                  <span>My Bag</span>
                </button>

                <button
                  type="button"
                  className="store-profileItem"
                  role="menuitem"
                  onClick={() => go("/products")}
                >
                  <span className="store-piIco">🛍</span>
                  <span>Browse Products</span>
                </button>

                <button
                  type="button"
                  className="store-profileItem"
                  role="menuitem"
                  onClick={() => go(wishlistPath)}
                >
                  <span className="store-piIco">♡</span>
                  <span>Wishlist</span>
                </button>

                <div className="store-profileDivider" />

                <button
                  type="button"
                  className="store-profileItem danger"
                  role="menuitem"
                  onClick={handleLogout}
                >
                  <span className="store-piIco">⎋</span>
                  <span>Log out</span>
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}