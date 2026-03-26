import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const API_TARGET = env.VITE_API_URL;

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      watch: {
        usePolling: true,
        interval: 300,
      },
      proxy: {
        "/api": {
          target: API_TARGET,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/api/, ""),
        },
        "/user": {
          target: API_TARGET,
          changeOrigin: true,
        },
        "/uploads": {
          target: API_TARGET,
          changeOrigin: true,
        },
      },
    },
  };
});