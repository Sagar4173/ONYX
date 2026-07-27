/**
 * Admin Route Guard Component
 * Protects admin-only routes by checking user role
 */
import { motion } from "framer-motion";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { ShieldExclamationIcon } from "@heroicons/react/24/outline";

/**
 * Access Denied Component
 */
const AccessDenied = () => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.3 }}
    className="min-h-[60vh] flex items-center justify-center p-8"
  >
    <div className="text-center max-w-md">
      <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-2xl mb-6 border border-red-500/30">
        <ShieldExclamationIcon className="h-10 w-10 text-red-400" />
      </div>
      <h1 className="text-2xl font-bold text-white mb-3">Access Denied</h1>
      <p className="text-gray-400 mb-6">
        You don't have permission to access this page. This area is restricted to administrators
        only.
      </p>
      <a
        href="/dashboard"
        className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-violet-600 
                   text-white font-medium rounded-xl hover:shadow-lg hover:shadow-cyan-500/25 
                   transition-all duration-300"
      >
        Return to Dashboard
      </a>
    </div>
  </motion.div>
);

/**
 * Admin Route Guard
 * Wraps routes that should only be accessible to admin users
 */
export const AdminRoute = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show loading while auth is being checked
  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
        className="min-h-[60vh] flex items-center justify-center"
      >
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
      </motion.div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // Check if user is admin
  const isAdmin = user?.role === "admin" || user?.role === "ADMIN";

  if (!isAdmin) {
    return <AccessDenied />;
  }

  // User is admin, render children
  return children;
};

export default AdminRoute;
