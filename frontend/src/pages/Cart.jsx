import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Cart.css";
import StoreTopBar from "./components/cart/StoreTopBar";

const CHECKOUT_CTX_KEY = "checkout_context";

const RAW_API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

const API_BASE_URL = String(RAW_API_BASE).replace(/\/+$/, "");

const EMPTY_CART = {
  cartId: "",
  buyerId: "",
  status: "ACTIVE",
  selectedCount: 0,
  subtotal: 0,
  deliveryCharge: 0,
  total: 0,
  deliveryBreakdown: [],
  items: [],
};

const money = (value) => `Rs. ${Number(value || 0).toLocaleString("en-NP")}`;

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("authToken") ||
    ""
  );
}

function getAuthHeaders() {
  const token = getToken();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function buildApiUrl(path) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
}

function resolveImageUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return buildApiUrl(path);
}

async function readErrorMessage(res, fallbackMessage) {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((x) => x?.msg || JSON.stringify(x)).join(", ");
    }
    if (typeof data?.message === "string") return data.message;
    return fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

function normalizeBackendCart(cart) {
  const backendItems = Array.isArray(cart?.items) ? cart.items : [];

  return {
    cartId: String(cart?.cart_id || ""),
    buyerId: String(cart?.buyer_id || ""),
    status: cart?.status || "ACTIVE",
    selectedCount: toNumber(cart?.selected_count, 0),
    subtotal: toNumber(cart?.subtotal, 0),
    deliveryCharge: toNumber(cart?.delivery_charge, 0),
    total: toNumber(cart?.total, 0),
    deliveryBreakdown: Array.isArray(cart?.delivery_breakdown)
      ? cart.delivery_breakdown
      : [],
    items: backendItems.map((item, index) => {
      const variant = item?.product_variant || {};
      const product = item?.product || {};
      const quantity = Math.max(1, toNumber(item?.quantity, 1));
      const price = toNumber(item?.price ?? variant?.price, 0);

      return {
        id: String(item?.cart_item_id || `cart_item_${index}`),
        quantity,
        price,
        lineTotal: toNumber(item?.line_total, quantity * price),
        selected: Boolean(item?.selected),

        variantId: String(variant?.variant_id || ""),
        sku: variant?.sku || "",
        color: variant?.color || "",
        size: variant?.size || "",
        stock: Math.max(0, toNumber(variant?.stock_quantity, 0)),
        inStock:
          Boolean(variant?.is_active) && toNumber(variant?.stock_quantity, 0) > 0,

        productId: String(product?.product_id || ""),
        name: product?.product_name || "Untitled product",
        slug: product?.url_slug || "",
        category: product?.product_category || "",
        audience: product?.target_audience || "",
        description: product?.description || "",
        image: resolveImageUrl(product?.image_url),
        productStatus: product?.status || "",
        sellerId: String(product?.seller_id || ""),
      };
    }),
  };
}

export default function Cart() {
  const navigate = useNavigate();

  const [cartState, setCartState] = useState(EMPTY_CART);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [actionBusy, setActionBusy] = useState(false);
  const [search, setSearch] = useState("");

  const items = cartState.items;

  const selectableItems = useMemo(
    () => items.filter((item) => item.inStock),
    [items]
  );

  const selectedItems = useMemo(
    () => items.filter((item) => item.selected),
    [items]
  );

  const allSelected = useMemo(() => {
    if (selectableItems.length === 0) return false;
    return selectableItems.every((item) => item.selected);
  }, [selectableItems]);

  const selectedItemCount = cartState.selectedCount;
  const subtotal = cartState.subtotal;
  const shipping = cartState.deliveryCharge;
  const total = cartState.total;

  function handleSearchSubmit(query) {
    navigate(query ? `/products?search=${encodeURIComponent(query)}` : "/products");
  }

  async function fetchCart(showLoader = false) {
    if (showLoader) setLoading(true);

    try {
      const res = await fetch(buildApiUrl("/cart/me"), {
        method: "GET",
        headers: getAuthHeaders(),
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(await readErrorMessage(res, `Failed to fetch cart (${res.status})`));
      }

      const cart = await res.json();
      setCartState(normalizeBackendCart(cart));
      setFetchError("");
      return cart;
    } catch (error) {
      console.error("Failed to load cart:", error);
      setFetchError(error.message || "Failed to load cart");

      if (showLoader) {
        setCartState(EMPTY_CART);
      }

      return null;
    } finally {
      if (showLoader) setLoading(false);
    }
  }

  async function patchItemSelected(itemId, nextSelected) {
    const res = await fetch(
      buildApiUrl(`/cart/items/${itemId}?select=${nextSelected}`),
      {
        method: "PATCH",
        headers: getAuthHeaders(),
        credentials: "include",
      }
    );

    if (!res.ok) {
      throw new Error(
        await readErrorMessage(res, `Failed to update item selection (${res.status})`)
      );
    }

    return await res.json();
  }

  async function deleteItemRequest(itemId) {
    const res = await fetch(buildApiUrl(`/cart/items/${itemId}`), {
      method: "DELETE",
      headers: getAuthHeaders(),
      credentials: "include",
    });

    if (!res.ok) {
      throw new Error(
        await readErrorMessage(res, `Failed to remove item (${res.status})`)
      );
    }

    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  useEffect(() => {
    fetchCart(true);
  }, []);

  async function toggleSelectOne(item) {
    if (actionBusy || !item.inStock) return;

    setActionBusy(true);
    setFetchError("");

    try {
      const updatedCart = await patchItemSelected(item.id, !item.selected);
      setCartState(normalizeBackendCart(updatedCart));
    } catch (error) {
      setFetchError(error.message || "Failed to update item selection");
    } finally {
      setActionBusy(false);
    }
  }

  async function toggleSelectAll() {
    if (actionBusy || selectableItems.length === 0) return;

    const nextSelected = !allSelected;

    setActionBusy(true);
    setFetchError("");

    try {
      let latestCart = null;

      for (const item of selectableItems) {
        if (item.selected !== nextSelected) {
          latestCart = await patchItemSelected(item.id, nextSelected);
        }
      }

      if (latestCart) {
        setCartState(normalizeBackendCart(latestCart));
      } else {
        await fetchCart(false);
      }
    } catch (error) {
      setFetchError(error.message || "Failed to update all items");
      await fetchCart(false);
    } finally {
      setActionBusy(false);
    }
  }

  async function removeItem(itemId) {
    if (actionBusy) return;

    setActionBusy(true);
    setFetchError("");

    try {
      const updatedCart = await deleteItemRequest(itemId);

      if (updatedCart?.items) {
        setCartState(normalizeBackendCart(updatedCart));
      } else {
        await fetchCart(false);
      }
    } catch (error) {
      setFetchError(error.message || "Failed to remove item");
    } finally {
      setActionBusy(false);
    }
  }

  async function deleteSelected() {
    if (actionBusy || selectedItems.length === 0) return;

    setActionBusy(true);
    setFetchError("");

    try {
      for (const item of selectedItems) {
        await deleteItemRequest(item.id);
      }
      await fetchCart(false);
    } catch (error) {
      setFetchError(error.message || "Failed to delete selected items");
      await fetchCart(false);
    } finally {
      setActionBusy(false);
    }
  }

  function proceedToCheckout() {
    if (selectedItemCount === 0) return;

    sessionStorage.setItem(
      CHECKOUT_CTX_KEY,
      JSON.stringify({
        mode: "CART",
        cart_id: cartState.cartId,
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
  }

  function continueShopping() {
    navigate("/products");
  }

  if (loading) {
    return (
      <>
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/wishlist"
          profilePath="/profile"
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

  if (fetchError && items.length === 0) {
    return (
      <>
        <StoreTopBar
          searchValue={search}
          onSearchChange={setSearch}
          onSearchSubmit={handleSearchSubmit}
          searchPlaceholder="Search footwear..."
          bagPath="/cart"
          wishlistPath="/wishlist"
          profilePath="/profile"
        />

        <main className="cartPage">
          <div className="cartContainer">
            <div className="emptyState">
              <div className="emptyIcon">⚠️</div>
              <h3>Failed to load cart</h3>
              <p>{fetchError}</p>
              <button className="primaryBtn" type="button" onClick={() => fetchCart(true)}>
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
        wishlistPath="/wishlist"
        profilePath="/profile"
      />

      <main className="cartPage">
        <div className="cartContainer">
          <div className="cartHeader">
            <h1 className="cartTitle">Cart</h1>
            <p className="cartSubtitle">
              Tick items you want to buy. Subtotal and delivery fee will appear automatically.
            </p>
          </div>

          {fetchError ? (
            <div
              style={{
                marginBottom: 16,
                padding: "12px 14px",
                border: "1px solid #f1c0c0",
                background: "#fff2f2",
                color: "#b42318",
                borderRadius: 8,
              }}
            >
              {fetchError}
            </div>
          ) : null}

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
                        disabled={selectableItems.length === 0 || actionBusy}
                        aria-label={allSelected ? "Untick all" : "Tick all"}
                        aria-pressed={allSelected}
                      >
                        {allSelected ? "✓" : ""}
                      </button>

                      <span className="bulkLabel">
                        SELECT ALL ({items.length} {items.length === 1 ? "ITEM" : "ITEMS"})
                      </span>
                    </div>

                    <button
                      className="deleteSelectedBtn"
                      onClick={deleteSelected}
                      disabled={selectedItems.length === 0 || actionBusy}
                      type="button"
                    >
                      {actionBusy ? "PLEASE WAIT..." : "DELETE"}
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
                            onClick={() => toggleSelectOne(item)}
                            disabled={!item.inStock || actionBusy}
                            aria-label={item.selected ? "Untick item" : "Tick item"}
                            aria-pressed={item.selected}
                          >
                            {item.selected ? "✓" : ""}
                          </button>
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
                            {!item.inStock ? (
                              <span className="stockPill">Out of stock</span>
                            ) : null}
                          </div>

                          <div className="itemMeta">
                            {item.color ? <p>Color: {item.color}</p> : null}
                            {item.size ? <p>Size: {item.size}</p> : null}
                            {item.sku ? <p>SKU: {item.sku}</p> : null}
                          </div>

                          <div className="mobileRow">
                            <div className="priceBox mobilePrice">
                              <div className="price">{money(item.price)}</div>
                              <div className="lineTotal">
                                Line total: {money(item.lineTotal)}
                              </div>
                            </div>

                            <div className="actionBox">
                              <div className="qtyControl">
                                <button type="button" disabled>
                                  −
                                </button>
                                <span>{item.quantity}</span>
                                <button type="button" disabled>
                                  +
                                </button>
                              </div>

                              <button
                                type="button"
                                className="removeBtn"
                                onClick={() => removeItem(item.id)}
                                disabled={actionBusy}
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>

                        <div className="priceBox desktopPrice">
                          <div className="price">{money(item.price)}</div>
                          <div className="lineTotal">
                            Line total: {money(item.lineTotal)}
                          </div>
                        </div>

                        <div className="actionBox desktopAction">
                          <div className="qtyControl">
                            <button type="button" disabled>
                              −
                            </button>
                            <span>{item.quantity}</span>
                            <button type="button" disabled>
                              +
                            </button>
                          </div>

                          <button
                            type="button"
                            className="removeBtn"
                            onClick={() => removeItem(item.id)}
                            disabled={actionBusy}
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
                  <button className="primaryBtn" onClick={continueShopping} type="button">
                    Continue Shopping
                  </button>
                </div>
              )}
            </section>

            <aside className="cartRight">
              <div className="summaryCard">
                <h2 className="summaryTitle">Order Summary</h2>

                {selectedItemCount > 0 ? (
                  <>
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
                  </>
                ) : (
                  <div
                    style={{
                      padding: "12px 0",
                      color: "#667085",
                      fontSize: "14px",
                      lineHeight: 1.5,
                    }}
                  >
                    Select at least one cart item to see subtotal, delivery fee, and total.
                  </div>
                )}

                <button
                  className="proceedBtn"
                  onClick={proceedToCheckout}
                  disabled={selectedItemCount === 0 || actionBusy}
                  type="button"
                >
                  PROCEED TO CHECKOUT ({selectedItemCount})
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