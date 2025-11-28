/**
 * LandingPage Component - Public-facing marketing page
 * Modern design showcasing platform features and benefits
 */
import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  ShieldCheckIcon,
  SparklesIcon,
  BoltIcon,
  ChartBarIcon,
  CodeBracketIcon,
  LockClosedIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  PlayCircleIcon,
  UserGroupIcon,
  GlobeAltIcon,
  ClockIcon,
  DocumentTextIcon,
  CpuChipIcon,
  BeakerIcon,
  RocketLaunchIcon,
  ShieldExclamationIcon,
  ArchiveBoxIcon,
  BuildingOfficeIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowUpIcon,
} from "@heroicons/react/24/outline";
import {
  ShieldCheckIcon as ShieldCheckSolid,
  SparklesIcon as SparklesSolid,
  BoltIcon as BoltSolid,
} from "@heroicons/react/24/solid";

const LandingPage = () => {
  const navigate = useNavigate();
  const [activeFeature, setActiveFeature] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [activeScannerDemo, setActiveScannerDemo] = useState(0);
  const [vulnerabilityCount, setVulnerabilityCount] = useState(0);
  const [scanCount, setScanCount] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showBackToTop, setShowBackToTop] = useState(false);

  // Smooth scroll function
  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      setMobileMenuOpen(false);
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
      setShowBackToTop(window.scrollY > 500);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Auto-rotate features
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % 6);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Animate counters
  useEffect(() => {
    const duration = 2000;
    const steps = 50;
    const increment = duration / steps;

    let vulnStep = 0;
    let scanStep = 0;

    const vulnInterval = setInterval(() => {
      vulnStep++;
      setVulnerabilityCount(Math.floor((vulnStep / steps) * 45000));
      if (vulnStep >= steps) clearInterval(vulnInterval);
    }, increment);

    const scanInterval = setInterval(() => {
      scanStep++;
      setScanCount(Math.floor((scanStep / steps) * 12000));
      if (scanStep >= steps) clearInterval(scanInterval);
    }, increment);

    return () => {
      clearInterval(vulnInterval);
      clearInterval(scanInterval);
    };
  }, []);

  // Auto-rotate scanner demo
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveScannerDemo((prev) => (prev + 1) % 6);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const features = [
    {
      icon: ShieldCheckIcon,
      title: "6 Security Scanners",
      description:
        "Semgrep, Trivy, GitLeaks, Lynis, Safety, and Bandit integrated",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      icon: SparklesIcon,
      title: "AI-Powered Analysis",
      description: "GPT-4 intelligence for smart vulnerability assessment",
      gradient: "from-purple-500 to-pink-500",
    },
    {
      icon: BoltIcon,
      title: "Real-time Scanning",
      description: "Instant security insights with WebSocket updates",
      gradient: "from-orange-500 to-red-500",
    },
    {
      icon: ChartBarIcon,
      title: "Advanced Analytics",
      description: "Comprehensive dashboards and trend analysis",
      gradient: "from-green-500 to-emerald-500",
    },
    {
      icon: ClockIcon,
      title: "Audit Logging",
      description:
        "Complete audit trail for compliance and security monitoring",
      gradient: "from-indigo-500 to-purple-500",
    },
    {
      icon: BuildingOfficeIcon,
      title: "Multi-Framework Compliance",
      description: "SOX, HIPAA, ISO 27001, PCI DSS, GDPR, and more",
      gradient: "from-teal-500 to-cyan-500",
    },
  ];

  const scanners = [
    {
      name: "Semgrep",
      description: "Static Application Security Testing",
      languages: "20+ Languages",
      icon: CodeBracketIcon,
      color: "from-blue-500 to-indigo-500",
    },
    {
      name: "Trivy",
      description: "Container & Dependency Scanning",
      languages: "CVE Detection",
      icon: ArchiveBoxIcon,
      color: "from-purple-500 to-pink-500",
    },
    {
      name: "GitLeaks",
      description: "Secret Detection",
      languages: "Git History",
      icon: LockClosedIcon,
      color: "from-orange-500 to-red-500",
    },
    {
      name: "Lynis",
      description: "System Security Auditing",
      languages: "Infrastructure",
      icon: ShieldExclamationIcon,
      color: "from-green-500 to-emerald-500",
    },
    {
      name: "Safety",
      description: "Python Dependency Scanning",
      languages: "PyPI Packages",
      icon: BeakerIcon,
      color: "from-yellow-500 to-orange-500",
    },
    {
      name: "Bandit",
      description: "Python Security Analysis",
      languages: "AST-based",
      icon: CpuChipIcon,
      color: "from-cyan-500 to-blue-500",
    },
  ];

  const stats = [
    { label: "Security Scanners", value: "6+", icon: ShieldCheckIcon },
    { label: "Languages Supported", value: "20+", icon: CodeBracketIcon },
    { label: "Compliance Frameworks", value: "9", icon: DocumentTextIcon },
    { label: "AI Analysis", value: "GPT-4", icon: SparklesIcon },
  ];

  const benefits = [
    {
      icon: BoltIcon,
      title: "Lightning Fast",
      description:
        "Average scan completion in under 5 minutes with parallel processing",
    },
    {
      icon: SparklesIcon,
      title: "AI-Powered",
      description:
        "GPT-4 intelligence provides context-aware vulnerability analysis",
    },
    {
      icon: LockClosedIcon,
      title: "Enterprise Security",
      description:
        "Bank-grade encryption, RBAC, and comprehensive audit logging",
    },
    {
      icon: ChartBarIcon,
      title: "Actionable Insights",
      description:
        "Clear remediation steps with code examples and priority ranking",
    },
    {
      icon: CloudArrowUpIcon,
      title: "Cloud Native",
      description: "Scalable architecture with MongoDB and async processing",
    },
    {
      icon: UserGroupIcon,
      title: "Team Collaboration",
      description: "Project-based organization with role-based access control",
    },
  ];

  const useCases = [
    {
      title: "Development Teams",
      description: "Integrate security into your CI/CD pipeline",
      icon: CodeBracketIcon,
      features: ["Pre-commit scanning", "PR automation", "Developer feedback"],
    },
    {
      title: "Security Teams",
      description: "Centralized security monitoring and compliance",
      icon: ShieldCheckIcon,
      features: [
        "Vulnerability tracking",
        "Compliance reports",
        "Audit trails",
      ],
    },
    {
      title: "Enterprise",
      description: "Scale security across multiple projects",
      icon: BuildingOfficeIcon,
      features: ["Multi-tenant", "SSO integration", "Custom policies"],
    },
  ];

  const complianceFrameworks = [
    "SOX",
    "HIPAA",
    "ISO 27001",
    "PCI DSS",
    "GDPR",
    "SOC2",
    "NIST",
    "CIS",
    "OWASP",
  ];

  const testimonials = [
    {
      name: "Sarah Chen",
      role: "Head of Security, TechCorp",
      avatar: "👩‍💼",
      quote:
        "SecureDevOps AI reduced our vulnerability response time by 70%. The AI-powered insights are game-changing.",
      rating: 5,
    },
    {
      name: "Michael Rodriguez",
      role: "DevOps Lead, StartupXYZ",
      avatar: "👨‍💻",
      quote:
        "Best security platform we've used. The integration with our CI/CD pipeline was seamless and scanning is incredibly fast.",
      rating: 5,
    },
    {
      name: "Emily Watson",
      role: "CTO, FinanceApp",
      avatar: "👩‍💼",
      quote:
        "Compliance reporting alone saved us weeks of work. SOX and PCI DSS assessments are now automated.",
      rating: 5,
    },
  ];

  const pricingPlans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for individual developers",
      features: [
        "5 scans per month",
        "Basic vulnerability detection",
        "Community support",
        "Public repositories only",
        "Email notifications",
      ],
      cta: "Start Free",
      popular: false,
      gradient: "from-gray-600 to-gray-700",
    },
    {
      name: "Pro",
      price: "$49",
      period: "per user/month",
      description: "For professional development teams",
      features: [
        "Unlimited scans",
        "AI-powered analysis",
        "Private repositories",
        "Priority support",
        "Advanced analytics",
        "Slack & Teams integration",
        "Compliance reporting",
        "API access",
      ],
      cta: "Start Free Trial",
      popular: true,
      gradient: "from-blue-600 to-purple-600",
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "contact sales",
      description: "For large organizations",
      features: [
        "Everything in Pro",
        "Custom compliance frameworks",
        "Dedicated support",
        "SSO & LDAP",
        "On-premises deployment",
        "SLA guarantees",
        "Custom integrations",
        "Security training",
      ],
      cta: "Contact Sales",
      popular: false,
      gradient: "from-purple-600 to-pink-600",
    },
  ];

  const integrations = [
    { name: "GitHub", logo: "🐙", connected: true },
    { name: "GitLab", logo: "🦊", connected: true },
    { name: "Slack", logo: "💬", connected: true },
    { name: "Teams", logo: "👥", connected: true },
    { name: "JIRA", logo: "📋", connected: false },
    { name: "Jenkins", logo: "⚙️", connected: false },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrollY > 50
            ? "bg-gray-900/95 backdrop-blur-xl border-b border-white/10 shadow-2xl"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
                <ShieldCheckSolid className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                SecureDevOps AI
              </span>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:flex items-center gap-6">
              <button
                onClick={() => scrollToSection("features")}
                className="text-gray-300 hover:text-white transition-colors"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection("scanners")}
                className="text-gray-300 hover:text-white transition-colors"
              >
                Scanners
              </button>
              <button
                onClick={() => scrollToSection("testimonials")}
                className="text-gray-300 hover:text-white transition-colors"
              >
                Testimonials
              </button>
              <button
                onClick={() => scrollToSection("pricing")}
                className="text-gray-300 hover:text-white transition-colors"
              >
                Pricing
              </button>
              <button
                onClick={() => navigate("/login")}
                className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate("/register")}
                className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl text-white font-semibold transition-all shadow-lg hover:shadow-2xl"
              >
                Get Started
              </button>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-300 hover:text-white transition-colors"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-white/10 bg-gray-900/95 backdrop-blur-xl">
              <div className="flex flex-col gap-4">
                <button
                  onClick={() => scrollToSection("features")}
                  className="text-left text-gray-300 hover:text-white transition-colors px-4"
                >
                  Features
                </button>
                <button
                  onClick={() => scrollToSection("scanners")}
                  className="text-left text-gray-300 hover:text-white transition-colors px-4"
                >
                  Scanners
                </button>
                <button
                  onClick={() => scrollToSection("testimonials")}
                  className="text-left text-gray-300 hover:text-white transition-colors px-4"
                >
                  Testimonials
                </button>
                <button
                  onClick={() => scrollToSection("pricing")}
                  className="text-left text-gray-300 hover:text-white transition-colors px-4"
                >
                  Pricing
                </button>
                <button
                  onClick={() => {
                    navigate("/login");
                    setMobileMenuOpen(false);
                  }}
                  className="text-left text-gray-300 hover:text-white transition-colors px-4"
                >
                  Sign In
                </button>
                <button
                  onClick={() => {
                    navigate("/register");
                    setMobileMenuOpen(false);
                  }}
                  className="mx-4 px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white font-semibold"
                >
                  Get Started
                </button>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="relative max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-sm font-medium mb-8">
              <SparklesSolid className="w-4 h-4" />
              AI-Powered Security Platform
            </div>
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
              Secure Your Code with
              <span className="block bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto">
              Comprehensive security scanning powered by 6 industry-leading
              tools and GPT-4 AI analysis. Detect vulnerabilities, secrets, and
              compliance issues in real-time.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate("/register")}
                className="group px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl text-white font-semibold text-lg shadow-2xl transition-all flex items-center gap-2"
              >
                Start Free Scan
                <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => scrollToSection("video-demo")}
                className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-semibold text-lg transition-all flex items-center gap-2"
              >
                <PlayCircleIcon className="w-6 h-6" />
                Watch Demo
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center transform hover:scale-105 transition-transform"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <stat.icon className="w-8 h-8 text-blue-400 mx-auto mb-3" />
                <div className="text-3xl font-bold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Live Demo Stats */}
          <div className="mt-16 max-w-3xl mx-auto">
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-2xl p-8 backdrop-blur-xl">
              <div className="text-center mb-6">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/20 rounded-full text-green-400 text-sm font-medium mb-4">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  Live Platform Stats
                </div>
              </div>
              <div className="grid grid-cols-2 gap-8">
                <div className="text-center">
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                    {vulnerabilityCount.toLocaleString()}+
                  </div>
                  <div className="text-gray-400">Vulnerabilities Detected</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                    {scanCount.toLocaleString()}+
                  </div>
                  <div className="text-gray-400">Scans Completed</div>
                </div>
              </div>
            </div>
          </div>

          {/* Scroll Indicator */}
          <div className="mt-16 flex flex-col items-center">
            <p className="text-gray-400 text-sm mb-3">Scroll to explore</p>
            <div className="w-6 h-10 border-2 border-white/30 rounded-full flex items-start justify-center p-2 animate-bounce">
              <div className="w-1.5 h-3 bg-white/50 rounded-full" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Powerful Features
            </h2>
            <p className="text-xl text-gray-400">
              Everything you need for comprehensive security scanning
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`group bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all cursor-pointer ${
                  activeFeature === index ? "ring-2 ring-purple-500" : ""
                }`}
                onMouseEnter={() => setActiveFeature(index)}
              >
                <div
                  className={`p-4 bg-gradient-to-r ${feature.gradient} rounded-xl inline-block mb-4`}
                >
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Scanners Showcase */}
      <section id="scanners" className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              6 Security Scanners
            </h2>
            <p className="text-xl text-gray-400">
              Industry-leading tools integrated into one platform
            </p>
          </div>

          {/* Scanner Demo Tabs */}
          <div className="mb-8 overflow-x-auto">
            <div className="flex gap-2 justify-center min-w-max px-4">
              {scanners.map((scanner, index) => (
                <button
                  key={index}
                  onClick={() => setActiveScannerDemo(index)}
                  className={`px-6 py-3 rounded-xl font-medium transition-all ${
                    activeScannerDemo === index
                      ? `bg-gradient-to-r ${scanner.color} text-white shadow-lg`
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                  }`}
                >
                  {scanner.name}
                </button>
              ))}
            </div>
          </div>

          {/* Active Scanner Demo */}
          <div className="mb-12 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8">
            <div className="flex items-start gap-6">
              <div
                className={`p-4 bg-gradient-to-r ${scanners[activeScannerDemo].color} rounded-xl`}
              >
                {React.createElement(scanners[activeScannerDemo].icon, {
                  className: "w-10 h-10 text-white",
                })}
              </div>
              <div className="flex-1">
                <h3 className="text-3xl font-bold text-white mb-3">
                  {scanners[activeScannerDemo].name}
                </h3>
                <p className="text-xl text-gray-400 mb-4">
                  {scanners[activeScannerDemo].description}
                </p>
                <div className="flex items-center gap-4">
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg font-medium">
                    <CheckCircleIcon className="w-5 h-5" />
                    {scanners[activeScannerDemo].languages}
                  </span>
                  <span className="text-gray-400">Fast & Accurate</span>
                </div>
              </div>
            </div>

            {/* Demo Terminal */}
            <div className="mt-6 bg-black/40 rounded-xl p-4 font-mono text-sm">
              <div className="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="ml-2 text-gray-400">Terminal</span>
              </div>
              <div className="space-y-1 text-green-400">
                <div>
                  $ {scanners[activeScannerDemo].name.toLowerCase()} scan
                  --target ./app
                </div>
                <div className="text-gray-500">Initializing scanner...</div>
                <div className="text-gray-500">Analyzing code...</div>
                <div className="text-yellow-400">⚠ Found 3 issues</div>
                <div className="text-green-400">✓ Scan completed in 2.3s</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scanners.map((scanner, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:shadow-2xl transition-all transform hover:scale-105"
              >
                <div
                  className={`p-3 bg-gradient-to-r ${scanner.color} rounded-xl inline-block mb-4`}
                >
                  <scanner.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  {scanner.name}
                </h3>
                <p className="text-gray-400 mb-3">{scanner.description}</p>
                <span className="inline-block px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                  {scanner.languages}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Why Choose Us
            </h2>
            <p className="text-xl text-gray-400">
              Built for modern development teams
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {benefits.map((benefit, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
              >
                <benefit.icon className="w-12 h-12 text-purple-400 mb-4" />
                <h3 className="text-xl font-bold text-white mb-3">
                  {benefit.title}
                </h3>
                <p className="text-gray-400">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Built For Every Team
            </h2>
            <p className="text-xl text-gray-400">
              From startups to enterprises
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {useCases.map((useCase, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
              >
                <useCase.icon className="w-12 h-12 text-blue-400 mb-4" />
                <h3 className="text-2xl font-bold text-white mb-3">
                  {useCase.title}
                </h3>
                <p className="text-gray-400 mb-6">{useCase.description}</p>
                <ul className="space-y-2">
                  {useCase.features.map((feature, idx) => (
                    <li
                      key={idx}
                      className="flex items-center gap-2 text-gray-300"
                    >
                      <CheckCircleIcon className="w-5 h-5 text-green-400" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Compliance Ready
          </h2>
          <p className="text-xl text-gray-400 mb-12">
            Support for 9 major compliance frameworks
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            {complianceFrameworks.map((framework, index) => (
              <div
                key={index}
                className="px-6 py-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl text-white font-semibold hover:bg-white/10 transition-all"
              >
                {framework}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section
        id="testimonials"
        className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Trusted by Security Teams
            </h2>
            <p className="text-xl text-gray-400">
              See what our customers have to say
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl border border-white/20 rounded-2xl p-8 hover:shadow-2xl transition-all transform hover:scale-105"
              >
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <svg
                      key={i}
                      className="w-5 h-5 text-yellow-400 fill-current"
                      viewBox="0 0 20 20"
                    >
                      <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-300 text-lg mb-6 italic">
                  "{testimonial.quote}"
                </p>
                <div className="flex items-center gap-4">
                  <img
                    src={testimonial.avatar}
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full border-2 border-blue-500"
                  />
                  <div>
                    <p className="text-white font-semibold">
                      {testimonial.name}
                    </p>
                    <p className="text-gray-400 text-sm">{testimonial.role}</p>
                    <p className="text-gray-500 text-sm">
                      {testimonial.company}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-400">
              Choose the plan that fits your needs
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <div
                key={index}
                className={`bg-white/5 backdrop-blur-xl border rounded-2xl p-8 hover:shadow-2xl transition-all transform hover:scale-105 ${
                  plan.popular
                    ? "border-blue-500 ring-2 ring-blue-500/50"
                    : "border-white/10"
                }`}
              >
                {plan.popular && (
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white text-sm font-bold px-4 py-1 rounded-full inline-block mb-4">
                    MOST POPULAR
                  </div>
                )}
                <h3 className="text-2xl font-bold text-white mb-2">
                  {plan.name}
                </h3>
                <div className="mb-6">
                  <span className="text-5xl font-bold text-white">
                    {plan.price}
                  </span>
                  {plan.price !== "Custom" && (
                    <span className="text-gray-400">/month</span>
                  )}
                </div>
                <p className="text-gray-400 mb-6">{plan.description}</p>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => navigate("/register")}
                  className={`block w-full text-center py-3 rounded-xl font-semibold transition-all ${
                    plan.popular
                      ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/50"
                      : "bg-white/10 text-white hover:bg-white/20"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Seamless Integrations
            </h2>
            <p className="text-xl text-gray-400">
              Connect with your favorite tools
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {integrations.map((integration, index) => (
              <div
                key={index}
                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:shadow-2xl transition-all transform hover:scale-105 flex flex-col items-center justify-center"
              >
                <div className="text-4xl mb-3">{integration.logo}</div>
                <p className="text-white font-semibold text-center">
                  {integration.name}
                </p>
                {integration.connected && (
                  <span className="text-xs text-green-400 mt-2 flex items-center gap-1">
                    <CheckCircleIcon className="w-3 h-3" />
                    Connected
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-gray-400 mb-4">
              Plus many more integrations via webhooks and API
            </p>
            <button
              onClick={() => scrollToSection("features")}
              className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 font-medium"
            >
              View all integrations
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Video Demo Section */}
      <section id="video-demo" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              See It In Action
            </h2>
            <p className="text-xl text-gray-400">
              Watch how easy it is to secure your code
            </p>
          </div>

          <div className="relative">
            <div className="relative overflow-hidden bg-gradient-to-br from-blue-600/20 to-purple-600/20 backdrop-blur-xl border border-white/10 rounded-3xl aspect-video">
              {!isVideoPlaying ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <button
                    onClick={() => setIsVideoPlaying(true)}
                    className="group relative"
                  >
                    <div className="absolute inset-0 bg-blue-500 rounded-full blur-2xl opacity-50 group-hover:opacity-70 transition-opacity animate-pulse" />
                    <div className="relative w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-2xl group-hover:scale-110 transition-transform">
                      <svg
                        className="w-12 h-12 text-white ml-1"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </button>

                  {/* Placeholder Screenshot */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-30">
                    <div className="text-center p-8">
                      <ShieldCheckIcon className="w-32 h-32 text-blue-400 mx-auto mb-4" />
                      <p className="text-2xl text-white font-semibold">
                        Platform Demo
                      </p>
                      <p className="text-gray-400">Click play to watch</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="absolute inset-0 p-8">
                  <div className="w-full h-full bg-black/40 rounded-2xl flex items-center justify-center">
                    <p className="text-white text-xl">
                      Video demo would play here
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Features Highlight Below Video */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 text-center">
                <ClockIcon className="w-10 h-10 text-blue-400 mx-auto mb-3" />
                <h4 className="text-white font-semibold mb-2">Quick Setup</h4>
                <p className="text-gray-400 text-sm">
                  Connect your repo in under 2 minutes
                </p>
              </div>
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 text-center">
                <BoltIcon className="w-10 h-10 text-purple-400 mx-auto mb-3" />
                <h4 className="text-white font-semibold mb-2">
                  Instant Results
                </h4>
                <p className="text-gray-400 text-sm">
                  Get comprehensive scan results instantly
                </p>
              </div>
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 text-center">
                <SparklesIcon className="w-10 h-10 text-pink-400 mx-auto mb-3" />
                <h4 className="text-white font-semibold mb-2">AI-Powered</h4>
                <p className="text-gray-400 text-sm">
                  Smart recommendations with GPT-4
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="relative overflow-hidden bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl p-12 text-center">
            <div className="absolute inset-0 bg-black/20" />
            <div className="relative">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Ready to Secure Your Code?
              </h2>
              <p className="text-xl text-white/90 mb-8">
                Start scanning your repositories in minutes. No credit card
                required.
              </p>
              <button
                onClick={() => navigate("/register")}
                className="px-8 py-4 bg-white hover:bg-gray-100 rounded-xl text-purple-600 font-bold text-lg shadow-2xl transition-all inline-flex items-center gap-2"
              >
                Get Started Free
                <RocketLaunchIcon className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black/40 backdrop-blur-xl border-t border-white/10 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <ShieldCheckSolid className="w-6 h-6 text-blue-400" />
                <span className="font-bold text-white">SecureDevOps AI</span>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered security scanning platform for modern development
                teams.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <a
                    href="#features"
                    className="hover:text-white transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#scanners"
                    className="hover:text-white transition-colors"
                  >
                    Scanners
                  </a>
                </li>
                <li>
                  <a
                    href="#pricing"
                    className="hover:text-white transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Documentation
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Terms
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Security
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Compliance
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-gray-400 text-sm">
            <p>&copy; 2025 SecureDevOps AI Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Back to Top Button */}
      {showBackToTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-8 right-8 z-50 p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full shadow-2xl hover:shadow-blue-500/50 transition-all transform hover:scale-110 animate-bounce"
          aria-label="Back to top"
        >
          <ArrowUpIcon className="w-6 h-6" />
        </button>
      )}
    </div>
  );
};

export default LandingPage;
