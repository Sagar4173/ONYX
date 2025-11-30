/**
 * Footer Component - Clean Production UI
 * Simple, professional footer
 */
import { Link } from "react-router-dom";

const VERSION = import.meta.env.VITE_APP_VERSION || "2.5.0";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 border-t border-slate-800">
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left: Copyright */}
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <span>© {currentYear} SecureDevOps AI</span>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">v{VERSION}</span>
          </div>

          {/* Right: Links */}
          <div className="flex items-center gap-6">
            <Link
              to="/docs"
              className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              Documentation
            </Link>
            <Link
              to="/support"
              className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              Support
            </Link>
            <Link
              to="/privacy"
              className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              Privacy
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
