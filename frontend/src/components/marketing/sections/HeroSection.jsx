import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { SparklesIcon, ArrowRightIcon, PlayIcon, ArrowDownIcon } from "@heroicons/react/24/outline";
import { CheckBadgeIcon } from "@heroicons/react/24/solid";
import { AnimatedCounter } from "../../../components/ui/StyleComponents";
import TypeWriter from "../TypeWriter";
import FloatingParticles from "../FloatingParticles";

const HeroSection = ({ counters, scrollToSection, heroRef, securityMetrics, heroWords }) => {
  const navigate = useNavigate();

  return (
    <section ref={heroRef} className="relative min-h-screen flex items-center justify-center pt-20">
      <FloatingParticles />
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20 mb-8"
          >
            <SparklesIcon className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-gray-300">AI-Powered Security Intelligence Platform</span>
            <span className="flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black mb-6 leading-tight"
          >
            <span className="block text-white mb-2">Stop</span>
            <span className="block bg-gradient-to-r from-cyan-400 via-violet-400 to-purple-400 bg-clip-text text-transparent min-h-[1.2em]">
              <TypeWriter words={heroWords} />
            </span>
            <span className="block text-white mt-2">Before They Start</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-xl md:text-2xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed"
          >
            AI-powered security platform that scans, analyzes, and protects your codebase with 10
            specialized scanners.
            <span className="text-cyan-400 font-medium">
              {" "}
              Find vulnerabilities before they ship.
            </span>
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.45 }}
            className="flex items-center justify-center gap-6 mb-10 text-sm text-gray-500"
          >
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
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
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
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.75 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto"
          >
            {securityMetrics.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.9 + index * 0.1 }}
                className="relative group p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-cyan-500/30 transition-all hover:transform hover:-translate-y-1"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-violet-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="inline-flex p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-violet-500/20 mb-3">
                  <stat.icon className="w-5 h-5 text-cyan-400" />
                </div>
                <div className="text-3xl md:text-4xl font-black text-white mb-1">
                  {counters[Object.keys(counters)[index]] > 0 ? (
                    <AnimatedCounter
                      value={counters[Object.keys(counters)[index]]}
                      suffix={stat.label.includes("Uptime") ? "%" : "+"}
                      duration={2000}
                    />
                  ) : (
                    <span className="text-gray-600">--</span>
                  )}
                </div>
                <div className="text-sm text-gray-500">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
        <span className="text-xs text-gray-500 uppercase tracking-widest">Explore</span>
        <div className="w-6 h-10 rounded-full border-2 border-gray-700 flex items-start justify-center p-2">
          <ArrowDownIcon className="w-3 h-3 text-cyan-400 animate-bounce" />
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
