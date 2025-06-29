import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import {resolve} from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Base public path
  base: "/",

  // Build options
  build: {
    target: "esnext",
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: true,
    // Optimize deps
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
    // Minification options
    minify: "terser",
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
  },

  // Development server options
  server: {
    host: true,
    port: 3000,
    cors: true,
    hmr: {
      overlay: true,
    },
  },

  // Resolve aliases
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
      "@components": resolve(__dirname, "./src/components"),
      "@hooks": resolve(__dirname, "./src/hooks"),
      "@utils": resolve(__dirname, "./src/utils"),
    },
  },

  // CSS options
  css: {
    modules: {
      localsConvention: "camelCase",
    },
    devSourcemap: true,
  },

  // Optimization options
  optimizeDeps: {
    include: ["react", "react-dom", "react-router-dom"],
  },
});
