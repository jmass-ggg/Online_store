import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Cart.css";
import StoreTopBar from "./components/cart/StoreTopBar";

const CHECKOUT_CTX_KEY = "checkout_context";
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const money = (n) => `Rs. ${Number(n || 0).toLocaleString("en-NP")}`;

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function resolveImageUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}

function normalizeBackendCart(cart) {
  const backendItems = Array.isArray(cart?.items) ? cart.items : [];
  const deliveryBreakdown = Array.isArray(cart?.delivery_breakdown)
    ? cart.delivery_breakdown
    : [];

  const deliveryMap = deliveryBreakdown.reduce((acc, row) => {
    const sellerId = String(row?.seller_id || "");
    if (sellerId) acc[sellerId] = toNumber(row?.delivery_charge, 0);
    return acc;
  }, {});

  return {
    cartId: String(cart?.cart_id || ""),
    buyerId: String(cart?.buyer_id || ""),
    status: cart?.status || "ACTIVE",
    deliveryMap,
    items: backendItems.map((item, index) => {
      const variant = item?.product_variant || {};
      const product = item?.product || {};
      const sellerId = String(product?.seller_id || "");

      return {
        id: String(item?.cart_item_id || `cart_item_${index}`),
        cart_id: String(cart?.cart_id || ""),
        quantity: Math.max(1, toNumber(item?.quantity, 1)),
        price: toNumber(item?.price ?? variant?.price, 0),
        selected: Boolean(item?.selected),
        line_total: toNumber(item?.line_total, 0),

        sellerId,
        deliveryCharge: toNumber(deliveryMap[sellerId], 0),

        inStock:
          Boolean(variant?.is_active) && toNumber(variant?.stock_quantity, 0) > 0,
        stock: Math.max(0, toNumber(variant?.stock_quantity, 0)),

        name: product?.product_name || "Untitled product",
        image: resolveImageUrl(product?.image_url),
        size: variant?.size || "",
        color: variant?.color || "",
        sku: variant?.sku || "",
        category: product?.product_category || "",
        audience: product?.target_audience || "",
        slug: product?.url_slug || "",
        productStatus: product?.status || "",
      };
    }),
  };
}

export default function Cart() {
  const navigate = useNavigate();

  const [cartId, setCartId] = useState("");
  const [deliveryMap, setDeliveryMap] = useState({});
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [search, setSearch] = useState("");

  function handleSearchSubmit(query) {
    navigate(query ? `/products?search=${encodeURIComponent(query)}` : "/products");
  }

  useEffect(() => {
    const fetchMyCart = async () => {
      try {
        setLoading(true);
        setFetchError("");

        const res = await fetch(`${API_BASE_URL}/cart/me`, {
          method: "GET",
          headers: getAuthHeaders(),
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error(`Failed to fetch cart (${res.status})`);
        }

        const cart = await res.json();
        const normalized = normalizeBackendCart(cart);

        setCartId(normalized.cartId);
        setDeliveryMap(normalized.deliveryMap);
        setItems(normalized.items);
      } catch (error) {
        console.error("Failed to load cart:", error);
        setFetchError(error.message || "Failed to load cart");
        setItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMyCart();
  }, []);

  const selectableItems = useMemo(
    () => items.filter((item) => item.inStock),
    [items]
  );

  const allSelected = useMemo(() => {
    if (selectableItems.length === 0) return false;
    return selectableItems.every((item) => item.selected);
  }, [selectableItems]);

  const selectedItems = useMemo(
    () => items.filter((item) => item.inStock && item.selected),
    [items]
  );

  const selectedItemCount = selectedItems.length;

  const subtotal = useMemo(() => {
    return selectedItems.reduce(
      (sum, item) => sum + toNumber(item.price) * toNumber(item.quantity, 1),
      0
    );
  }, [selectedItems]);

  const shipping = useMemo(() => {
    const uniqueSellerIds = [...new Set(selectedItems.map((i) => i.sellerId))].filter(
      Boolean
    );

    return uniqueSellerIds.reduce(
      (sum, sellerId) => sum + toNumber(deliveryMap[sellerId], 0),
      0
    );
  }, [selectedItems, deliveryMap]);

  const total = useMemo(() => subtotal + shipping, [subtotal, shipping]);

  const toggleSelectAll = () => {
    setItems((prev) =>
      prev.map((item) =>
        item.inStock ? { ...item, selected: !allSelected } : item
      )
    );
  };

  const toggleSelectOne = (id) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id && item.inStock
          ? { ...item, selected: !item.selected }
          : item
      )
    );
  };

  const changeQty = (id, delta) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id || !item.inStock) return item;

        const next = Math.max(1, toNumber(item.quantity, 1) + delta);
        const capped = item.stock > 0 ? Math.min(next, item.stock) : next;

        return { ...item, quantity: capped };
      })
    );
  };

  const removeItem = (id) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  const deleteSelected = () => {
    setItems((prev) => prev.filter((item) => !(item.inStock && item.selected)));
  };

  const proceedToCheckout = () => {
    if (selectedItemCount === 0) return;

    sessionStorage.setItem(
      CHECKOUT_CTX_KEY,
      JSON.stringify({
        mode: "CART",
        cart_id: cartId,
        summary: {
          selected_count: selectedItemCount,
          subtotal,
          delivery_charge: shipping,
          total,
        },
        items: selectedItems,
      })
    );

    navigate("/checkout");
  };

  const continueShopping = () => navigate("/");

  if (loading) {
    return (
      <>
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/products"
          profilePath="/login"
        />
        <main className="cartPage">
          <div className="cartContainer">
            <div className="emptyState">
              <div className="emptyIcon">🛒</div>
              <h3>Loading cart...</h3>
              <p>Please wait while we fetch your cart.</p>
            </div>
          </div>
        </main>
      </>
    );
  }

  if (fetchError) {
    return (
      <>
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/products"
          profilePath="/login"
        />
        <main className="cartPage">
          <div className="cartContainer">
            <div className="emptyState">
              <div className="emptyIcon">⚠️</div>
              <h3>Failed to load cart</h3>
              <p>{fetchError}</p>
              <button
                className="primaryBtn"
                onClick={() => window.location.reload()}
                type="button"
              >
                Retry
              </button>
            </div>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <StoreTopBar
        searchValue={search}
        onSearchChange={setSearch}
        onSearchSubmit={handleSearchSubmit}
        searchPlaceholder="Search footwear..."
        bagPath="/cart"
        wishlistPath="/products"
        profilePath="/login"
      />
      <main className="cartPage">
        <div className="cartContainer">
          <div className="cartHeader">
            <h1 className="cartTitle">Cart</h1>
            <p className="cartSubtitle">
              Review your selected products and proceed to checkout.
            </p>
          </div>

          <div className="cartLayout">
            <section className="cartLeft">
              {items.length > 0 ? (
                <>
                  <div className="bulkBar">
                    <div className="bulkLeft">
                      <button
                        type="button"
                        className={`tickBox ${allSelected ? "checked" : ""}`}
                        onClick={toggleSelectAll}
                        disabled={selectableItems.length === 0}
                        aria-label={allSelected ? "Unselect all" : "Select all"}
                        aria-pressed={allSelected}
                      />
                      <span className="bulkLabel">
                        SELECT ALL ({items.length} {items.length === 1 ? "ITEM" : "ITEMS"})
                      </span>
                    </div>

                    <button
                      className="deleteSelectedBtn"
                      onClick={deleteSelected}
                      disabled={selectedItemCount === 0}
                      type="button"
                    >
                      DELETE
                    </button>
                  </div>

                  <div className="itemsList">
                    {items.map((item) => (
                      <article
                        className={`cartItem ${!item.inStock ? "disabled" : ""}`}
                        key={item.id}
                      >
                        <div className="checkCol">
                          <button
                            type="button"
                            className={`tickBox ${item.selected ? "checked" : ""}`}
                            onClick={() => toggleSelectOne(item.id)}
                            disabled={!item.inStock}
                            aria-label={
                              item.selected ? "Unselect item" : "Select item"
                            }
                            aria-pressed={item.selected}
                          />
                        </div>

                        <div className="thumb">
                          {item.image ? (
                            <img src={item.image} alt={item.name} />
                          ) : (
                            <div className="thumbFallback">No Image</div>
                          )}
                        </div>

                        <div className="itemBody">
                          <div className="itemNameRow">
                            <h3 className="itemName">{item.name}</h3>
                            {!item.inStock && (
                              <span className="stockPill">Out of stock</span>
                            )}
                          </div>

                          <div className="itemMeta">
                            {item.color && <p>Color: {item.color}</p>}
                            {item.size && <p>Size: {item.size}</p>}
                            {item.sku && <p>SKU: {item.sku}</p>}
                          </div>

                          <div className="mobileRow">
                            <div className="priceBox mobilePrice">
                              <div className="price">{money(item.price)}</div>
                              <div className="lineTotal">
                                Line total: {money(item.price * item.quantity)}
                              </div>
                            </div>

                            <div className="actionBox">
                              <div className="qtyControl">
                                <button
                                  type="button"
                                  onClick={() => changeQty(item.id, -1)}
                                  disabled={!item.inStock || item.quantity <= 1}
                                >
                                  −
                                </button>
                                <span>{item.quantity}</span>
                                <button
                                  type="button"
                                  onClick={() => changeQty(item.id, +1)}
                                  disabled={
                                    !item.inStock || item.quantity >= item.stock
                                  }
                                >
                                  +
                                </button>
                              </div>

                              <button
                                type="button"
                                className="removeBtn"
                                onClick={() => removeItem(item.id)}
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>

                        <div className="priceBox desktopPrice">
                          <div className="price">{money(item.price)}</div>
                          <div className="lineTotal">
                            Line total: {money(item.price * item.quantity)}
                          </div>
                        </div>

                        <div className="actionBox desktopAction">
                          <div className="qtyControl">
                            <button
                              type="button"
                              onClick={() => changeQty(item.id, -1)}
                              disabled={!item.inStock || item.quantity <= 1}
                            >
                              −
                            </button>
                            <span>{item.quantity}</span>
                            <button
                              type="button"
                              onClick={() => changeQty(item.id, +1)}
                              disabled={!item.inStock || item.quantity >= item.stock}
                            >
                              +
                            </button>
                          </div>

                          <button
                            type="button"
                            className="removeBtn"
                            onClick={() => removeItem(item.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </>
              ) : (
                <div className="emptyState">
                  <div className="emptyIcon">🛒</div>
                  <h3>Your cart is empty</h3>
                  <p>Looks like you haven’t added anything yet.</p>
                  <button
                    className="primaryBtn"
                    onClick={continueShopping}
                    type="button"
                  >
                    Continue Shopping
                  </button>
                </div>
              )}
            </section>

            <aside className="cartRight">
              <div className="summaryCard">
                <h2 className="summaryTitle">Order Summary</h2>

                <div className="summaryLines">
                  <div className="summaryLine">
                    <span>
                      Subtotal ({selectedItemCount}{" "}
                      {selectedItemCount === 1 ? "item" : "items"})
                    </span>
                    <strong>{money(subtotal)}</strong>
                  </div>

                  <div className="summaryLine">
                    <span>Shipping Fee</span>
                    <strong>{money(shipping)}</strong>
                  </div>
                </div>

                <div className="summaryDivider" />

                <div className="summaryTotal">
                  <span>Total</span>
                  <strong>{money(total)}</strong>
                </div>

                <button
                  className="proceedBtn"
                  onClick={proceedToCheckout}
                  disabled={selectedItemCount === 0}
                  type="button"
                >
                  PROCEED TO CHECKOUT({selectedItemCount})
                </button>
              </div>

              <button className="linkBtn" onClick={continueShopping} type="button">
                ← Continue Shopping
              </button>
            </aside>
          </div>
        </div>
      </main>
    </>
  );
}