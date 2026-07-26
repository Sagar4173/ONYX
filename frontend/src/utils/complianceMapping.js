export const COMPLIANCE_STANDARDS = {
  OWASP: {
    name: "OWASP Top 10",
    description: "Web Application Security",
    color: "#f43f5e",
    categories: [
      {
        id: "A01",
        name: "Broken Access Control",
        description: "Failure to enforce user permissions",
      },
      { id: "A02", name: "Cryptographic Failures", description: "Weak or missing encryption" },
      { id: "A03", name: "Injection", description: "SQL, XSS, and command injection" },
      { id: "A04", name: "Insecure Design", description: "Architecture-level flaws" },
      { id: "A05", name: "Security Misconfiguration", description: "Default or insecure configs" },
      { id: "A06", name: "Vulnerable Components", description: "Outdated dependencies" },
      { id: "A07", name: "Auth Failures", description: "Broken authentication" },
      { id: "A08", name: "Data Integrity", description: "Software supply chain" },
      { id: "A09", name: "Logging Failures", description: "Insufficient monitoring" },
      { id: "A10", name: "SSRF", description: "Server-side request forgery" },
    ],
  },
  NIST: {
    name: "NIST CSF",
    description: "Cybersecurity Framework",
    color: "#3b82f6",
    categories: [
      { id: "ID", name: "Identify", description: "Asset management and risk assessment" },
      { id: "PR", name: "Protect", description: "Safeguards and access control" },
      { id: "DE", name: "Detect", description: "Monitoring and anomaly detection" },
      { id: "RS", name: "Respond", description: "Incident response planning" },
      { id: "RC", name: "Recover", description: "Resilience and restoration" },
    ],
  },
  ISO27001: {
    name: "ISO 27001",
    description: "Information Security Standard",
    color: "#8b5cf6",
    categories: [
      { id: "A.5", name: "Security Policies", description: "Management direction" },
      { id: "A.6", name: "Organization", description: "Internal security roles" },
      { id: "A.7", name: "HR Security", description: "Personnel vetting" },
      { id: "A.8", name: "Asset Management", description: "Asset inventory" },
      { id: "A.9", name: "Access Control", description: "Authentication and authorization" },
      { id: "A.10", name: "Cryptography", description: "Encryption key management" },
      { id: "A.11", name: "Physical Security", description: "Facility protection" },
      { id: "A.12", name: "Operations", description: "Change and capacity management" },
      { id: "A.13", name: "Communications", description: "Network security" },
      { id: "A.14", name: "Development", description: "Secure development lifecycle" },
      { id: "A.15", name: "Supplier", description: "Third-party security" },
      { id: "A.16", name: "Incident", description: "Incident management" },
    ],
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
