import React from "react";

export default function CartItemRow({
  item,
  onToggle,
  onRemove,
  onQtyMinus,
  onQtyPlus,
}) {
  const {
    productName,
    price,
    oldPrice,
    imageUrl,
    quantity,
    size,
    color,
    sellerName,
    selected,
    inStock,
  } = item;

  return (
    <div className={`cartItem ${!inStock ? "disabled" : ""}`}>
      {!inStock && <div className="stockBadge">OUT OF STOCK</div>}

      <input
        type="checkbox"
        className="check"
        checked={!!selected}
        onChange={onToggle}
        disabled={!inStock}
      />

      <div className={`thumb ${!inStock ? "thumbDisabled" : ""}`}>
        <img src={imageUrl} alt={productName} />
      </div>

      <div className="itemBody">
        <div className="itemTop">
          <h3 className="itemName" title={productName}>
            {productName}
          </h3>

          <div className="priceBox">
            <div className="price">${price.toFixed(2)}</div>
            {typeof oldPrice === "number" && oldPrice > price ? (
              <div className="oldPrice">${oldPrice.toFixed(2)}</div>
            ) : null}
          </div>
        </div>

        <div className="itemMeta">
          {sellerName ? <p>Seller: <span>{sellerName}</span></p> : null}
          <p>
            {size ? `Size: ${size}` : null}
            {size && color ? " | " : null}
            {color ? `Color: ${color}` : null}
          </p>
        </div>

        <div className="itemBottom">
          <div className={`qtyControl ${!inStock ? "qtyDisabled" : ""}`}>
            <button type="button" onClick={onQtyMinus} disabled={!inStock || quantity <= 1}>
              −
            </button>
            <span>{quantity}</span>
            <button type="button" onClick={onQtyPlus} disabled={!inStock}>
              +
            </button>
          </div>

          <button className="removeBtn" type="button" onClick={onRemove} title="Remove item">
            🗑
          </button>
        </div>
      </div>
    </div>
  );
}
