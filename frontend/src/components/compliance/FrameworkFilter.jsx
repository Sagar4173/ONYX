import { motion } from "framer-motion";
import { frameworks } from "./complianceHelpers";

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.04 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: -5 },
  visible: { opacity: 1, y: 0 },
};

const FrameworkFilter = ({ selectedFramework, setSelectedFramework }) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, ease: "easeOut" }}
    className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-xl lg:rounded-2xl p-3 lg:p-4 shadow-xl mb-8"
  >
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-wrap gap-2"
    >
      <motion.div variants={itemVariants}>
        <button
          onClick={() => setSelectedFramework("all")}
          className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
            selectedFramework === "all"
              ? "bg-cyan-500 text-white"
              : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
          }`}
        >
          All Frameworks
        </button>
      </motion.div>
      {frameworks.map((framework) => (
        <motion.div key={framework.id} variants={itemVariants}>
          <button
            onClick={() => setSelectedFramework(framework.id)}
            className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
              selectedFramework === framework.id
                ? `bg-gradient-to-r ${framework.color} text-white`
                : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
            }`}
          >
            {framework.icon} {framework.name}
          </button>
        </motion.div>
      ))}
    </motion.div>
  </motion.div>
);

export default FrameworkFilter;
