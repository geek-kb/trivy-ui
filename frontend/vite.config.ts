// frontend/vite.config.ts
import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/", // <--- REQUIRED for root-based serving
  build: {
    target: "esnext", // <--- required for modern browsers
    outDir: "dist", // <--- default, just explicit
    assetsDir: "assets", // <--- default, just explicit
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
