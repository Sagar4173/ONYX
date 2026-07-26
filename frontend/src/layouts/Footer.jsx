/**
 * Footer Component - Enterprise Grade
 * Professional footer for ONYX Security Platform
 */
import { Link } from "react-router-dom";
import {
  DocumentTextIcon,
  QuestionMarkCircleIcon,
  LockClosedIcon,
  BookOpenIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../components/common";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = [
    { name: "Documentation", href: "/docs", icon: BookOpenIcon },
    { name: "API Reference", href: "/api-docs", icon: DocumentTextIcon },
    { name: "Security", href: "/security", icon: LockClosedIcon },
    { name: "Support", href: "/support", icon: QuestionMarkCircleIcon },
  ];

  return (
    <footer className="relative">
      {/* Glass background */}
      <div className="absolute inset-0 bg-gray-900/80 backdrop-blur-xl border-t border-gray-800/50" />

      {/* Content */}
      <div className="relative px-4 sm:px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left - Brand & Copyright */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-lg bg-gradient-to-br from-gray-900 to-gray-800 
                          flex items-center justify-center shadow-lg border border-cyan-500/30"
              >
                <OnyxLogo variant="mini" className="w-5 h-5" />
              </div>
              <div>
                <span className="text-sm font-bold text-white tracking-wide">ONYX</span>
              </div>
            </div>
            <div className="hidden sm:block w-px h-4 bg-gray-700" />
            <span className="text-xs text-gray-500">© {currentYear} All rights reserved</span>
          </div>

          {/* Center - Links */}
          <div className="flex items-center gap-1">
            {footerLinks.map((link) => (
              <Link
                key={link.name}
                to={link.href}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400
                         hover:text-white hover:bg-gray-800/50 rounded-lg transition-all
                         focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <link.icon className="w-3.5 h-3.5" aria-hidden="true" />
                <span className="hidden md:inline">{link.name}</span>
              </Link>
            ))}
          </div>

          {/* Right - Version */}
          <div className="flex items-center gap-3">
            <div
              className="flex items-center gap-2 px-2.5 py-1 rounded-md 
                        bg-gray-800/50 border border-gray-700/50"
            >
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Version</span>
              <span className="text-xs text-gray-300 font-mono">1.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
