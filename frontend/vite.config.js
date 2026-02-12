import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = process.env.DOCKER ? "http://backend:8030" : "http://127.0.0.1:8030";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
      "/user": { target: API_TARGET, changeOrigin: true },
      "/uploads": { target: API_TARGET, changeOrigin: true },
    },
  },
});
