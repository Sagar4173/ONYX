/**
 * About Page - ONYX Security Platform
 * Company information and mission
 */
import { Link, useNavigate } from "react-router-dom";
import {
  ShieldCheckIcon,
  SparklesIcon,
  UserGroupIcon,
  LightBulbIcon,
  HeartIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CpuChipIcon,
  LockClosedIcon,
  BoltIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../common";

const AboutPage = () => {
  const navigate = useNavigate();

  const values = [
    {
      icon: ShieldCheckIcon,
      title: "Security First",
      description:
        "We believe security should be accessible to every development team, not just enterprises with massive budgets.",
      gradient: "from-cyan-500 to-violet-500",
    },
    {
      icon: LightBulbIcon,
      title: "Innovation",
      description:
        "We leverage cutting-edge AI and machine learning to detect vulnerabilities that traditional tools miss.",
      gradient: "from-violet-500 to-purple-500",
    },
    {
      icon: UserGroupIcon,
      title: "Developer Experience",
      description:
        "Security tools should enhance productivity, not hinder it. We design for developers, by developers.",
      gradient: "from-emerald-500 to-green-500",
    },
    {
      icon: HeartIcon,
      title: "Transparency",
      description:
        "We're open about how we work, what we detect, and how we protect your data. No black boxes.",
      gradient: "from-pink-500 to-rose-500",
    },
  ];

  const stats = [
    { value: "AI", label: "Dual AI Providers", icon: CpuChipIcon },
    { value: "10", label: "Security Scanners", icon: ShieldCheckIcon },
    { value: "9", label: "Compliance Frameworks", icon: BoltIcon },
    { value: "256-bit", label: "Encryption Standard", icon: LockClosedIcon },
  ];

  const timeline = [
    {
      year: "2024",
      title: "The Beginning",
      description:
        "ONYX was founded with a mission to democratize application security for modern development teams.",
    },
    {
      year: "2024",
      title: "Platform Launch",
      description:
        "Released our AI-powered security scanning platform with support for 10 security scanners and 9 compliance frameworks.",
    },
    {
      year: "2025",
      title: "Enterprise Ready",
      description:
        "Launched enterprise features including advanced compliance mapping, webhook integrations, and role-based access control.",
    },
    {
      year: "Future",
      title: "Continuous Innovation",
      description:
        "Expanding AI capabilities, adding new scanners like Redis caching and Elasticsearch indexing.",
    },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <OnyxLogo className="w-8 h-8" />
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              ONYX
            </span>
          </Link>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            <span>Back</span>
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 relative overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-full blur-3xl" />

        <div className="max-w-4xl mx-auto px-6 text-center relative">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-8">
            <SparklesIcon className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-cyan-400">About ONYX</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Building the Future of{" "}
            <span className="bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">
              Application Security
            </span>
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            We're on a mission to make world-class security accessible to every development team,
            empowering developers to build secure software without slowing down.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 border-t border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">Our Mission</h2>
              <p className="text-gray-400 text-lg leading-relaxed mb-6">
                Security vulnerabilities cost businesses billions of dollars annually and erode user
                trust. Yet, most security tools are either too complex, too expensive, or too slow
                for modern development workflows.
              </p>
              <p className="text-gray-400 text-lg leading-relaxed mb-6">
                ONYX was built to change that. We combine the power of AI with proven security
                scanning technologies to deliver fast, accurate, and actionable security insights
                directly in your development pipeline.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/register"
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold hover:shadow-lg hover:shadow-cyan-500/25 transition-all flex items-center gap-2"
                >
                  Start Free Trial
                  <ArrowRightIcon className="w-4 h-4" />
                </Link>
                <Link
                  to="/"
                  className="px-6 py-3 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
                >
                  Learn More
                </Link>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              {stats.map((stat, i) => (
                <div
                  key={i}
                  className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-cyan-500/30 transition-all group"
                >
                  <stat.icon className="w-8 h-8 text-cyan-400 mb-4 group-hover:scale-110 transition-transform" />
                  <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-gray-900/30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Values</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              The principles that guide everything we do
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all group"
              >
                <div
                  className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${value.gradient} mb-4 group-hover:scale-110 transition-transform`}
                >
                  <value.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{value.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Journey</h2>
            <p className="text-gray-400 text-lg">Building security tools for the modern era</p>
          </div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500 via-violet-500 to-purple-500 hidden md:block" />

            <div className="space-y-8">
              {timeline.map((item, i) => (
                <div key={i} className="flex gap-6 md:gap-8">
                  {/* Year bubble */}
                  <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm">
                    {item.year}
                  </div>

                  {/* Content */}
                  <div className="flex-1 pt-2">
                    <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                    <p className="text-gray-400">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-purple-500/10" />

        <div className="max-w-4xl mx-auto px-6 text-center relative">
          <OnyxLogo className="w-16 h-16 mx-auto mb-6" />
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Secure Your Code?</h2>
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            Join developers who trust ONYX to protect their applications. Start your free trial
            today — no credit card required.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-bold hover:shadow-lg hover:shadow-cyan-500/25 transition-all flex items-center gap-2"
            >
              Get Started Free
              <ArrowRightIcon className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="px-8 py-4 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} ONYX Security Intelligence
          </p>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/about" className="text-cyan-400">
              About
            </Link>
            <Link to="/terms" className="text-gray-500 hover:text-gray-300 transition-colors">
              Terms
            </Link>
            <Link to="/legal" className="text-gray-500 hover:text-gray-300 transition-colors">
              Data Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AboutPage;
