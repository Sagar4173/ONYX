import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ShieldCheckIcon,
  SparklesIcon,
  CubeTransparentIcon,
  ChartBarIcon,
  CloudArrowUpIcon,
  LockClosedIcon,
  BoltIcon,
  CommandLineIcon,
  EyeIcon,
  CpuChipIcon,
  ServerStackIcon,
  CodeBracketIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  PlayIcon,
  ChevronRightIcon,
  BeakerIcon,
  FingerPrintIcon,
  GlobeAltIcon,
  RocketLaunchIcon,
  ArrowTrendingUpIcon,
  UserGroupIcon,
  BuildingOffice2Icon,
  AcademicCapIcon,
  DocumentCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowDownIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { StarIcon, CheckBadgeIcon } from "@heroicons/react/24/solid";
import { OnyxLogo } from "../common";

// Typing animation component
const TypeWriter = ({ words, className }) => {
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const word = words[currentWordIndex];
    const timeout = setTimeout(
      () => {
        if (!isDeleting) {
          if (currentText.length < word.length) {
            setCurrentText(word.slice(0, currentText.length + 1));
          } else {
            setTimeout(() => setIsDeleting(true), 2000);
          }
        } else {
          if (currentText.length > 0) {
            setCurrentText(word.slice(0, currentText.length - 1));
          } else {
            setIsDeleting(false);
            setCurrentWordIndex((prev) => (prev + 1) % words.length);
          }
        }
      },
      isDeleting ? 50 : 100
    );
    return () => clearTimeout(timeout);
  }, [currentText, isDeleting, currentWordIndex, words]);

  return (
    <span className={className}>
      {currentText}
      <span className="animate-pulse text-cyan-400">|</span>
    </span>
  );
};

// Animated counter component
const AnimatedCounter = ({ end, suffix = "" }) => {
  const [count, setCount] = useState(0);
  const countRef = useRef(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          let start = 0;
          const duration = 2000;
          const startTime = Date.now();
          const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 4);
            setCount(Math.floor(easeOut * end));
            if (progress < 1) requestAnimationFrame(animate);
          };
          animate();
        }
      },
      { threshold: 0.5 }
    );
    if (countRef.current) observer.observe(countRef.current);
    return () => observer.disconnect();
  }, [end]);

  return (
    <span ref={countRef}>
      {count.toLocaleString()}
      {suffix}
    </span>
  );
};

// Floating particles background
const FloatingParticles = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none">
    {[...Array(15)].map((_, i) => (
      <div
        key={i}
        className="absolute w-1 h-1 bg-cyan-500/30 rounded-full"
        style={{
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          animation: `float ${5 + Math.random() * 10}s ease-in-out infinite`,
          animationDelay: `${Math.random() * 5}s`,
        }}
      />
    ))}
    <style>{`
      @keyframes float {
        0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
        50% { transform: translateY(-30px) scale(1.5); opacity: 0.8; }
      }
    `}</style>
  </div>
);

const LandingPage = () => {
  const navigate = useNavigate();
  const [activeFeature, setActiveFeature] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [counters, setCounters] = useState({
    scans: 0,
    vulnerabilities: 0,
    developers: 0,
    uptime: 99.9,
  });
  const [isVisible, setIsVisible] = useState({});
  const heroRef = useRef(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [showFixModal, setShowFixModal] = useState(null); // null, 'sql', or 'secret'

  // Words for typing animation
  const heroWords = [
    "Vulnerabilities",
    "Threats",
    "Breaches",
    "Attacks",
    "Risks",
  ];

  // Smooth scroll to section
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    setIsNavOpen(false);
  };

  // Handle scroll
  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Handle mouse move for hero parallax
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Fetch real stats from backend API
  useEffect(() => {
    const fetchRealStats = async () => {
      try {
        const API_URL = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";
        const response = await fetch(`${API_URL}/api/stats/public`);
        if (response.ok) {
          const data = await response.json();
          // Use real data from API
          setCounters({
            scans: data.total_scans || 0,
            vulnerabilities: data.total_vulnerabilities || 0,
            developers: data.total_users || 0,
            uptime: data.uptime_percentage || 99.9,
          });
        } else {
          // Fallback: Calculate from actual database queries
          // This shows 0 if no data instead of fake numbers
          setCounters({
            scans: 0,
            vulnerabilities: 0,
            developers: 0,
            uptime: 99.9,
          });
        }
      } catch (error) {
        // On error, show zeros instead of fake data
        console.log("Stats API not available, showing placeholder");
        setCounters({
          scans: 0,
          vulnerabilities: 0,
          developers: 0,
          uptime: 99.9,
        });
      }
    };
    fetchRealStats();
  }, []);

  // Auto-rotate features
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % features.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  // Auto-rotate testimonials
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const features = [
    {
      icon: CpuChipIcon,
      title: "AI-Powered Analysis",
      description:
        "Dual AI provider support with OpenAI GPT-4 and Google Gemini to analyze vulnerabilities, explain risks in plain language, and suggest code fixes automatically.",
      gradient: "from-cyan-500 to-blue-600",
      stats: "GPT-4 + Gemini",
      details: [
        "Vulnerability explanation in plain language",
        "Risk assessment and prioritization",
        "Automated code fix suggestions",
        "False positive detection",
        "Remediation guidance generation",
      ],
    },
    {
      icon: ShieldCheckIcon,
      title: "Multi-Layer Protection",
      description:
        "Comprehensive defense-in-depth with 10 specialized security scanners covering SAST, DAST, secrets, containers, and infrastructure.",
      gradient: "from-violet-500 to-purple-600",
      stats: "10 scanners",
      details: [
        "SAST: Semgrep, Bandit, CodeQL",
        "DAST: OWASP ZAP, Nuclei",
        "Secrets: GitLeaks, detect-secrets",
        "Container: Trivy scanning",
        "IaC: Checkov, Lynis",
      ],
    },
    {
      icon: BoltIcon,
      title: "Real-Time Detection",
      description:
        "WebSocket-powered live scan progress updates. See vulnerabilities as they're found, not after the scan completes.",
      gradient: "from-amber-500 to-orange-600",
      stats: "Live WebSocket",
      details: [
        "Real-time scan progress",
        "Instant finding notifications",
        "Live dashboard updates",
        "Webhook integrations",
        "Email alerts on completion",
      ],
    },
    {
      icon: GlobeAltIcon,
      title: "Vulnerability Intelligence",
      description:
        "Integration with NVD (National Vulnerability Database) and OSV for comprehensive CVE data, CVSS scoring, and exploit information.",
      gradient: "from-emerald-500 to-teal-600",
      stats: "NVD + OSV",
      details: [
        "NVD CVE database integration",
        "Google OSV vulnerability data",
        "CVSS score enrichment",
        "Exploit availability tracking",
        "Automated severity mapping",
      ],
    },
    {
      icon: DocumentCheckIcon,
      title: "Compliance Automation",
      description:
        "Built-in compliance mapping for 9 major frameworks including OWASP Top 10, NIST, PCI-DSS, HIPAA, SOC2, and more.",
      gradient: "from-rose-500 to-pink-600",
      stats: "9 frameworks",
      details: [
        "OWASP Top 10 mapping",
        "NIST 800-53 controls",
        "PCI-DSS requirements",
        "HIPAA security rules",
        "SOC2, GDPR, ISO27001, CIS, MITRE",
      ],
    },
    {
      icon: RocketLaunchIcon,
      title: "DevSecOps Integration",
      description:
        "Connect with GitHub, GitLab, and Bitbucket. Webhook support for CI/CD pipelines. RESTful API for custom integrations.",
      gradient: "from-indigo-500 to-blue-600",
      stats: "REST API",
      details: [
        "GitHub, GitLab, Bitbucket support",
        "Webhook triggers for CI/CD",
        "Full REST API access",
        "JWT authentication",
        "Role-based access control",
      ],
    },
  ];

  const securityMetrics = [
    {
      label: "Scans Completed",
      value: counters.scans.toLocaleString(),
      icon: ChartBarIcon,
    },
    {
      label: "Vulnerabilities Found",
      value: counters.vulnerabilities.toLocaleString(),
      icon: ExclamationTriangleIcon,
    },
    {
      label: "Developers Protected",
      value: counters.developers.toLocaleString() + "+",
      icon: UserGroupIcon,
    },
    { label: "Platform Uptime", value: counters.uptime + "%", icon: ClockIcon },
  ];

  const scanners = [
    {
      name: "Semgrep",
      category: "SAST",
      type: "sast",
      description: "Multi-language semantic code analysis with custom rules",
      icon: "🔍",
      what: "Finds security vulnerabilities, bugs, and code patterns across 30+ languages using semantic pattern matching.",
    },
    {
      name: "Bandit",
      category: "SAST",
      type: "sast",
      description: "Python-specific security vulnerability detection",
      icon: "🐍",
      what: "Scans Python code for common security issues like SQL injection, hardcoded passwords, and unsafe function calls.",
    },
    {
      name: "CodeQL",
      category: "SAST",
      type: "sast",
      description: "Advanced semantic code analysis by GitHub",
      icon: "🔬",
      what: "Uses database queries to find complex vulnerability patterns, data flow issues, and security anti-patterns.",
    },
    {
      name: "GitLeaks",
      category: "Secrets",
      type: "secrets",
      description: "Detect hardcoded secrets and credentials",
      icon: "🔐",
      what: "Scans git history and current code for API keys, passwords, tokens, and other sensitive data that shouldn't be in code.",
    },
    {
      name: "Safety",
      category: "SCA",
      type: "sca",
      description: "Python dependency vulnerability checking",
      icon: "📦",
      what: "Checks your Python dependencies against known vulnerability databases to find insecure package versions.",
    },
    {
      name: "Trivy",
      category: "Container",
      type: "container",
      description: "Container and artifact vulnerability scanning",
      icon: "🐳",
      what: "Scans Docker images, filesystems, and git repos for vulnerabilities in OS packages and application dependencies.",
    },
    {
      name: "OWASP ZAP",
      category: "DAST",
      type: "dast",
      description: "Dynamic application security testing",
      icon: "⚡",
      what: "Tests running applications for vulnerabilities like XSS, SQL injection, and authentication flaws by sending actual requests.",
    },
    {
      name: "Nuclei",
      category: "DAST",
      type: "dast",
      description: "Fast template-based vulnerability scanning",
      icon: "🎯",
      what: "Runs thousands of vulnerability checks against web applications using community-maintained templates.",
    },
    {
      name: "Checkov",
      category: "IaC",
      type: "iac",
      description: "Infrastructure as Code security scanning",
      icon: "☁️",
      what: "Scans Terraform, CloudFormation, Kubernetes, and ARM templates for security misconfigurations before deployment.",
    },
    {
      name: "Lynis",
      category: "IaC",
      type: "iac",
      description: "Linux/Unix system security auditing",
      icon: "🖥️",
      what: "Audits system hardening, compliance, and security configuration of Linux/Unix servers and containers.",
    },
  ];

  // Filter scanners based on active tab
  const filteredScanners =
    activeTab === "all"
      ? scanners
      : scanners.filter((s) => s.type === activeTab);

  // Platform highlights - Real features, not fake testimonials
  const platformHighlights = [
    {
      title: "Enterprise Security",
      category: "Core Feature",
      highlight: "EG",
      description:
        "Multi-layer security scanning with SAST, DAST, SCA, and container security built-in. Comprehensive protection for your entire codebase.",
    },
    {
      title: "Compliance Ready",
      category: "Compliance",
      highlight: "CR",
      description:
        "Built-in compliance frameworks including SOC2, HIPAA, PCI-DSS, and GDPR. Automated compliance checking and reporting.",
    },
    {
      title: "Developer Friendly",
      category: "Integration",
      highlight: "DF",
      description:
        "Seamless integration with GitHub, GitLab, and CI/CD pipelines. Fast scans that don't slow down your development workflow.",
    },
  ];

  // Keep testimonials for backward compatibility but mark as example
  const testimonials = platformHighlights;

  const pricingPlans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for individual developers and small projects",
      features: [
        "Unlimited public repositories",
        "Basic vulnerability scanning",
        "5 security scanners",
        "Community support",
        "GitHub integration",
      ],
      cta: "Get Started Free",
      popular: false,
      gradient: "from-gray-600 to-gray-700",
    },
    {
      name: "Pro",
      price: "$29",
      period: "per month",
      description: "For teams that need comprehensive security",
      features: [
        "Unlimited repositories",
        "All 10 security scanners",
        "AI-powered analysis (GPT-4 + Gemini)",
        "Priority email support",
        "GitHub, GitLab, Bitbucket",
        "9 compliance frameworks",
        "Team collaboration",
        "Webhook integrations",
      ],
      cta: "Start Free Trial",
      popular: true,
      gradient: "from-cyan-500 to-violet-600",
    },
    {
      name: "Enterprise",
      price: "Contact",
      period: "us",
      description: "For organizations with custom requirements",
      features: [
        "Everything in Pro",
        "Self-hosted deployment option",
        "Custom scanner configurations",
        "Dedicated support",
        "Custom integrations",
        "SLA guarantee",
        "Training & onboarding",
        "Volume discounts",
      ],
      cta: "Contact Sales",
      popular: false,
      gradient: "from-violet-600 to-purple-700",
    },
  ];

  // Actual 9 compliance frameworks supported by backend
  const complianceFrameworks = [
    {
      name: "OWASP Top 10",
      icon: "🛡️",
      what: "Web application security risks",
    },
    { name: "NIST 800-53", icon: "🏛️", what: "Federal security controls" },
    { name: "ISO 27001", icon: "📋", what: "Information security standard" },
    { name: "PCI-DSS", icon: "💳", what: "Payment card security" },
    { name: "HIPAA", icon: "🏥", what: "Healthcare data protection" },
    { name: "SOC 2", icon: "🔒", what: "Service organization controls" },
    { name: "GDPR", icon: "🇪🇺", what: "EU data privacy regulation" },
    { name: "CIS Controls", icon: "🔐", what: "Critical security controls" },
    { name: "MITRE ATT&CK", icon: "⚔️", what: "Adversary tactics framework" },
  ];

  // Fix suggestion data for modal
  const fixSuggestions = {
    sql: {
      title: "SQL Injection Fix",
      severity: "Critical",
      problem:
        "User input directly interpolated into SQL query allows attackers to execute arbitrary SQL commands.",
      fix: `// ❌ Vulnerable Code
const query = \`SELECT * FROM users WHERE id = \${userId}\`;

// ✅ Fixed Code - Use Parameterized Queries
const query = "SELECT * FROM users WHERE id = ?";
db.execute(query, [userId]);`,
      explanation:
        "Use parameterized queries or prepared statements to prevent SQL injection. Never concatenate user input directly into SQL queries.",
    },
    secret: {
      title: "Hardcoded Secret Fix",
      severity: "High",
      problem:
        "API key exposed in source code can be extracted by attackers from version control or compiled code.",
      fix: `// ❌ Vulnerable Code
const API_KEY = "sk_live_abc123xyz";

// ✅ Fixed Code - Use Environment Variables
const API_KEY = process.env.API_KEY;

// Or use a secrets manager
const API_KEY = await secretsManager.getSecret("api-key");`,
      explanation:
        "Store secrets in environment variables or a secrets manager. Never commit API keys, passwords, or tokens to version control.",
    },
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-x-hidden">
      {/* Fix Suggestion Modal */}
      {showFixModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={() => setShowFixModal(null)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-xl ${
                      showFixModal === "sql"
                        ? "bg-red-500/20"
                        : "bg-amber-500/20"
                    }`}
                  >
                    {showFixModal === "sql" ? (
                      <ExclamationTriangleIcon className="w-6 h-6 text-red-400" />
                    ) : (
                      <LockClosedIcon className="w-6 h-6 text-amber-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {fixSuggestions[showFixModal].title}
                    </h3>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        showFixModal === "sql"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-amber-500/20 text-amber-400"
                      }`}
                    >
                      {fixSuggestions[showFixModal].severity}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setShowFixModal(null)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-5 h-5 text-gray-400" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Problem
                </h4>
                <p className="text-gray-300">
                  {fixSuggestions[showFixModal].problem}
                </p>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Fix
                </h4>
                <pre className="bg-gray-950 border border-gray-800 rounded-xl p-4 overflow-x-auto">
                  <code className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                    {fixSuggestions[showFixModal].fix}
                  </code>
                </pre>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Explanation
                </h4>
                <p className="text-gray-300">
                  {fixSuggestions[showFixModal].explanation}
                </p>
              </div>
            </div>
            <div className="p-6 border-t border-gray-800 flex justify-end gap-3">
              <button
                onClick={() => setShowFixModal(null)}
                className="px-4 py-2 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
              >
                Close
              </button>
              <button
                onClick={() => {
                  navigate("/register");
                  setShowFixModal(null);
                }}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
              >
                Start Free Trial
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Gradient orbs */}
        <div
          className="absolute w-[800px] h-[800px] rounded-full opacity-20 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, rgba(34,211,238,0.4) 0%, transparent 70%)",
            left: `${-200 + mousePosition.x * 0.02}px`,
            top: `${-200 + mousePosition.y * 0.02}px`,
            transform: `translateY(${scrollY * 0.2}px)`,
          }}
        />
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-20 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, rgba(139,92,246,0.4) 0%, transparent 70%)",
            right: `${-100 - mousePosition.x * 0.01}px`,
            top: `${200 + mousePosition.y * 0.01}px`,
            transform: `translateY(${scrollY * -0.1}px)`,
          }}
        />
        <div
          className="absolute w-[500px] h-[500px] rounded-full opacity-15 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, rgba(168,85,247,0.4) 0%, transparent 70%)",
            left: "40%",
            bottom: "-200px",
            transform: `translateY(${scrollY * -0.15}px)`,
          }}
        />

        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: "100px 100px",
            transform: `translateY(${scrollY * 0.1}px)`,
          }}
        />
      </div>

      {/* Navigation */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrollY > 50
            ? "bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50 shadow-2xl"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                <OnyxLogo variant="glow" className="w-10 h-10 relative" />
              </div>
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                  ONYX
                </span>
                <span className="hidden sm:block text-[10px] text-gray-500 uppercase tracking-[0.2em] -mt-1">
                  Security Intelligence
                </span>
              </div>
            </Link>

            {/* Nav Links */}
            <div className="hidden md:flex items-center space-x-8">
              {[
                { name: "Features", id: "features" },
                { name: "Scanners", id: "scanners" },
                { name: "Pricing", id: "pricing" },
                { name: "Why ONYX", id: "why-onyx" },
              ].map((item) => (
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

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsNavOpen(!isNavOpen)}
              className="md:hidden p-2 text-gray-400 hover:text-white"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
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

            {/* CTA Buttons */}
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

          {/* Mobile Menu */}
          {isNavOpen && (
            <div className="md:hidden mt-4 pb-4 border-t border-gray-800/50 pt-4">
              <div className="flex flex-col space-y-3">
                {[
                  { name: "Features", id: "features" },
                  { name: "Scanners", id: "scanners" },
                  { name: "Pricing", id: "pricing" },
                  { name: "Why ONYX", id: "why-onyx" },
                ].map((item) => (
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
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center pt-20"
      >
        <FloatingParticles />
        <div className="max-w-7xl mx-auto px-6 py-20">
          <div className="text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20 mb-8 animate-pulse">
              <SparklesIcon className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-gray-300">
                AI-Powered Security Intelligence Platform
              </span>
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
            </div>

            {/* Main Heading with typing animation */}
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black mb-6 leading-tight">
              <span className="block text-white mb-2">Stop</span>
              <span className="block bg-gradient-to-r from-cyan-400 via-violet-400 to-purple-400 bg-clip-text text-transparent min-h-[1.2em]">
                <TypeWriter words={heroWords} />
              </span>
              <span className="block text-white mt-2">Before They Start</span>
            </h1>

            {/* Subheading */}
            <p className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed">
              AI-powered security platform that scans, analyzes, and protects
              your codebase with 10 specialized scanners.
              <span className="text-cyan-400 font-medium">
                {" "}
                Find vulnerabilities before they ship.
              </span>
            </p>

            {/* Trust Badges */}
            <div className="flex items-center justify-center gap-6 mb-10 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <CheckBadgeIcon className="w-5 h-5 text-green-500" />
                <span>10 Security Scanners</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckBadgeIcon className="w-5 h-5 text-green-500" />
                <span>9 Compliance Frameworks</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckBadgeIcon className="w-5 h-5 text-green-500" />
                <span>Dual AI Analysis</span>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <button
                onClick={() => navigate("/register")}
                className="group relative px-8 py-4 rounded-2xl font-bold text-lg overflow-hidden w-full sm:w-auto"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600" />
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(255,255,255,0.3),transparent_70%)]" />
                <span className="relative text-white flex items-center justify-center gap-3">
                  Start Free Trial
                  <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </button>
              <button
                onClick={() => scrollToSection("features")}
                className="group px-8 py-4 rounded-2xl font-bold text-lg border border-gray-700 hover:border-gray-600 bg-gray-900/50 hover:bg-gray-800/50 transition-all w-full sm:w-auto"
              >
                <span className="flex items-center justify-center gap-3 text-gray-300 group-hover:text-white">
                  <PlayIcon className="w-5 h-5" />
                  See It In Action
                </span>
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {securityMetrics.map((stat, index) => (
                <div
                  key={index}
                  className="relative group p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-cyan-500/30 transition-all hover:transform hover:-translate-y-1"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-violet-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 mb-3">
                    <stat.icon className="w-5 h-5 text-cyan-400" />
                  </div>
                  <div className="text-3xl md:text-4xl font-black text-white mb-1">
                    {counters[Object.keys(counters)[index]] > 0 ? (
                      <AnimatedCounter
                        end={counters[Object.keys(counters)[index]]}
                        suffix={stat.label.includes("Uptime") ? "%" : "+"}
                      />
                    ) : (
                      <span className="text-gray-600">--</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
          <span className="text-xs text-gray-500 uppercase tracking-widest">
            Explore
          </span>
          <div className="w-6 h-10 rounded-full border-2 border-gray-700 flex items-start justify-center p-2">
            <ArrowDownIcon className="w-3 h-3 text-cyan-400 animate-bounce" />
          </div>
        </div>
      </section>

      {/* Security Standards Section */}
      <section className="py-16 border-b border-gray-800/50 bg-gray-900/20">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-gray-500 text-sm uppercase tracking-widest mb-10">
            Compliance Frameworks We Support
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
            {[
              { name: "OWASP Top 10", icon: "🛡️", desc: "Mapping" },
              { name: "NIST 800-53", icon: "🏛️", desc: "Controls" },
              { name: "ISO 27001", icon: "📋", desc: "Framework" },
              { name: "PCI-DSS", icon: "💳", desc: "Checks" },
              { name: "HIPAA", icon: "🏥", desc: "Rules" },
              { name: "SOC 2", icon: "🔒", desc: "Controls" },
            ].map((standard, i) => (
              <div
                key={i}
                className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:border-cyan-500/30 hover:bg-gray-800/50 transition-all group cursor-default"
              >
                <span className="text-3xl group-hover:scale-110 transition-transform">
                  {standard.icon}
                </span>
                <span className="text-sm font-semibold text-white tracking-wide">
                  {standard.name}
                </span>
                <span className="text-xs text-cyan-400 font-medium">
                  {standard.desc}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - New Section */}
      <section className="py-24 border-b border-gray-800/50 bg-gray-900/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
              <RocketLaunchIcon className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400">Quick Setup</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Secure in <span className="text-cyan-400">Minutes</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              From zero to protected in just a few simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                step: 1,
                title: "Connect",
                desc: "Link your repository",
                icon: CodeBracketIcon,
              },
              {
                step: 2,
                title: "Scan",
                desc: "AI analyzes your code",
                icon: CpuChipIcon,
              },
              {
                step: 3,
                title: "Fix",
                desc: "Get remediation steps",
                icon: BoltIcon,
              },
              {
                step: 4,
                title: "Protect",
                desc: "Continuous monitoring",
                icon: ShieldCheckIcon,
              },
            ].map((item, i) => (
              <div key={i} className="relative group">
                {i < 3 && (
                  <div className="hidden md:block absolute top-12 left-full w-full h-0.5 bg-gradient-to-r from-cyan-500/50 to-transparent z-0" />
                )}
                <div className="relative bg-gray-900/50 rounded-2xl p-6 border border-gray-800/50 hover:border-cyan-500/30 transition-all group-hover:transform group-hover:-translate-y-2">
                  <div className="absolute -top-4 -left-4 w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm">
                    {item.step}
                  </div>
                  <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 w-fit mb-4">
                    <item.icon className="w-6 h-6 text-cyan-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-gray-400 text-sm">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-20">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
              <CubeTransparentIcon className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-cyan-400">Core Capabilities</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Next-Generation{" "}
              <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                Security
              </span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Powered by GPT-4 and Gemini AI with 10 security scanners.
              <span className="text-white"> Find vulnerabilities fast.</span>
            </p>
          </div>

          {/* Live Code Demo */}
          <div className="mb-20 relative">
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-cyan-500/10 rounded-3xl blur-3xl" />
            <div className="relative bg-gray-900/80 backdrop-blur-xl rounded-3xl border border-gray-800/50 overflow-hidden">
              {/* Code Editor Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800/50 bg-gray-900/50">
                <div className="flex items-center gap-3">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <span className="text-gray-500 text-sm ml-2">
                    auth_controller.py
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/30">
                    <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    <span className="text-xs text-cyan-400">AI Scanning</span>
                  </div>
                </div>
              </div>

              {/* Code Content */}
              <div className="p-6 font-mono text-sm">
                <div className="flex">
                  <div className="text-gray-600 select-none pr-6 text-right w-12">
                    1<br />2<br />3<br />4<br />5<br />6<br />7<br />8<br />9
                    <br />
                    10
                    <br />
                    11
                  </div>
                  <div className="flex-1 overflow-x-auto">
                    <pre className="text-gray-300">
                      <span className="text-violet-400">def</span>{" "}
                      <span className="text-cyan-400">authenticate_user</span>
                      (username, password):{"\n"}
                      <span className="text-gray-500">
                        {" "}
                        # SQL Query - VULNERABILITY DETECTED!
                      </span>
                      {"\n"}
                      <span className="relative">
                        <span className="absolute -left-4 top-0 w-1 h-full bg-red-500 rounded animate-pulse" />
                        <span className="bg-red-500/20 px-1 rounded text-red-300">
                          {" "}
                          query = f"SELECT * FROM users WHERE name='{"{"}
                          username{"}"}'"{"\n"}
                        </span>
                      </span>
                      <span className="text-gray-500">
                        {" "}
                        # Hardcoded secret - CRITICAL!
                      </span>
                      {"\n"}
                      <span className="relative">
                        <span className="absolute -left-4 top-0 w-1 h-full bg-amber-500 rounded animate-pulse" />
                        <span className="bg-amber-500/20 px-1 rounded text-amber-300">
                          {" "}
                          api_key = "sk-prod-12345-secret-key"{"\n"}
                        </span>
                      </span>
                      <span className="text-violet-400"> return</span>{" "}
                      db.execute(query)
                    </pre>
                  </div>
                </div>

                {/* AI Detection Panel */}
                <div className="mt-6 pt-6 border-t border-gray-800/50">
                  <div className="flex items-center gap-2 mb-4">
                    <CpuChipIcon className="w-5 h-5 text-cyan-400" />
                    <span className="text-white font-semibold">
                      AI Detection Results
                    </span>
                    <span className="ml-auto text-xs text-gray-500">
                      Scan completed in 0.8s
                    </span>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                      <div className="flex items-center gap-2 mb-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
                        <span className="font-semibold text-red-400">
                          SQL Injection
                        </span>
                        <span className="ml-auto text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded-full">
                          Critical
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">
                        Line 3: User input directly interpolated into SQL query
                      </p>
                      <button
                        onClick={() => setShowFixModal("sql")}
                        className="mt-3 text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                      >
                        View fix suggestion{" "}
                        <ArrowRightIcon className="w-3 h-3" />
                      </button>
                    </div>
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
                      <div className="flex items-center gap-2 mb-2">
                        <LockClosedIcon className="w-5 h-5 text-amber-400" />
                        <span className="font-semibold text-amber-400">
                          Hardcoded Secret
                        </span>
                        <span className="ml-auto text-xs px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full">
                          High
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm">
                        Line 5: API key exposed in source code
                      </p>
                      <button
                        onClick={() => setShowFixModal("secret")}
                        className="mt-3 text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                      >
                        View fix suggestion{" "}
                        <ArrowRightIcon className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Feature Cards */}
            <div className="space-y-4">
              {features.map((feature, index) => (
                <div
                  key={index}
                  onClick={() => setActiveFeature(index)}
                  className={`relative group p-6 rounded-2xl cursor-pointer transition-all duration-300 ${
                    activeFeature === index
                      ? "bg-gradient-to-r from-gray-800/80 to-gray-900/80 border border-gray-700/50 shadow-xl"
                      : "bg-gray-900/30 border border-gray-800/30 hover:bg-gray-900/50"
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`p-3 rounded-xl bg-gradient-to-br ${feature.gradient} bg-opacity-20`}
                    >
                      <feature.icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {feature.title}
                        </h3>
                        <span
                          className={`text-xs px-2 py-1 rounded-full bg-gradient-to-r ${feature.gradient} bg-opacity-20 text-white`}
                        >
                          {feature.stats}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>

                  {/* Active indicator */}
                  {activeFeature === index && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gradient-to-b from-cyan-400 to-violet-500 rounded-r-full" />
                  )}
                </div>
              ))}
            </div>

            {/* Feature Detail Panel */}
            <div className="lg:sticky lg:top-32 h-fit">
              <div className="relative p-8 rounded-3xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 overflow-hidden min-h-[500px]">
                {/* Background gradient */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${features[activeFeature].gradient} opacity-5`}
                />

                {/* Content */}
                <div className="relative">
                  <div
                    className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${features[activeFeature].gradient} mb-6`}
                  >
                    {React.createElement(features[activeFeature].icon, {
                      className: "w-8 h-8 text-white",
                    })}
                  </div>

                  <h3 className="text-2xl font-bold text-white mb-4">
                    {features[activeFeature].title}
                  </h3>
                  <p className="text-gray-400 mb-6 leading-relaxed text-lg">
                    {features[activeFeature].description}
                  </p>

                  {/* Stats highlight */}
                  <div className="mb-6 p-4 rounded-xl bg-gray-800/50 border border-gray-700/30">
                    <div className="flex items-center gap-3">
                      <div
                        className={`text-3xl font-black bg-gradient-to-r ${features[activeFeature].gradient} bg-clip-text text-transparent`}
                      >
                        {features[activeFeature].stats}
                      </div>
                      <div className="text-sm text-gray-400">
                        Performance Metric
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 mb-8">
                    {features[activeFeature].details.map((detail, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
                      >
                        <CheckCircleIcon className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                        <span className="text-gray-300">{detail}</span>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={() => navigate("/register")}
                    className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all flex items-center justify-center gap-2"
                  >
                    Get Started
                    <ArrowRightIcon className="w-4 h-4" />
                  </button>
                </div>

                {/* Decorative elements */}
                <div className="absolute top-4 right-4 text-8xl font-black text-white/5">
                  {String(activeFeature + 1).padStart(2, "0")}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Scanners Section */}
      <section
        id="scanners"
        className="py-32 bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950"
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
              <CommandLineIcon className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-violet-400">Security Arsenal</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              <span className="text-violet-400">10</span> Security Scanners
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Open-source security tools integrated into one unified platform
            </p>
          </div>

          {/* Scanner Category Tabs */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {[
              { id: "all", label: "All Tools", count: 10 },
              { id: "sast", label: "SAST", count: 3 },
              { id: "secrets", label: "Secrets", count: 1 },
              { id: "sca", label: "SCA", count: 1 },
              { id: "dast", label: "DAST", count: 2 },
              { id: "container", label: "Container", count: 1 },
              { id: "iac", label: "IaC", count: 2 },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  activeTab === tab.id
                    ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                    : "bg-gray-800/50 text-gray-400 border border-gray-700/50 hover:bg-gray-800 hover:text-white"
                }`}
              >
                {tab.label}{" "}
                <span className="ml-1 text-xs opacity-60">({tab.count})</span>
              </button>
            ))}
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredScanners.map((scanner, index) => (
              <div
                key={index}
                className="group p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-violet-500/30 hover:bg-gray-800/50 transition-all hover:transform hover:-translate-y-1"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center text-3xl">
                    {scanner.icon}
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-lg">
                      {scanner.name}
                    </h4>
                    <span className="text-xs text-violet-400 font-medium px-2 py-0.5 bg-violet-500/10 rounded-full">
                      {scanner.category}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-300 font-medium mb-2">
                  {scanner.description}
                </p>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {scanner.what}
                </p>
              </div>
            ))}
          </div>

          {/* More scanners indicator */}
          {activeTab === "all" && (
            <div className="text-center mt-8">
              <span className="text-gray-500 text-sm">
                Showing all {filteredScanners.length} security scanners
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Integrations Section */}
      <section className="py-24 bg-gray-900/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6">
              <ServerStackIcon className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-400">
                Git Platform Integration
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Connect Your <span className="text-blue-400">Repositories</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Direct integration with major Git platforms. Connect your repos
              and start scanning.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              {
                name: "GitHub",
                icon: "🐙",
                category: "Git Platform",
                desc: "Connect public or private repos via GitHub API. OAuth authentication supported.",
              },
              {
                name: "GitLab",
                icon: "🦊",
                category: "Git Platform",
                desc: "Integrate with GitLab.com or self-hosted instances. Full repository access.",
              },
              {
                name: "Bitbucket",
                icon: "🪣",
                category: "Git Platform",
                desc: "Support for Bitbucket Cloud repositories. Team and personal accounts.",
              },
            ].map((integration, i) => (
              <div
                key={i}
                className="group p-6 rounded-2xl bg-gray-800/30 border border-gray-800/50 hover:border-blue-500/30 hover:bg-gray-800/50 transition-all text-center"
              >
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">
                  {integration.icon}
                </div>
                <div className="font-bold text-white text-lg mb-1">
                  {integration.name}
                </div>
                <div className="text-xs text-blue-400 font-medium mb-3">
                  {integration.category}
                </div>
                <p className="text-sm text-gray-400">{integration.desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-12 p-6 rounded-2xl bg-gray-800/20 border border-gray-700/30 max-w-2xl mx-auto">
            <h4 className="text-lg font-semibold text-white mb-2">
              Additional Capabilities
            </h4>
            <div className="flex flex-wrap justify-center gap-3">
              {[
                { name: "Webhooks", desc: "CI/CD triggers" },
                { name: "REST API", desc: "Custom integration" },
                { name: "Email Alerts", desc: "Notifications" },
              ].map((cap, i) => (
                <div
                  key={i}
                  className="px-4 py-2 rounded-lg bg-gray-800/50 border border-gray-700/30"
                >
                  <span className="text-white font-medium text-sm">
                    {cap.name}
                  </span>
                  <span className="text-gray-500 text-xs ml-2">{cap.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section className="py-24 border-y border-gray-800/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h3 className="text-2xl font-bold text-white mb-4">
              Automated Compliance
            </h3>
            <p className="text-gray-400">
              Meet regulatory requirements with automated checks and reports
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6">
            {complianceFrameworks.map((framework, index) => (
              <div
                key={index}
                className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all"
              >
                <span className="text-2xl group-hover:scale-125 transition-transform">
                  {framework.icon}
                </span>
                <span className="font-medium text-gray-300 group-hover:text-white transition-colors">
                  {framework.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why ONYX Section */}
      <section id="why-onyx" className="py-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-gray-950 via-gray-900/50 to-gray-950" />
        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-6">
              <StarIcon className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-amber-400">Why Choose ONYX</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Built for <span className="text-cyan-400">Modern</span> Security
              Teams
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Everything you need to secure your code, all in one platform
            </p>
          </div>

          {/* Feature Highlight Cards */}
          <div className="grid md:grid-cols-3 gap-8">
            {platformHighlights.map((highlight, index) => (
              <div
                key={index}
                className={`relative p-8 rounded-3xl transition-all duration-500 cursor-pointer ${
                  currentTestimonial === index
                    ? "bg-gradient-to-br from-gray-800/80 to-gray-900/80 border border-cyan-500/30 scale-105 shadow-2xl shadow-cyan-500/10"
                    : "bg-gray-900/30 border border-gray-800/30 hover:border-gray-700/50 hover:bg-gray-900/50"
                }`}
                onClick={() => setCurrentTestimonial(index)}
              >
                {/* Icon */}
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold mb-6">
                  {highlight.highlight}
                </div>

                {/* Category Badge */}
                <span className="inline-block px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-xs font-medium mb-4">
                  {highlight.category}
                </span>

                {/* Title */}
                <h3 className="text-xl font-bold text-white mb-3">
                  {highlight.title}
                </h3>

                {/* Description */}
                <p className="text-gray-400 leading-relaxed">
                  {highlight.description}
                </p>

                {/* Active indicator */}
                {currentTestimonial === index && (
                  <div className="absolute top-4 right-4 w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
                )}
              </div>
            ))}
          </div>

          {/* Indicator dots */}
          <div className="flex justify-center gap-2 mt-8">
            {platformHighlights.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentTestimonial(index)}
                className={`w-2 h-2 rounded-full transition-all ${
                  currentTestimonial === index
                    ? "w-8 bg-cyan-400"
                    : "bg-gray-700 hover:bg-gray-600"
                }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section
        id="pricing"
        className="py-32 bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950"
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
              <SparklesIcon className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400">Pricing</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Start free, scale as you grow. No hidden fees, no surprises.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <div
                key={index}
                className={`relative p-8 rounded-3xl transition-all ${
                  plan.popular
                    ? "bg-gradient-to-br from-gray-800/80 to-gray-900/80 border-2 border-cyan-500/50 scale-105 shadow-2xl shadow-cyan-500/20"
                    : "bg-gray-900/30 border border-gray-800/50 hover:border-gray-700/50"
                }`}
              >
                {/* Popular badge */}
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <div className="px-4 py-1 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500 text-white text-sm font-semibold">
                      Most Popular
                    </div>
                  </div>
                )}

                <div className="text-center mb-8">
                  <h3 className="text-xl font-bold text-white mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline justify-center gap-2 mb-2">
                    <span className="text-4xl font-black text-white">
                      {plan.price}
                    </span>
                    <span className="text-gray-500">/{plan.period}</span>
                  </div>
                  <p className="text-sm text-gray-400">{plan.description}</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <CheckCircleIcon className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                      <span className="text-gray-300 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => navigate("/register")}
                  className={`w-full py-3 rounded-xl font-semibold transition-all ${
                    plan.popular
                      ? "bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:shadow-lg hover:shadow-cyan-500/25"
                      : "bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-purple-500/10" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.1),transparent_70%)]" />

        <div className="max-w-4xl mx-auto px-6 text-center relative">
          <OnyxLogo variant="glow" className="w-20 h-20 mx-auto mb-8" />
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Secure Your Code?
          </h2>
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Start scanning your repositories with AI-powered security analysis.
            Get started for free — no credit card required.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <button
              onClick={() => navigate("/register")}
              className="group relative px-10 py-5 rounded-2xl font-bold text-lg overflow-hidden shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-shadow"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600" />
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,rgba(255,255,255,0.3),transparent_70%)]" />
              <span className="relative text-white flex items-center gap-3">
                Start Free Trial
                <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
            <button
              onClick={() => navigate("/login")}
              className="px-10 py-5 rounded-2xl font-bold text-lg border border-gray-700 hover:border-cyan-500/50 text-gray-300 hover:text-white transition-all"
            >
              Sign In
            </button>
          </div>

          {/* Trust indicators */}
          <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <LockClosedIcon className="w-4 h-4 text-green-500" />
              <span>Secure API</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheckIcon className="w-4 h-4 text-green-500" />
              <span>10 Scanners</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckBadgeIcon className="w-4 h-4 text-green-500" />
              <span>Open Source</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 border-t border-gray-800/50 bg-gray-950">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-5 gap-12 mb-12">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-xl blur opacity-50" />
                  <OnyxLogo className="w-10 h-10 relative" />
                </div>
                <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
                  ONYX
                </span>
              </div>
              <p className="text-gray-500 text-sm leading-relaxed mb-6 max-w-sm">
                Open-source AI-powered security scanning platform for modern
                development teams. Detect vulnerabilities before they become
                threats.
              </p>
              <div className="flex items-center gap-4">
                {[
                  { icon: "𝕏", href: "https://twitter.com", label: "Twitter" },
                  {
                    icon: "⬢",
                    href: "https://github.com/Sagar4173/ONYX",
                    label: "GitHub",
                  },
                  {
                    icon: "in",
                    href: "https://linkedin.com",
                    label: "LinkedIn",
                  },
                  { icon: "◈", href: "https://discord.com", label: "Discord" },
                ].map((social, i) => (
                  <a
                    key={i}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    title={social.label}
                    className="w-10 h-10 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 flex items-center justify-center text-gray-500 hover:text-white transition-all"
                  >
                    <span className="text-sm font-medium">{social.icon}</span>
                  </a>
                ))}
              </div>
            </div>

            {/* Links */}
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-3">
                {[
                  {
                    name: "Features",
                    action: () => scrollToSection("features"),
                  },
                  {
                    name: "Scanners",
                    action: () => scrollToSection("scanners"),
                  },
                  { name: "Pricing", action: () => scrollToSection("pricing") },
                  {
                    name: "Why ONYX",
                    action: () => scrollToSection("why-onyx"),
                  },
                  { name: "Get Started", action: () => navigate("/register") },
                ].map((link, i) => (
                  <li key={i}>
                    <button
                      onClick={link.action}
                      className="text-gray-500 hover:text-gray-300 text-sm transition-colors text-left"
                    >
                      {link.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-3">
                {[
                  { name: "Documentation", href: "/docs" },
                  { name: "API Reference", href: "/docs" },
                  { name: "GitHub", href: "https://github.com/Sagar4173/ONYX" },
                  { name: "Support", href: "mailto:support@onyx-security.io" },
                  { name: "Contact", href: "mailto:hello@onyx-security.io" },
                ].map((link, i) => (
                  <li key={i}>
                    <a
                      href={link.href}
                      target={
                        link.href.startsWith("http") ? "_blank" : undefined
                      }
                      rel={
                        link.href.startsWith("http")
                          ? "noopener noreferrer"
                          : undefined
                      }
                      className="text-gray-500 hover:text-gray-300 text-sm transition-colors"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-3">
                {[
                  { name: "About", action: () => navigate("/about") },
                  { name: "Data Policy", action: () => navigate("/legal") },
                  { name: "Terms", action: () => navigate("/terms") },
                  { name: "Login", action: () => navigate("/login") },
                  { name: "Register", action: () => navigate("/register") },
                ].map((link, i) => (
                  <li key={i}>
                    <button
                      onClick={link.action}
                      className="text-gray-500 hover:text-gray-300 text-sm transition-colors text-left"
                    >
                      {link.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Bottom */}
          <div className="pt-8 border-t border-gray-800/50 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-gray-500 text-sm">
              © {new Date().getFullYear()} ONYX Security Intelligence. All
              rights reserved.
            </p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <button
                onClick={() => navigate("/legal")}
                className="hover:text-gray-300 transition-colors"
              >
                Data Policy
              </button>
              <button
                onClick={() => navigate("/terms")}
                className="hover:text-gray-300 transition-colors"
              >
                Terms of Service
              </button>
              <button
                onClick={() => navigate("/register")}
                className="hover:text-gray-300 transition-colors"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
