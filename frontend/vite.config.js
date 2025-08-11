import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), "");

  // Get backend URL from environment or default
  const backendUrl =
    env.BACKEND_URL || env.API_BASE_URL || "http://127.0.0.1:8000";

  console.log("🔧 Vite Config:", {
    mode,
    backendUrl,
    frontendPort: parseInt(env.FRONTEND_PORT) || 5173,
  });

  return {
    plugins: [react()],
    base: "/",
    server: {
      port: parseInt(env.FRONTEND_PORT) || 5173,
      host: true,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on("error", (err, req, res) => {
              console.log("API proxy error:", err.message);
            });
          },
        },
        // Temporarily disable WebSocket proxy to allow direct connection
        // "/ws": {
        //   target: websocketUrl,
        //   ws: true,
        //   changeOrigin: true,
        //   secure: false,
        //   timeout: 120000,
        //   proxyTimeout: 120000,
        //   configure: (proxy, options) => {
        //     proxy.on("error", (err, req, res) => {
        //       // Only log significant errors, not connection resets
        //       if (err.code !== 'ECONNRESET' && err.code !== 'ECONNABORTED') {
        //         console.log("WebSocket proxy error:", err.code, err.message);
        //       }
        //     });
        //     proxy.on("proxyReq", (proxyReq, req, res) => {
        //       proxyReq.setHeader("Connection", "Upgrade");
        //       proxyReq.setHeader("Upgrade", "websocket");
        //     });
        //   },
        // },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ["react", "react-dom"],
            charts: ["recharts"],
            ui: ["@headlessui/react", "@heroicons/react"],
          },
        },
      },
    },
    define: {
      // Suppress Vite CJS deprecation warning in development
      __DEV__: mode === "development",
    },
    optimizeDeps: {
      include: ["react", "react-dom", "@headlessui/react", "@heroicons/react"],
    },
    // Add esbuild configuration to suppress warnings
    esbuild: {
      logOverride: { "this-is-undefined-in-esm": "silent" },
    },
    // Silence some warnings
    logLevel: mode === "development" ? "info" : "warn",
  };
});
