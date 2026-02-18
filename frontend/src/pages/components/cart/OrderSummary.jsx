import React from "react";

export default function OrderSummary({
  selectedItemCount,
  subtotal,
  shipping,
  discount,
  total,
  promoInput,
  onPromoInputChange,
  onApplyPromo,
  promoMessage,
  appliedPromo,
  proceedDisabled,
  onProceed,
  money,
}) {
  return (
    <div className="summaryCard">
      <h2 className="summaryTitle">Order Summary</h2>

      <div className="summaryLines">
        <div className="line">
          <span>Subtotal ({selectedItemCount} {selectedItemCount === 1 ? "item" : "items"})</span>
          <strong>{money(subtotal)}</strong>
        </div>

        <div className="line">
          <span>Shipping Fee</span>
          <strong>{money(shipping)}</strong>
        </div>

        {discount > 0 ? (
          <div className="line discountLine">
            <span>{appliedPromo ? `Voucher (${appliedPromo})` : "Voucher"}</span>
            <strong>-{money(discount)}</strong>
          </div>
        ) : null}
      </div>

      <div className="promoBlock">
        <label className="promoLabel">PROMO CODE</label>
        <div className="promoRow">
          <input
            value={promoInput}
            onChange={(e) => onPromoInputChange(e.target.value)}
            placeholder="SAVE10"
          />
          <button type="button" onClick={onApplyPromo}>
            Apply
          </button>
        </div>
        {promoMessage ? (
          <p className={`promoMsg ${promoMessage.startsWith("Invalid") ? "error" : "ok"}`}>
            {promoMessage.startsWith("Invalid") ? promoMessage : `✔ ${promoMessage}`}
          </p>
        ) : null}
      </div>

      <div className="divider" />

      <div className="totalRow">
        <div>
          <div className="totalLabel">TOTAL</div>
          <div className="totalValue">{money(total)}</div>
        </div>
        <div className="taxNote">Taxes included</div>
      </div>

      <button
        className={`proceedBtn ${proceedDisabled ? "disabled" : ""}`}
        type="button"
        onClick={onProceed}
        disabled={proceedDisabled}
      >
        Proceed to Checkout <span className="arrow">→</span>
      </button>

      <div className="trustGrid">
        <div className="trustItem">
          <div className="trustIcon">🔒</div>
          <div>Secure</div>
        </div>
        <div className="trustItem">
          <div className="trustIcon">🚚</div>
          <div>Insured</div>
        </div>
        <div className="trustItem">
          <div className="trustIcon">↩</div>
          <div>30-day</div>
        </div>
      </div>
    </div>
  );
}
