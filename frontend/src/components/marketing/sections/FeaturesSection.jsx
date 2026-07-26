import React from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  CubeTransparentIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";
import { features } from "../landingPageData";

const LiveCodeDemo = ({ setShowFixModal }) => (
  <div className="mb-20 relative">
    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-violet-500/10 to-cyan-500/10 rounded-3xl blur-3xl" />
    <div className="relative bg-gray-900/80 backdrop-blur-xl rounded-3xl border border-gray-800/50 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800/50 bg-gray-900/50">
        <div className="flex items-center gap-3">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
          </div>
          <span className="text-gray-500 text-sm ml-2">auth_controller.py</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/30">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs text-cyan-400">AI Scanning</span>
          </div>
        </div>
      </div>
      <div className="p-6 font-mono text-sm">
        <div className="flex">
          <div className="text-gray-600 select-none pr-6 text-right w-12">
            1<br />2<br />3<br />4<br />5<br />6<br />7<br />8<br />9<br />
            10
            <br />
            11
          </div>
          <div className="flex-1 overflow-x-auto">
            <pre className="text-gray-300">
              <span className="text-violet-400">def</span>{" "}
              <span className="text-cyan-400">authenticate_user</span>(username, password):{"\n"}
              <span className="text-gray-500"> # SQL Query - VULNERABILITY DETECTED!</span>
              {"\n"}
              <span className="relative">
                <span className="absolute -left-4 top-0 w-1 h-full bg-red-500 rounded animate-pulse" />
                <span className="bg-red-500/20 px-1 rounded text-red-300">
                  {" "}
                  query = f"SELECT * FROM users WHERE name='{"{"}username{"}"}'"{"\n"}
                </span>
              </span>
              <span className="text-gray-500"> # Hardcoded secret - CRITICAL!</span>
              {"\n"}
              <span className="relative">
                <span className="absolute -left-4 top-0 w-1 h-full bg-amber-500 rounded animate-pulse" />
                <span className="bg-amber-500/20 px-1 rounded text-amber-300">
                  {" "}
                  api_key = "sk-prod-12345-secret-key"{"\n"}
                </span>
              </span>
              <span className="text-violet-400"> return</span> db.execute(query)
            </pre>
          </div>
        </div>
        <div className="mt-6 pt-6 border-t border-gray-800/50">
          <div className="flex items-center gap-2 mb-4">
            <CpuChipIcon className="w-5 h-5 text-cyan-400" />
            <span className="text-white font-semibold">AI Detection Results</span>
            <span className="ml-auto text-xs text-gray-500">Scan completed in 0.8s</span>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
              <div className="flex items-center gap-2 mb-2">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
                <span className="font-semibold text-red-400">SQL Injection</span>
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
                View fix suggestion <ArrowRightIcon className="w-3 h-3" />
              </button>
            </div>
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
              <div className="flex items-center gap-2 mb-2">
                <LockClosedIcon className="w-5 h-5 text-amber-400" />
                <span className="font-semibold text-amber-400">Hardcoded Secret</span>
                <span className="ml-auto text-xs px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full">
                  High
                </span>
              </div>
              <p className="text-gray-400 text-sm">Line 5: API key exposed in source code</p>
              <button
                onClick={() => setShowFixModal("secret")}
                className="mt-3 text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
              >
                View fix suggestion <ArrowRightIcon className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const FeaturesSection = ({ activeFeature, setActiveFeature, setShowFixModal }) => {
  const navigate = useNavigate();

  return (
    <section id="features" className="py-32 relative">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
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
            Powered by GPT-4 and Gemini AI with 10 security scanners. Find vulnerabilities fast.
          </p>
        </motion.div>

        <LiveCodeDemo setShowFixModal={setShowFixModal} />

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="grid lg:grid-cols-2 gap-8"
        >
          <div className="space-y-4">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.08 }}
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
                      <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
                      <span
                        className={`text-xs px-2 py-1 rounded-full bg-gradient-to-r ${feature.gradient} bg-opacity-20 text-white`}
                      >
                        {feature.stats}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>
                  </div>
                </div>
                {activeFeature === index && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gradient-to-b from-cyan-400 to-violet-500 rounded-r-full" />
                )}
              </motion.div>
            ))}
          </div>

          <div className="lg:sticky lg:top-32 h-fit">
            <div className="relative p-8 rounded-3xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 overflow-hidden min-h-[500px]">
              <div
                className={`absolute inset-0 bg-gradient-to-br ${features[activeFeature].gradient} opacity-5`}
              />
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
                <div className="mb-6 p-4 rounded-xl bg-gray-800/50 border border-gray-700/30">
                  <div className="flex items-center gap-3">
                    <div
                      className={`text-3xl font-black bg-gradient-to-r ${features[activeFeature].gradient} bg-clip-text text-transparent`}
                    >
                      {features[activeFeature].stats}
                    </div>
                    <div className="text-sm text-gray-400">Performance Metric</div>
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
              <div className="absolute top-4 right-4 text-8xl font-black text-white/5">
                {String(activeFeature + 1).padStart(2, "0")}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default FeaturesSection;
