export const frameworks = [
  {
    id: "sox",
    name: "SOX",
    fullName: "Sarbanes-Oxley Act",
    description: "Financial reporting and internal controls",
    color: "from-blue-500 to-cyan-500",
    icon: "💼",
  },
  {
    id: "hipaa",
    name: "HIPAA",
    fullName: "Health Insurance Portability and Accountability Act",
    description: "Healthcare data privacy and security",
    color: "from-green-500 to-emerald-500",
    icon: "🏥",
  },
  {
    id: "iso27001",
    name: "ISO 27001",
    fullName: "ISO/IEC 27001",
    description: "Information security management",
    color: "from-purple-500 to-pink-500",
    icon: "🔒",
  },
  {
    id: "pci_dss",
    name: "PCI DSS",
    fullName: "Payment Card Industry Data Security Standard",
    description: "Payment card data protection",
    color: "from-orange-500 to-red-500",
    icon: "💳",
  },
  {
    id: "gdpr",
    name: "GDPR",
    fullName: "General Data Protection Regulation",
    description: "EU data protection and privacy",
    color: "from-cyan-500 to-violet-500",
    icon: "🇪🇺",
  },
  {
    id: "soc2",
    name: "SOC 2",
    fullName: "Service Organization Control 2",
    description: "Service provider security controls",
    color: "from-teal-500 to-cyan-500",
    icon: "🛡️",
  },
  {
    id: "nist",
    name: "NIST",
    fullName: "NIST Cybersecurity Framework",
    description: "Risk-based cybersecurity guidance",
    color: "from-indigo-500 to-purple-500",
    icon: "🔐",
  },
  {
    id: "cis",
    name: "CIS",
    fullName: "CIS Controls",
    description: "Cybersecurity best practices",
    color: "from-yellow-500 to-orange-500",
    icon: "⚡",
  },
  {
    id: "owasp",
    name: "OWASP",
    fullName: "OWASP Top 10",
    description: "Web application security risks",
    color: "from-red-500 to-pink-500",
    icon: "🌐",
  },
];

export const getScoreColor = (score) => {
  if (score >= 90) return "text-green-400 bg-green-500/20";
  if (score >= 70) return "text-yellow-400 bg-yellow-500/20";
  if (score >= 50) return "text-orange-400 bg-orange-500/20";
  return "text-red-400 bg-red-500/20";
};

export const getScoreGradient = (score) => {
  if (score >= 90) return "from-green-500 to-emerald-500";
  if (score >= 70) return "from-yellow-500 to-orange-500";
  if (score >= 50) return "from-orange-500 to-red-500";
  return "from-red-500 to-pink-500";
};

export const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return isNaN(date.getTime()) ? "N/A" : date.toLocaleString();
};

export const getFrameworkInfo = (frameworkId) => frameworks.find((f) => f.id === frameworkId);
