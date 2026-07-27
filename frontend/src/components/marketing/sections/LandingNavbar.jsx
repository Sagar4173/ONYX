import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRightIcon } from "@heroicons/react/24/outline";
import { OnyxLogo } from "../../common";

const navLinks = [
  { name: "Features", id: "features" },
  { name: "Scanners", id: "scanners" },
  { name: "Pricing", id: "pricing" },
  { name: "Why ONYX", id: "why-onyx" },
];

const LandingNavbar = ({ scrollY, isNavOpen, setIsNavOpen, scrollToSection }) => {
  const navigate = useNavigate();

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrollY > 50
          ? "bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50 shadow-2xl"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
              <OnyxLogo variant="glow" className="w-10 h-10 relative" />
            </div>
            <div>
              <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
                ONYX
              </span>
              <span className="hidden sm:block text-[10px] text-gray-500 uppercase tracking-[0.2em] -mt-1">
                Security Intelligence
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-gray-400 hover:text-white transition-colors text-sm font-medium relative group"
              >
                {item.name}
                <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-cyan-500 to-violet-500 group-hover:w-full transition-all duration-300" />
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsNavOpen(!isNavOpen)}
            aria-label={isNavOpen ? "Close navigation menu" : "Open navigation menu"}
            className="md:hidden p-2 text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isNavOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>

          <div className="hidden md:flex items-center space-x-4">
            <button
              onClick={() => navigate("/login")}
              className="hidden sm:block text-gray-300 hover:text-white transition-colors text-sm font-medium"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate("/register")}
              className="relative group px-5 py-2.5 rounded-xl font-semibold text-sm overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600 transition-transform group-hover:scale-105" />
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="relative text-white flex items-center gap-2">
                Start Free Trial
                <ArrowRightIcon className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </span>
            </button>
          </div>
        </div>

        <AnimatePresence>
          {isNavOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="md:hidden overflow-hidden"
            >
              <div className="mt-4 pb-4 border-t border-gray-800/50 pt-4">
            <div className="flex flex-col space-y-3">
              {navLinks.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className="text-gray-400 hover:text-white transition-colors text-sm font-medium text-left py-2"
                >
                  {item.name}
                </button>
              ))}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => navigate("/login")}
                  className="flex-1 py-2 text-gray-300 hover:text-white transition-colors text-sm font-medium border border-gray-700 rounded-lg"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate("/register")}
                  className="flex-1 py-2 bg-gradient-to-r from-cyan-500 to-violet-600 text-white text-sm font-medium rounded-lg"
                >
                  Start Free
                </button>
              </div>
            </div>
          </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
};

export default LandingNavbar;
