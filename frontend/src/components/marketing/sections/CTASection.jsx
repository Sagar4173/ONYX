import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  ArrowRightIcon,
  LockClosedIcon,
  ClockIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { OnyxLogo } from "../../common";

const CTASection = () => {
  const navigate = useNavigate();

  return (
    <motion.section
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6 }}
      className="py-32 relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-purple-500/10" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.1),transparent_70%)]" />

      <div className="max-w-4xl mx-auto px-6 text-center relative">
        <OnyxLogo variant="glow" className="w-20 h-20 mx-auto mb-8" />
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Ready to Secure Your Code?
        </h2>
        <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
          Start scanning your repositories with AI-powered security analysis. Get started for free —
          no credit card required.
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
        <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <LockClosedIcon className="w-4 h-4 text-green-500" />
            <span>Secure API</span>
          </div>
          <div className="flex items-center gap-2">
            <ClockIcon className="w-4 h-4 text-green-500" />
            <span>30-Day Free Trial</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-4 h-4 text-green-500" />
            <span>No Credit Card</span>
          </div>
        </div>
      </div>
    </motion.section>
  );
};

export default CTASection;
