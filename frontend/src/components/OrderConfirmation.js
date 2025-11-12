// src/components/OrderConfirmation.js
import React, { useEffect, useState } from "react";
import { useParams, useHistory } from "react-router-dom";
import { getOrderById } from "../api/CartApi";
import checkIcon from "../img/check.svg";
import styles from "./Homepage.module.css";

const OrderConfirmation = () => {
  const { id } = useParams();
  const history = useHistory();
  const token = localStorage.getItem("token");

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        const data = await getOrderById(id, token);
        setOrder(data);
      } catch (err) {
        console.error("Error fetching order:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrder();
  }, [id, token]);

  if (loading) return <p>Loading order details...</p>;
  if (!order) return <p>Order not found!</p>;

  return (
    <div className={styles.orderConfirmation}>
      <img src={checkIcon} alt="Success" width={60} />
      <h1>Order Confirmed!</h1>
      <p>Order ID: #{order.id}</p>
      <p>Status: <strong>{order.order_status}</strong></p>
      <p>Date: {new Date(order.order_at).toLocaleString()}</p>

      <div className={styles.cart}>
        <h2>Items:</h2>
        {order.items.map((item) => (
          <div key={item.id} className={styles.cartItem}>
            <span>{item.product.product_name}</span>
            <span>Qty: {item.quantity}</span>
            <span>${item.product.price * item.quantity}</span>
          </div>
        ))}
      </div>

      <h3>Total: ${order.total_price.toFixed(2)}</h3>
      <button onClick={() => history.push("/homepage")}>Back to Shop</button>
    </div>
  );
};

export default OrderConfirmation;
