export const COMPLIANCE_STANDARDS = {
  OWASP: {
    name: "OWASP Top 10",
    description: "Web Application Security",
    icon: "🔐",
    color: "#f43f5e",
    categories: {
      A01: "Broken Access Control",
      A02: "Cryptographic Failures",
      A03: "Injection",
      A04: "Insecure Design",
      A05: "Security Misconfiguration",
      A06: "Vulnerable Components",
      A07: "Auth Failures",
      A08: "Data Integrity",
      A09: "Logging Failures",
      A10: "SSRF",
    },
  },
  NIST: {
    name: "NIST CSF",
    description: "Cybersecurity Framework",
    icon: "🏛️",
    color: "#3b82f6",
    categories: {
      ID: "Identify",
      PR: "Protect",
      DE: "Detect",
      RS: "Respond",
      RC: "Recover",
    },
  },
  ISO27001: {
    name: "ISO 27001",
    description: "Information Security Standard",
    icon: "📋",
    color: "#8b5cf6",
    categories: {
      "A.5": "Security Policies",
      "A.6": "Organization",
      "A.7": "HR Security",
      "A.8": "Asset Management",
      "A.9": "Access Control",
      "A.10": "Cryptography",
      "A.11": "Physical Security",
      "A.12": "Operations",
      "A.13": "Communications",
      "A.14": "Development",
      "A.15": "Supplier",
      "A.16": "Incident",
    },
  },
};

export const mapFindingToCompliance = (finding, standard) => {
  const description = (finding.description || finding.title || "").toLowerCase();
  const categories = [];

  switch (standard) {
    case "OWASP":
      if (
        description.includes("access") ||
        description.includes("authorization") ||
        description.includes("permission")
      ) {
        categories.push("A01");
      }
      if (
        description.includes("crypto") ||
        description.includes("encryption") ||
        description.includes("hash") ||
        description.includes("password")
      ) {
        categories.push("A02");
      }
      if (
        description.includes("injection") ||
        description.includes("sql") ||
        description.includes("xss") ||
        description.includes("command")
      ) {
        categories.push("A03");
      }
      if (
        description.includes("misconfiguration") ||
        description.includes("default") ||
        description.includes("config")
      ) {
        categories.push("A05");
      }
      if (
        description.includes("component") ||
        description.includes("dependency") ||
        description.includes("outdated") ||
        description.includes("vulnerable")
      ) {
        categories.push("A06");
      }
      if (
        description.includes("auth") ||
        description.includes("session") ||
        description.includes("token")
      ) {
        categories.push("A07");
      }
      if (categories.length === 0) categories.push("A05");
      break;
    case "NIST":
      categories.push("ID");
      if (
        description.includes("protect") ||
        description.includes("secure") ||
        description.includes("encrypt")
      ) {
        categories.push("PR");
      }
      if (
        description.includes("detect") ||
        description.includes("monitor") ||
        description.includes("log")
      ) {
        categories.push("DE");
      }
      break;
    case "ISO27001":
      if (description.includes("access") || description.includes("authentication")) {
        categories.push("A.9");
      }
      if (description.includes("crypto") || description.includes("encryption")) {
        categories.push("A.10");
      }
      if (description.includes("development") || description.includes("code")) {
        categories.push("A.14");
      }
      if (categories.length === 0) categories.push("A.12");
      break;
  }
  return categories;
};
