// src/api/CartApi.js
import axios from "axios";

export const placeOrder = async (cart, token) => {
  const response = await axios.post(
    "/order/",
    { items: cart },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data; // ✅ must return full order object (with id)
};

export const getOrderById = async (orderId, token) => {
  const response = await axios.get(`/order/${orderId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
};
