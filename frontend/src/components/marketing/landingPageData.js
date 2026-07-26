import {
  ShieldCheckIcon,
  BoltIcon,
  CpuChipIcon,
  ChartBarIcon,
  LockClosedIcon,
  CodeBracketIcon,
  CheckCircleIcon,
  RocketLaunchIcon,
} from "@heroicons/react/24/outline";

export const features = [
  {
    title: "AI-Powered Analysis",
    description:
      "Dual AI engine combining GPT-4 and Gemini to detect complex vulnerabilities, logic flaws, and zero-day patterns.",
    icon: CpuChipIcon,
    gradient: "from-cyan-500 to-violet-600",
    stats: "99.9%",
    details: [
      "Real-time code analysis with GPT-4 and Gemini",
      "Context-aware vulnerability detection",
      "False positive reduction through cross-referencing",
      "Pattern recognition for zero-day exploits",
      "Natural language remediation suggestions",
    ],
  },
  {
    title: "Multi-Layer Protection",
    description:
      "Comprehensive security scanning across SAST, DAST, SCA, secrets detection, and infrastructure analysis.",
    icon: ShieldCheckIcon,
    gradient: "from-violet-500 to-purple-600",
    stats: "10",
    details: [
      "Static code analysis (SAST) for 15+ languages",
      "Dynamic analysis for running applications",
      "Software composition analysis for dependencies",
      "Secret detection for credentials and keys",
      "Infrastructure-as-code security scanning",
    ],
  },
  {
    title: "Real-Time Detection",
    description:
      "Continuous monitoring with instant alerts when vulnerabilities are discovered in your codebase.",
    icon: BoltIcon,
    gradient: "from-emerald-500 to-green-600",
    stats: "<100ms",
    details: [
      "Instant webhook notifications for critical issues",
      "Real-time dashboard with live updates",
      "Automated PR comments on new findings",
      "Slack, email, and PagerDuty integrations",
      "Scheduled scanning with cron triggers",
    ],
  },
  {
    title: "Vulnerability Intelligence",
    description:
      "Stay ahead of emerging threats with our constantly updated vulnerability database and CVE tracking.",
    icon: ChartBarIcon,
    gradient: "from-orange-500 to-amber-600",
    stats: "50K+",
    details: [
      "Comprehensive CVE database integration",
      "Zero-day vulnerability monitoring",
      "Exploit prediction and risk scoring",
      "Vendor security advisory tracking",
      "Automated patch recommendation engine",
    ],
  },
  {
    title: "Compliance Automation",
    description:
      "Automatically map findings to compliance frameworks and generate audit-ready reports.",
    icon: LockClosedIcon,
    gradient: "from-red-500 to-rose-600",
    stats: "9",
    details: [
      "OWASP Top 10 automated mapping",
      "PCI-DSS compliance scanning",
      "SOC 2 readiness reports",
      "GDPR data protection checks",
      "HIPAA security rule compliance",
    ],
  },
  {
    title: "DevSecOps Integration",
    description:
      "Seamlessly integrate security into your existing CI/CD pipeline with zero configuration overhead.",
    icon: CodeBracketIcon,
    gradient: "from-blue-500 to-cyan-600",
    stats: "15min",
    details: [
      "GitHub Actions native integration",
      "GitLab CI/CD pipeline support",
      "Jenkins plugin for enterprise",
      "Pre-commit hooks for local scanning",
      "Container registry scanning integration",
    ],
  },
];

export const securityMetrics = [
  { label: "Scans Completed", icon: CheckCircleIcon, key: "scans" },
  { label: "Vulnerabilities Found", icon: ShieldCheckIcon, key: "vulnerabilities" },
  { label: "Developers Protected", icon: CodeBracketIcon, key: "developers" },
  { label: "Platform Uptime", icon: RocketLaunchIcon, key: "uptime" },
];

export const scanners = [
  {
    name: "Semgrep",
    icon: "🔍",
    category: "SAST",
    description: "Static analysis for multiple languages",
    what: "Scans Python, JavaScript, TypeScript, Java, and Go for custom security patterns and code quality issues using 2,000+ community rules.",
  },
  {
    name: "Bandit",
    icon: "🐍",
    category: "SAST",
    description: "Python security linter",
    what: "Detects common Python security issues including SQL injection, command injection, hardcoded passwords, and insecure deserialization.",
  },
  {
    name: "CodeQL",
    icon: "🔬",
    category: "SAST",
    description: "Semantic code analysis",
    what: "Powers GitHub code scanning with deep semantic analysis across multiple languages to find complex vulnerabilities.",
  },
  {
    name: "GitLeaks",
    icon: "🔑",
    category: "Secrets",
    description: "Secret detection engine",
    what: "Detects hardcoded secrets, API keys, tokens, and credentials in your repositories using entropy analysis and pattern matching.",
  },
  {
    name: "Safety",
    icon: "📦",
    category: "SCA",
    description: "Dependency vulnerability check",
    what: "Checks Python dependencies against a database of known vulnerabilities and suggests secure version upgrades.",
  },
  {
    name: "Trivy",
    icon: "🐳",
    category: "Container",
    description: "Container image scanner",
    what: "Comprehensive vulnerability scanning for container images, detecting OS packages, libraries, and misconfigurations.",
  },
  {
    name: "OWASP ZAP",
    icon: "🕷️",
    category: "DAST",
    description: "Web application scanner",
    what: "Dynamic application security testing that finds vulnerabilities in running web applications through automated attacks.",
  },
  {
    name: "Nuclei",
    icon: "🎯",
    category: "DAST",
    description: "Template-based scanner",
    what: "Fast vulnerability scanner using YAML templates to probe for known CVEs, misconfigurations, and exposed services.",
  },
  {
    name: "Checkov",
    icon: "🏗️",
    category: "IaC",
    description: "Infrastructure scanner",
    what: "Scans Terraform, CloudFormation, Kubernetes, and ARM templates for security misconfigurations and compliance violations.",
  },
  {
    name: "Lynis",
    icon: "🖥️",
    category: "IaC",
    description: "System hardening audit",
    what: "Security auditing tool for Unix-based systems that performs deep system configuration analysis and hardening recommendations.",
  },
];

export const pricingPlans = [
  {
    name: "Free",
    price: "$0",
    period: "month",
    description: "Perfect for individual developers",
    cta: "Get Started",
    popular: false,
    features: [
      "Up to 3 projects",
      "10 scans per month",
      "Basic vulnerability scanning",
      "Email support",
      "Community access",
      "Public repository scanning",
    ],
  },
  {
    name: "Pro",
    price: "$29",
    period: "month",
    description: "For growing security teams",
    cta: "Start Free Trial",
    popular: true,
    features: [
      "Unlimited projects",
      "1,000 scans per month",
      "AI-powered analysis",
      "Priority support",
      "CI/CD integration",
      "Private repository scanning",
      "Custom rules engine",
      "API access",
      "Team collaboration",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "month",
    description: "For large organizations",
    cta: "Contact Sales",
    popular: false,
    features: [
      "Everything in Pro",
      "Unlimited scans",
      "On-premise deployment",
      "Custom compliance frameworks",
      "SLA guarantee",
      "Dedicated support",
      "Advanced reporting",
      "SSO/SAML integration",
      "Audit logs",
      "Custom integrations",
    ],
  },
];

export const complianceFrameworks = [
  { name: "OWASP Top 10", icon: "🛡️" },
  { name: "NIST 800-53", icon: "🏛️" },
  { name: "ISO 27001", icon: "📋" },
  { name: "PCI-DSS", icon: "💳" },
  { name: "HIPAA", icon: "🏥" },
  { name: "SOC 2", icon: "🔒" },
  { name: "GDPR", icon: "🇪🇺" },
  { name: "CIS Controls", icon: "⚙️" },
  { name: "MITRE ATT&CK", icon: "🎯" },
];

export const platformHighlights = [
  {
    category: "Enterprise Security",
    title: "Bank-Grade Protection",
    highlight: "🛡️",
    description:
      "SOC 2 compliant with end-to-end encryption. Your code never leaves our secure environment. Enterprise-grade access controls and audit logging.",
  },
  {
    category: "Compliance Ready",
    title: "Audit-Ready Reports",
    highlight: "📋",
    description:
      "Automated compliance mapping for 9 major frameworks including OWASP, NIST, ISO 27001, PCI-DSS, HIPAA, and SOC 2.",
  },
  {
    category: "Developer Friendly",
    title: "Fast & Non-Intrusive",
    highlight: "⚡",
    description:
      "Lightweight scanning that won't slow down your CI/CD pipeline. Average scan time under 60 seconds for most repositories.",
  },
];

export const fixSuggestions = {
  sql: {
    title: "SQL Injection Vulnerability",
    severity: "Critical",
    problem:
      "User input is directly interpolated into an SQL query string, allowing attackers to manipulate the query structure.",
    fix: '// BEFORE - VULNERABLE\nconst query = `SELECT * FROM users WHERE id = ${userId}`;\n\n// AFTER - FIXED\nconst query = "SELECT * FROM users WHERE id = ?";\ndb.execute(query, [userId]);',
    explanation:
      "Use parameterized queries instead of string interpolation. Parameterized queries escape user input automatically, preventing SQL injection attacks. This is the single most effective defense against SQL injection.",
  },
  secret: {
    title: "Hardcoded API Secret",
    severity: "High",
    problem:
      "An API secret key is hardcoded directly in the source code. Anyone with access to the repository can use this key.",
    fix: '// BEFORE - VULNERABLE\nconst API_KEY = "sk_live_abc123xyz";\n\n// AFTER - FIXED\nconst API_KEY = process.env.API_KEY;\n\n// BEST - USE SECRETS MANAGER\nconst API_KEY = await secretsManager.getSecret("api-key");',
    explanation:
      "Never hardcode secrets in source code. Use environment variables for local development. For production, use a secrets manager like HashiCorp Vault or AWS Secrets Manager.",
  },
};
