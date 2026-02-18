import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import CartItemRow from "./components/cart/CartItemRow.jsx";
import OrderSummary from "./components/cart/OrderSummary.jsx";

import "./Cart.css";

const CART_STORAGE_KEY = "cart_items";
const CHECKOUT_STORAGE_KEY = "checkout_payload";

const money = (n) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    Number(n || 0)
  );

export default function Cart() {
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [promoInput, setPromoInput] = useState("");
  const [appliedPromo, setAppliedPromo] = useState(null);
  const [promoError, setPromoError] = useState("");

  // Load cart from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(CART_STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      // Ensure each item has selected field (default true for in-stock)
      const hydrated = (Array.isArray(parsed) ? parsed : []).map((it) => ({
        ...it,
        selected: it.inStock ? (typeof it.selected === "boolean" ? it.selected : true) : false,
      }));
      setItems(hydrated);
    } catch {
      setItems([]);
    }
  }, []);

  // Persist cart to localStorage
  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const inStockItems = useMemo(() => items.filter((i) => i.inStock), [items]);

  const allSelected = useMemo(() => {
    if (inStockItems.length === 0) return false;
    return inStockItems.every((i) => i.selected);
  }, [inStockItems]);

  const selectedItems = useMemo(
    () => items.filter((i) => i.inStock && i.selected),
    [items]
  );

  const selectedItemCount = selectedItems.length;

  const subtotal = useMemo(() => {
    return selectedItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
  }, [selectedItems]);

  const shipping = useMemo(() => {
    // Fixed shipping per order if anything is selected
    return selectedItemCount > 0 ? 4.5 : 0;
  }, [selectedItemCount]);

  const discount = useMemo(() => {
    if (appliedPromo === "SAVE10") return subtotal * 0.1;
    return 0;
  }, [appliedPromo, subtotal]);

  const total = useMemo(() => {
    const t = subtotal + shipping - discount;
    return t < 0 ? 0 : t;
  }, [subtotal, shipping, discount]);

  const cartCountText = items.length === 1 ? "1 item" : `${items.length} items`;

  const toggleSelectAll = () => {
    setItems((prev) =>
      prev.map((it) =>
        it.inStock ? { ...it, selected: !allSelected } : it
      )
    );
  };

  const toggleSelectOne = (id) => {
    setItems((prev) =>
      prev.map((it) =>
        it.id === id && it.inStock ? { ...it, selected: !it.selected } : it
      )
    );
  };

  const changeQty = (id, delta) => {
    setItems((prev) =>
      prev.map((it) => {
        if (it.id !== id) return it;
        if (!it.inStock) return it;
        const next = Math.max(1, (it.quantity || 1) + delta);
        return { ...it, quantity: next };
      })
    );
  };

  const removeItem = (id) => {
    setItems((prev) => prev.filter((it) => it.id !== id));
  };

  const deleteSelected = () => {
    setItems((prev) => prev.filter((it) => !(it.inStock && it.selected)));
  };

  const applyPromo = () => {
    const code = promoInput.trim().toUpperCase();
    setPromoError("");

    if (!code) {
      setAppliedPromo(null);
      return;
    }

    if (code === "SAVE10") {
      setAppliedPromo("SAVE10");
      setPromoError("");
    } else {
      setAppliedPromo(null);
      setPromoError("Invalid code. Try SAVE10");
    }
  };

  const proceedToCheckout = () => {
    if (selectedItemCount === 0) return;

    const payload = {
      selectedItems,
      subtotal,
      shipping,
      discount,
      total,
      voucherCode: appliedPromo,
      currency: "USD",
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem(CHECKOUT_STORAGE_KEY, JSON.stringify(payload));

    navigate("/payment", { state: payload });
  };

  const continueShopping = () => navigate("/");

  const promoMessage =
    appliedPromo === "SAVE10"
      ? `Voucher (${appliedPromo})`
      : promoError
      ? promoError
      : "";

  return (
    <main className="cartPage">
      <div className="cartContainer">
        {/* Page header */}
        <div className="cartHeader">
          <h1 className="cartTitle">Shopping Bag</h1>
          <p className="cartSubtitle">
            You have {cartCountText} in your cart. Review and checkout.
          </p>
        </div>

        <div className="cartLayout">
          {/* LEFT */}
          <section className="cartLeft">
            {items.length > 0 ? (
              <>
                {/* Bulk actions */}
                <div className="bulkBar">
                  <label className="bulkLeft">
                    <input
                      type="checkbox"
                      className="check"
                      checked={allSelected}
                      onChange={toggleSelectAll}
                      disabled={inStockItems.length === 0}
                    />
                    <span className="bulkLabel">
                      Select All ({items.length} {items.length === 1 ? "item" : "items"})
                    </span>
                  </label>

                  <button
                    className="dangerBtn"
                    onClick={deleteSelected}
                    disabled={selectedItemCount === 0}
                    type="button"
                    title="Delete selected"
                  >
                    Delete selected
                  </button>
                </div>

                {/* Items */}
                <div className="itemsList">
                  {items.map((item) => (
                    <CartItemRow
                      key={item.id}
                      item={item}
                      onToggle={() => toggleSelectOne(item.id)}
                      onRemove={() => removeItem(item.id)}
                      onQtyMinus={() => changeQty(item.id, -1)}
                      onQtyPlus={() => changeQty(item.id, +1)}
                    />
                  ))}
                </div>

                {/* Empty state hidden here; handled below */}
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

          {/* RIGHT */}
          <aside className="cartRight">
            <OrderSummary
              selectedItemCount={selectedItemCount}
              subtotal={subtotal}
              shipping={shipping}
              discount={discount}
              total={total}
              promoInput={promoInput}
              onPromoInputChange={setPromoInput}
              onApplyPromo={applyPromo}
              promoMessage={promoMessage}
              appliedPromo={appliedPromo}
              proceedDisabled={selectedItemCount === 0}
              onProceed={proceedToCheckout}
              money={money}
            />

            <button className="linkBtn" onClick={continueShopping} type="button">
              ← Continue Shopping
            </button>
          </aside>
        </div>
      </div>
    </main>
  );
}
