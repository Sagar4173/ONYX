/**
 * NotFound Page - 404 Error Page
 * Professional error handling for unmatched routes
 */

import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { HomeIcon, ExclamationTriangleIcon, ArrowLeftIcon } from "@heroicons/react/24/outline";
import { PageContainer } from "../layouts";

const NotFound = () => {
  return (
    <PageContainer>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="min-h-[70vh] flex items-center justify-center"
      >
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.08 } },
          }}
          className="text-center max-w-md mx-auto"
        >
          <motion.div
            variants={{
              hidden: { opacity: 0, scale: 0.8 },
              visible: { opacity: 1, scale: 1 },
            }}
            className="relative mb-8"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-full blur-3xl" />
            <div className="relative inline-flex p-6 rounded-3xl bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20">
              <ExclamationTriangleIcon className="h-16 w-16 text-red-400" />
            </div>
          </motion.div>

          <motion.h1
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="text-6xl sm:text-7xl font-bold text-white mb-4"
          >
            404
          </motion.h1>

          <motion.h2
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="text-xl sm:text-2xl font-semibold text-white mb-3"
          >
            Page Not Found
          </motion.h2>

          <motion.p
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="text-gray-400 mb-8 leading-relaxed"
          >
            The page you're looking for doesn't exist or has been moved. Let's get you back on
            track.
          </motion.p>

          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200"
            >
              <HomeIcon className="h-5 w-5" />
              Go to Dashboard
            </Link>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-800/50 border border-gray-700/50 text-gray-300 hover:text-white font-medium rounded-xl hover:bg-gray-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 transition-all"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              Go Back
            </button>
          </motion.div>

          <motion.div
            variants={{
              hidden: { opacity: 0 },
              visible: { opacity: 1 },
            }}
            className="mt-12 pt-8 border-t border-gray-800/50"
          >
            <p className="text-sm text-gray-500 mb-4">Quick Links</p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/projects"
                className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
              >
                Projects
              </Link>
              <Link
                to="/reports"
                className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
              >
                Reports
              </Link>
              <Link
                to="/analytics"
                className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
              >
                Analytics
              </Link>
              <Link
                to="/settings"
                className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
              >
                Settings
              </Link>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </PageContainer>
  );
};

export default NotFound;
