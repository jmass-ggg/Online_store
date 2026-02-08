import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,

    allowedHosts: [".ngrok-free.dev"],

    proxy: {
      "/product": { target: API_TARGET, changeOrigin: true },
      "/customer": { target: API_TARGET, changeOrigin: true },
      "/login": { target: API_TARGET, changeOrigin: true },
      "/cart": { target: API_TARGET, changeOrigin: true },
      "/address": { target: API_TARGET, changeOrigin: true },
      "/order": { target: API_TARGET, changeOrigin: true },
      "/review": { target: API_TARGET, changeOrigin: true },
      "/seller": { target: API_TARGET, changeOrigin: true },
      "/admin": { target: API_TARGET, changeOrigin: true },
      "/seller_management": { target: API_TARGET, changeOrigin: true },
      "/esewa": { target: API_TARGET, changeOrigin: true },

      "/uploads": { target: API_TARGET, changeOrigin: true },

      "/docs": { target: API_TARGET, changeOrigin: true },
      "/openapi.json": { target: API_TARGET, changeOrigin: true },
    },
  },
});
