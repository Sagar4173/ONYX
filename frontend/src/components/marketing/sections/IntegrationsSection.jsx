import { motion } from "framer-motion";
import { ServerStackIcon } from "@heroicons/react/24/outline";

const integrations = [
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
];

const capabilities = [
  { name: "Webhooks", desc: "CI/CD triggers" },
  { name: "REST API", desc: "Custom integration" },
  { name: "Email Alerts", desc: "Notifications" },
];

const IntegrationsSection = () => (
  <motion.section
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4 }}
    className="py-24 bg-gray-900/30"
  >
    <div className="max-w-7xl mx-auto px-6">
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
          <ServerStackIcon className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-cyan-400">Git Platform Integration</span>
        </div>
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Connect Your <span className="text-cyan-400">Repositories</span>
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Direct integration with major Git platforms. Connect your repos and start scanning.
        </p>
      </div>

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.08 } },
        }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto"
      >
        {integrations.map((item) => (
          <motion.div
            key={item.name}
            variants={{
              hidden: { opacity: 0, y: 15 },
              visible: { opacity: 1, y: 0 },
            }}
            className="group p-6 rounded-2xl bg-gray-800/30 border border-gray-800/50 hover:border-cyan-500/30 hover:bg-gray-800/50 transition-all text-center"
          >
            <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">
              {item.icon}
            </div>
            <div className="font-bold text-white text-lg mb-1">{item.name}</div>
            <div className="text-xs text-cyan-400 font-medium mb-3">{item.category}</div>
            <p className="text-sm text-gray-400">{item.desc}</p>
          </motion.div>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="text-center mt-12 p-6 rounded-2xl bg-gray-800/20 border border-gray-700/30 max-w-2xl mx-auto"
      >
        <h4 className="text-lg font-semibold text-white mb-2">Additional Capabilities</h4>
        <div className="flex flex-wrap justify-center gap-3">
          {capabilities.map((cap) => (
            <div
              key={cap.name}
              className="px-4 py-2 rounded-lg bg-gray-800/50 border border-gray-700/30"
            >
              <span className="text-white font-medium text-sm">{cap.name}</span>
              <span className="text-gray-500 text-xs ml-2">{cap.desc}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  </motion.section>
);

export default IntegrationsSection;
