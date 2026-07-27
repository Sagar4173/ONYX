import { motion } from "framer-motion";
import { complianceFrameworks } from "../landingPageData";

const complianceStandards = [
  { name: "OWASP Top 10", icon: "🛡️", desc: "Mapping" },
  { name: "NIST 800-53", icon: "🏛️", desc: "Controls" },
  { name: "ISO 27001", icon: "📋", desc: "Framework" },
  { name: "PCI-DSS", icon: "💳", desc: "Checks" },
  { name: "HIPAA", icon: "🏥", desc: "Rules" },
  { name: "SOC 2", icon: "🔒", desc: "Controls" },
];

const ComplianceSection = () => (
  <>
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="py-16 border-b border-gray-800/50 bg-gray-900/20"
    >
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-gray-500 text-sm uppercase tracking-widest mb-10">
          Compliance Frameworks We Support
        </p>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.05 } },
          }}
          className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8"
        >
          {complianceStandards.map((standard) => (
            <motion.div
              key={standard.name}
              variants={{
                hidden: { opacity: 0, y: 10 },
                visible: { opacity: 1, y: 0 },
              }}
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:border-cyan-500/30 hover:bg-gray-800/50 transition-all group cursor-default"
            >
              <span className="text-3xl group-hover:scale-110 transition-transform">
                {standard.icon}
              </span>
              <span className="text-sm font-semibold text-white tracking-wide">
                {standard.name}
              </span>
              <span className="text-xs text-cyan-400 font-medium">{standard.desc}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.section>

    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="py-24 border-y border-gray-800/50"
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h3 className="text-2xl font-bold text-white mb-4">Automated Compliance</h3>
          <p className="text-gray-400">
            Meet regulatory requirements with automated checks and reports
          </p>
        </div>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.05 } },
          }}
          className="flex flex-wrap items-center justify-center gap-6"
        >
          {complianceFrameworks.map((framework) => (
            <motion.div
              key={framework.name}
              variants={{
                hidden: { opacity: 0, y: 10 },
                visible: { opacity: 1, y: 0 },
              }}
              className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all"
            >
              <span className="text-2xl">{framework.icon}</span>
              <span className="font-medium text-gray-300">{framework.name}</span>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.section>
  </>
);

export default ComplianceSection;
