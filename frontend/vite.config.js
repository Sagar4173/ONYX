import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), "");

  // Get backend URL from environment or default
  const backendUrl =
    env.BACKEND_URL || env.API_BASE_URL || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    base: "/",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
        "@styles": path.resolve(__dirname, "./src/styles"),
        "@components": path.resolve(__dirname, "./src/components"),
        "@services": path.resolve(__dirname, "./src/services"),
        "@utils": path.resolve(__dirname, "./src/utils"),
        "@config": path.resolve(__dirname, "./src/config"),
        "@pages": path.resolve(__dirname, "./src/pages"),
        "@layouts": path.resolve(__dirname, "./src/layouts"),
      },
    },
    server: {
      port: parseInt(env.FRONTEND_PORT) || 5173,
      host: true,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
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
      sourcemap: false, // Disable sourcemaps in production for security
      minify: "esbuild",
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes("node_modules/react") || id.includes("node_modules/react-dom")) return "vendor";
            if (id.includes("node_modules/html2canvas")) return "html2canvas";
            if (id.includes("node_modules/jspdf")) return "jspdf";
            if (id.includes("node_modules/html2pdf")) return "html2pdf";
            if (id.includes("node_modules/recharts")) return "charts";
            if (id.includes("node_modules/framer-motion")) return "motion";
            if (id.includes("node_modules/@tanstack/react-query")) return "query";
            if (id.includes("node_modules/@headlessui") || id.includes("node_modules/@heroicons")) return "ui";
            if (id.includes("EnhancedReportDetails") || id.includes("ReportCharts") || id.includes("AISection")) return "report-details";
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
    // Add esbuild configuration - drop console in production
    esbuild: {
      logOverride: { "this-is-undefined-in-esm": "silent" },
      drop: mode === "production" ? ["console", "debugger"] : [],
    },
    // Silence some warnings
    logLevel: mode === "development" ? "info" : "warn",
  };
});
