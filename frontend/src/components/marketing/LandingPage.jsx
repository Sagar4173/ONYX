import { motion } from "framer-motion";
import { useState, useEffect, useRef, useCallback } from "react";
import AnimatedBackground from "./AnimatedBackground";
import FixSuggestionModal from "./FixSuggestionModal";
import { securityMetrics } from "./landingPageData";
import LandingNavbar from "./sections/LandingNavbar";
import HeroSection from "./sections/HeroSection";
import ComplianceSection from "./sections/ComplianceSection";
import FeaturesSection from "./sections/FeaturesSection";
import ScannersSection from "./sections/ScannersSection";
import IntegrationsSection from "./sections/IntegrationsSection";
import WhyOnyxSection from "./sections/WhyOnyxSection";
import PricingSection from "./sections/PricingSection";
import CTASection from "./sections/CTASection";
import LandingFooter from "./sections/LandingFooter";

const DEFAULT_COUNTERS = { scans: 0, vulnerabilities: 0, developers: 0, uptime: null };

const LandingPage = () => {
  const [activeFeature, setActiveFeature] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [counters, setCounters] = useState(DEFAULT_COUNTERS);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [showFixModal, setShowFixModal] = useState(null);
  const heroRef = useRef(null);

  const heroWords = ["Vulnerabilities", "Threats", "Breaches", "Attacks", "Risks"];

  const scrollToSection = useCallback((sectionId) => {
    const el = document.getElementById(sectionId);
    if (el) el.scrollIntoView({ behavior: "smooth" });
    setIsNavOpen(false);
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e) => setMousePosition({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const fetchStats = async () => {
      try {
        const res = await fetch("/api/stats/public");
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();
        if (!cancelled) {
          setCounters({
            scans: data.total_scans || 0,
            vulnerabilities: data.total_vulnerabilities || 0,
            developers: data.total_developers || 0,
            uptime: data.uptime != null ? data.uptime : null,
          });
        }
      } catch {
        if (!cancelled) setCounters(DEFAULT_COUNTERS);
      }
    };
    fetchStats();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % 6);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % 3);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-x-hidden">
      {showFixModal && (
        <FixSuggestionModal type={showFixModal} onClose={() => setShowFixModal(null)} />
      )}

      <AnimatedBackground scrollY={scrollY} mousePosition={mousePosition} />

      <LandingNavbar
        scrollY={scrollY}
        isNavOpen={isNavOpen}
        setIsNavOpen={setIsNavOpen}
        scrollToSection={scrollToSection}
      />

      <HeroSection
        counters={counters}
        scrollToSection={scrollToSection}
        heroRef={heroRef}
        securityMetrics={securityMetrics}
        heroWords={heroWords}
      />

      <ComplianceSection />

      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="py-24 border-b border-gray-800/50 bg-gray-900/30"
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
              <span className="text-sm text-emerald-400">Quick Setup</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Secure in <span className="text-cyan-400">Minutes</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              From zero to protected in just a few simple steps
            </p>
          </div>
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
            }}
            className="grid md:grid-cols-4 gap-8"
          >
            {[
              { step: 1, title: "Connect", desc: "Link your repository" },
              { step: 2, title: "Scan", desc: "AI analyzes your code" },
              { step: 3, title: "Fix", desc: "Get remediation steps" },
              { step: 4, title: "Protect", desc: "Continuous monitoring" },
            ].map((item, i) => (
              <motion.div
                key={item.title}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="relative group"
              >
                {i < 3 && (
                  <div className="hidden md:block absolute top-12 left-full w-full h-0.5 bg-gradient-to-r from-cyan-500/50 to-transparent z-0" />
                )}
                <div className="relative bg-gray-900/50 rounded-2xl p-6 border border-gray-800/50 hover:border-cyan-500/30 transition-all group-hover:transform group-hover:-translate-y-2">
                  <div className="absolute -top-4 -left-4 w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-violet-600 flex items-center justify-center text-white font-bold text-sm">
                    {item.step}
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-gray-400 text-sm">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      <FeaturesSection
        activeFeature={activeFeature}
        setActiveFeature={setActiveFeature}
        setShowFixModal={setShowFixModal}
      />

      <ScannersSection activeTab={activeTab} setActiveTab={setActiveTab} />

      <IntegrationsSection />

      <WhyOnyxSection
        currentTestimonial={currentTestimonial}
        setCurrentTestimonial={setCurrentTestimonial}
      />

      <PricingSection />

      <CTASection />

      <LandingFooter />
    </div>
  );
};

export default LandingPage;
