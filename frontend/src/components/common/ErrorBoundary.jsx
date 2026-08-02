/**
 * Error Boundary Component for ONYX Platform
 * Catches JavaScript errors anywhere in the component tree and displays a fallback UI
 */
import React from "react";
import { motion } from "framer-motion";
import { ExclamationTriangleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(_error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });

    // In production, you could send this to an error reporting service
    if (import.meta.env.PROD) {
      // Example: Send to error tracking service
      // errorTrackingService.log(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1, ease: "easeOut" }}
            className="max-w-md w-full bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-8 text-center"
          >
            {/* Error Icon */}
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-6">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>

            {/* Description */}
            <p className="text-gray-400 mb-6">
              We're sorry, but something unexpected happened. Please try again or reload the page.
            </p>

            {/* Error Details (Development only) */}
            {this.state.error && (
              <details className="mb-6 p-4 bg-gray-900/50 rounded-lg text-left overflow-auto max-h-40">
                <summary className="text-red-400 text-sm font-mono cursor-pointer select-none">
                  {this.state.error.toString()}
                </summary>
                {this.state.errorInfo && (
                  <pre className="text-gray-500 text-xs mt-2 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                type="button"
                onClick={this.handleRetry}
                className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium rounded-lg hover:from-cyan-600 hover:to-violet-700 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <ArrowPathIcon className="h-5 w-5 mr-2" aria-hidden="true" />
                Try Again
              </button>
              <button
                type="button"
                onClick={this.handleReload}
                className="inline-flex items-center justify-center px-6 py-3 bg-gray-700 text-white font-medium rounded-lg hover:bg-gray-600 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                Reload Page
              </button>
            </div>

            {/* Support Link */}
            <p className="text-gray-500 text-sm mt-6">
              If the problem persists,{" "}
              <a
                href="mailto:support@onyx-platform.com"
                className="text-cyan-400 hover:text-cyan-300 underline"
              >
                contact support
              </a>
            </p>
          </motion.div>
        </motion.div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
