import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,

    // DEV: proxy backend through /api
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },

      // DEV: allow backend uploads to load in frontend
      "/uploads": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },

    // If you use ngrok:
    // allowedHosts: [".ngrok-free.dev"],
    // hmr: { clientPort: 443 },
  },
});
