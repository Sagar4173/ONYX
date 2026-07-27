import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { OnyxLogo } from "../../common";

const socialLinks = [
  { name: "GitHub", href: "#" },
  { name: "Twitter", href: "#" },
  { name: "LinkedIn", href: "#" },
  { name: "Discord", href: "#" },
];

const footerLinks = {
  Product: [
    { name: "Features", action: "features" },
    { name: "Pricing", action: "pricing" },
    { name: "Integrations", action: "integrations" },
    { name: "Changelog", action: "changelog" },
    { name: "Documentation", href: "/docs" },
  ],
  Resources: [
    { name: "Documentation", href: "/docs" },
    { name: "API Reference", href: "/docs" },
    { name: "Security Blog", href: "#" },
    { name: "Community", href: "#" },
    { name: "Support", href: "#" },
  ],
  Company: [
    { name: "About", href: "/about" },
    { name: "Terms", href: "/terms" },
    { name: "Privacy", href: "/legal" },
    { name: "Contact", href: "#" },
    { name: "Status", href: "#" },
  ],
};

const LandingFooter = () => {
  const navigate = useNavigate();

  const handleClick = (item) => {
    if (item.action) {
      const el = document.getElementById(item.action);
      if (el) el.scrollIntoView({ behavior: "smooth" });
    } else if (item.href?.startsWith("/")) {
      navigate(item.href);
    }
  };

  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="border-t border-gray-800/50 bg-gray-950"
    >
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          <div>
            <Link to="/" className="flex items-center space-x-3 group mb-4">
              <OnyxLogo variant="glow" className="w-8 h-8" />
              <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
                ONYX
              </span>
            </Link>
            <p className="text-gray-500 text-sm leading-relaxed mb-6">
              AI-powered security scanning platform. Protect your code with 10 specialized scanners
              powered by GPT-4 and Gemini AI.
            </p>
            <div className="flex gap-4">
              {socialLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  aria-label={link.name}
                  className="text-gray-500 hover:text-cyan-400 transition-colors text-sm"
                >
                  {link.name}
                </a>
              ))}
            </div>
          </div>
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-white font-semibold mb-4">{title}</h4>
              <ul className="space-y-3">
                {links.map((item) => (
                  <li key={item.name}>
                    <button
                      onClick={() => handleClick(item)}
                      className="text-gray-500 hover:text-cyan-400 transition-colors text-sm"
                    >
                      {item.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-gray-800/50 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-gray-600 text-sm">
            &copy; {new Date().getFullYear()} ONYX Security. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-gray-600">
            <a href="/terms" className="hover:text-gray-400 transition-colors">
              Terms
            </a>
            <a href="/legal" className="hover:text-gray-400 transition-colors">
              Privacy
            </a>
            <a href="/docs" className="hover:text-gray-400 transition-colors">
              Docs
            </a>
          </div>
        </div>
      </div>
    </motion.footer>
  );
};

export default LandingFooter;
