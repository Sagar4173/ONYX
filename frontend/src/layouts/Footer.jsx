/**
 * Footer Component
 * Modern footer with version info, quick links, and social links
 */
import React from "react";
import { Link } from "react-router-dom";
import {
  ShieldCheckIcon,
  HeartIcon,
  CodeBracketIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  EnvelopeIcon,
  GlobeAltIcon,
} from "@heroicons/react/24/outline";

/**
 * Version Info Component
 */
const VersionInfo = () => {
  return (
    <div className="flex items-center gap-2 text-sm">
      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800/50 rounded-lg border border-gray-700/50">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span className="text-gray-400">v2.0.0</span>
      </div>
      <span className="text-gray-600">•</span>
      <span className="text-gray-500">API Status: Healthy</span>
    </div>
  );
};

/**
 * Social Links
 */
const SocialLinks = () => {
  const links = [
    {
      name: "GitHub",
      icon: CodeBracketIcon,
      href: "https://github.com/securedevops",
    },
    {
      name: "Documentation",
      icon: BookOpenIcon,
      href: "/docs",
    },
    {
      name: "Support",
      icon: ChatBubbleLeftRightIcon,
      href: "mailto:support@securedevops.ai",
    },
    {
      name: "Website",
      icon: GlobeAltIcon,
      href: "https://securedevops.ai",
    },
  ];

  return (
    <div className="flex items-center gap-2">
      {links.map((link) => (
        <a
          key={link.name}
          href={link.href}
          target={link.href.startsWith("http") ? "_blank" : undefined}
          rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
          className="p-2 text-gray-500 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all"
          title={link.name}
        >
          <link.icon className="h-4 w-4" />
        </a>
      ))}
    </div>
  );
};

/**
 * Quick Links Component
 */
const QuickLinks = () => {
  const links = [
    { name: "Privacy Policy", path: "/privacy" },
    { name: "Terms of Service", path: "/terms" },
    { name: "Security", path: "/security" },
    { name: "Status", path: "/status" },
  ];

  return (
    <div className="flex items-center gap-4">
      {links.map((link) => (
        <Link
          key={link.name}
          to={link.path}
          className="text-xs text-gray-500 hover:text-white transition-colors"
        >
          {link.name}
        </Link>
      ))}
    </div>
  );
};

/**
 * Compact Footer - For use in main layout
 */
export const CompactFooter = () => {
  return (
    <footer className="border-t border-gray-800/50 bg-gray-900/50">
      <div className="px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Left - Version & Status */}
          <VersionInfo />

          {/* Center - Copyright */}
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span>Made with</span>
            <HeartIcon className="h-4 w-4 text-red-500" />
            <span>by</span>
            <span className="text-white font-medium">SecureDevOps AI</span>
            <span className="text-gray-600">•</span>
            <span>© {new Date().getFullYear()}</span>
          </div>

          {/* Right - Social Links */}
          <SocialLinks />
        </div>
      </div>
    </footer>
  );
};

/**
 * Full Footer - For landing pages or expanded views
 */
export const FullFooter = () => {
  const footerSections = [
    {
      title: "Product",
      links: [
        { name: "Features", path: "/features" },
        { name: "Pricing", path: "/pricing" },
        { name: "Changelog", path: "/changelog" },
        { name: "Roadmap", path: "/roadmap" },
      ],
    },
    {
      title: "Resources",
      links: [
        { name: "Documentation", path: "/docs" },
        { name: "API Reference", path: "/api" },
        { name: "Blog", path: "/blog" },
        { name: "Community", path: "/community" },
      ],
    },
    {
      title: "Company",
      links: [
        { name: "About", path: "/about" },
        { name: "Careers", path: "/careers" },
        { name: "Contact", path: "/contact" },
        { name: "Partners", path: "/partners" },
      ],
    },
    {
      title: "Legal",
      links: [
        { name: "Privacy", path: "/privacy" },
        { name: "Terms", path: "/terms" },
        { name: "Security", path: "/security" },
        { name: "Compliance", path: "/compliance-info" },
      ],
    },
  ];

  return (
    <footer className="border-t border-gray-800/50 bg-gray-900/80 backdrop-blur-xl">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand Section */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">SecureDevOps</h3>
                <p className="text-xs text-gray-400">AI Security Platform</p>
              </div>
            </Link>
            <p className="text-sm text-gray-400 mb-4 max-w-xs">
              Enterprise-grade security scanning powered by AI. Protect your
              code, secure your future.
            </p>

            {/* Social Links */}
            <SocialLinks />
          </div>

          {/* Footer Sections */}
          {footerSections.map((section) => (
            <div key={section.title}>
              <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                {section.title}
              </h4>
              <ul className="space-y-3">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      to={link.path}
                      className="text-sm text-gray-400 hover:text-white transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-800/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            {/* Version Info */}
            <VersionInfo />

            {/* Copyright */}
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>© {new Date().getFullYear()} SecureDevOps AI.</span>
              <span>All rights reserved.</span>
            </div>

            {/* Quick Links */}
            <QuickLinks />
          </div>
        </div>
      </div>
    </footer>
  );
};

/**
 * Minimal Footer - Just copyright and essentials
 */
export const MinimalFooter = () => {
  return (
    <footer className="py-4 px-6">
      <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
        <span>© {new Date().getFullYear()} SecureDevOps AI</span>
        <span className="text-gray-700">•</span>
        <Link to="/privacy" className="hover:text-white transition-colors">
          Privacy
        </Link>
        <span className="text-gray-700">•</span>
        <Link to="/terms" className="hover:text-white transition-colors">
          Terms
        </Link>
        <span className="text-gray-700">•</span>
        <a
          href="mailto:support@securedevops.ai"
          className="hover:text-white transition-colors flex items-center gap-1"
        >
          <EnvelopeIcon className="h-3 w-3" />
          Support
        </a>
      </div>
    </footer>
  );
};

/**
 * Default Export - Compact footer for main layout
 */
export const Footer = CompactFooter;

export default Footer;
