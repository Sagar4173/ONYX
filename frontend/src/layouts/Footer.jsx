/**
 * Footer Component - Enterprise Glass Design
 * Minimal footer matching the project's glass morphism design
 */
import { ShieldCheckIcon, HeartIcon } from "@heroicons/react/24/solid";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative">
      {/* Glass background */}
      <div className="absolute inset-0 bg-gray-900/80 backdrop-blur-xl border-t border-gray-800/50" />
      
      {/* Content */}
      <div className="relative px-4 sm:px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left - Brand & Copyright */}
          <div className="flex items-center gap-3">
            {/* Logo Icon */}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20 
                          border border-blue-500/30 flex items-center justify-center">
              <ShieldCheckIcon className="w-4 h-4 text-blue-400" />
            </div>
            
            <div className="text-center sm:text-left">
              <p className="text-sm text-gray-400">
                <span className="font-medium text-gray-300">SecureDevOps AI</span>
                {" "}© {currentYear}
              </p>
            </div>
          </div>

          {/* Center - Version & Status */}
          <div className="flex items-center gap-4">
            {/* Version Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg 
                          bg-gray-800/50 border border-gray-700/50">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-gray-400">v1.0.0</span>
            </div>

            {/* Status Badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg 
                          bg-emerald-500/10 border border-emerald-500/30">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-xs text-emerald-400 font-medium">Operational</span>
            </div>
          </div>

          {/* Right - Links */}
          <div className="flex items-center gap-6 text-sm">
            <a 
              href="/docs" 
              className="text-gray-400 hover:text-white transition-colors"
            >
              Documentation
            </a>
            <a 
              href="/support" 
              className="text-gray-400 hover:text-white transition-colors"
            >
              Support
            </a>
            <span className="flex items-center gap-1.5 text-gray-500">
              Made with <HeartIcon className="w-3.5 h-3.5 text-rose-500" /> 
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
