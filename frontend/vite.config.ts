// frontend/vite.config.ts

import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/api": {
        target: "http://trivy-ui-backend:8000", // Use docker-compose backend service name
        changeOrigin: true,
      },
    },
  },
});
