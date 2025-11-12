import React from "react";
import styles from "./Homepage.module.css";

const ProductCard = ({ product, addToCart }) => {
  return (
    <div className={styles.card}>
      <img
        src={product.image_url} // already full URL from Homepage.js
        alt={product.product_name}
        style={{ width: "200px", height: "200px", objectFit: "cover" }}
      />
      <h3>{product.product_name}</h3>
      <p>${product.price}</p>
      <p>Stock: {product.stock}</p>
      <button
        disabled={product.stock === 0}
        onClick={() => addToCart(product)}
      >
        {product.stock === 0 ? "Out of stock" : "Add to Cart"}
      </button>
    </div>
  );
};

export default ProductCard;
