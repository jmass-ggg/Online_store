import React, { useState, useEffect } from "react";
import axios from "axios";
import styles from "./Homepage.module.css";
import Cart from "./Cart";
import ProductCard from "./ProductCard";

function Homepage() {
  const [cart, setCart] = useState([]);
  const [products, setProducts] = useState([]);

  // Fetch products on load
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await axios.get("http://127.0.0.1:8000/product/", {
          headers: { Authorization: `Bearer ${token}` },
        });

        // Fix image URLs
        const productsWithUrl = res.data.map((p) => ({
          ...p,
          image_url: p.image_url
            ? p.image_url.startsWith("http")
              ? p.image_url // already a full URL
              : `http://127.0.0.1:8000/${p.image_url}` // relative URL from backend
            : "https://via.placeholder.com/200", // fallback placeholder
        }));

        setProducts(productsWithUrl);
      } catch (error) {
        console.error("Error fetching products:", error);
        alert("⚠️ Could not fetch products.");
      }
    };
    fetchProducts();
  }, []);

  // Add product to cart
  const addToCart = (product) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product_id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product_id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [
        ...prev,
        {
          product_id: product.id,
          product_name: product.product_name,
          price: product.price,
          quantity: 1,
          image_url: product.image_url,
        },
      ];
    });
  };

  // Remove product from cart
  const removeFromCart = (id) => {
    setCart((prev) => prev.filter((item) => item.product_id !== id));
  };

  return (
    <div className={styles.homepage}>
      <h1>🛒 Online Store</h1>

      <div className={styles.products}>
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            addToCart={addToCart}
          />
        ))}
      </div>

      <Cart cartItems={cart} removeFromCart={removeFromCart} />
    </div>
  );
}

export default Homepage;
