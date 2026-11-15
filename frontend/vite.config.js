import { defineConfig } from "vite";

const usePolling = process.env.VITE_USE_POLLING === "true";

export default defineConfig({
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    watch: usePolling ? { usePolling: true } : undefined,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
