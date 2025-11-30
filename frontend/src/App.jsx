/**
 * ONYX Security Intelligence Platform - Main Application Entry
 * Clean, modular architecture with separated concerns
 */
import React, { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { ShieldCheckIcon } from "@heroicons/react/24/outline";

// Core Components
import { AuthProvider, useAuth, AuthRoutingHandler } from "./components/auth";
import { MainLayout } from "./layouts";
import { LandingPage } from "./components/marketing";

// Create QueryClient with enhanced settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      refetchInterval: 30000,
    },
  },
});

/**
 * Loading Screen Component
 */
const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
    <div className="text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl mb-4 animate-pulse">
        <ShieldCheckIcon className="h-8 w-8 text-white" />
      </div>
      <p className="text-white text-lg">Loading ONYX Platform...</p>
    </div>
  </div>
);

/**
 * App Content - Handles authentication routing
 */
function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const location = useLocation();

  // Show loading screen while checking auth status
  if (isLoading) {
    return <LoadingScreen />;
  }

  // Public routes that don't require authentication
  const publicRoutes = [
    "/",
    "/landing",
    "/login",
    "/register",
    "/reset-password",
    "/verify-email",
  ];
  const isPublicRoute = publicRoutes.some(
    (route) =>
      location.pathname === route || location.pathname.startsWith(route)
  );

  // If authenticated, show main layout with all routes
  if (isAuthenticated) {
    return <MainLayout />;
  }

  // If not authenticated, handle public routes or show auth modal
  return (
    <AuthRoutingHandler
      authModalOpen={authModalOpen}
      setAuthModalOpen={setAuthModalOpen}
    />
  );
}

/**
 * Main App Component
 * Provides all context providers and global configuration
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>

      {/* Global Toast Notifications */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        containerStyle={{ zIndex: 9999 }}
        toastOptions={{
          duration: 4000,
          style: {
            background:
              "linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(31, 41, 55, 0.95) 100%)",
            color: "#fff",
            border: "1px solid rgba(75, 85, 99, 0.3)",
            borderRadius: "1rem",
            backdropFilter: "blur(16px)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            maxWidth: "500px",
          },
          success: {
            duration: 3000,
            iconTheme: { primary: "#10b981", secondary: "#fff" },
          },
          error: {
            duration: 5000,
            iconTheme: { primary: "#ef4444", secondary: "#fff" },
          },
          loading: {
            duration: Infinity,
            iconTheme: { primary: "#3b82f6", secondary: "#fff" },
          },
        }}
      />
    </QueryClientProvider>
  );
}

export default App;
