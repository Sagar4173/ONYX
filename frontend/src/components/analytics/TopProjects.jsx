import { motion } from "framer-motion";
import { FolderIcon } from "@heroicons/react/24/outline";
import { EmptyState } from "../../layouts";

const rankGradients = [
  "from-yellow-400 to-yellow-600",
  "from-gray-300 to-gray-500",
  "from-amber-600 to-amber-800",
];

const TopProjects = ({ projects = [] }) => {
  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FolderIcon}
        title="No Project Data"
        description="Scan some projects to see analytics"
      />
    );
  }

  return (
    <motion.div
      className="space-y-3"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}
    >
      {projects.slice(0, 5).map((project, index) => {
        const totalCritHigh = (project.critical_findings || 0) + (project.high_findings || 0);
        const totalMed = project.medium_findings || 0;
        const totalLow = project.low_findings || 0;
        const total = totalCritHigh + totalMed + totalLow || 1;
        return (
          <motion.div
            key={project.project_name}
            variants={{
              hidden: { opacity: 0, x: -15 },
              show: { opacity: 1, x: 0 },
            }}
            className="flex items-center justify-between p-4 rounded-xl bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 hover:bg-gray-800/60 transition-all"
          >
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-r ${
                  rankGradients[index] || "from-cyan-500 to-violet-500"
                } flex items-center justify-center text-white font-bold text-sm`}
              >
                {index + 1}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{project.project_name}</p>
                <p className="text-xs text-gray-500">{project.scans_count} scans</p>
              </div>
            </div>
            <div className="text-right flex-shrink-0 ml-4">
              <div className="flex items-center gap-2 justify-end">
                {project.critical_findings > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">
                    {project.critical_findings} critical
                  </span>
                )}
                {project.high_findings > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-xs bg-orange-500/20 text-orange-400">
                    {project.high_findings} high
                  </span>
                )}
              </div>
              <div className="mt-1.5 h-1.5 bg-gray-700/50 rounded-full overflow-hidden flex max-w-[120px] ml-auto">
                <motion.div
                  className="h-full bg-red-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${(totalCritHigh / total) * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                />
                <motion.div
                  className="h-full bg-yellow-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${(totalMed / total) * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                />
                <motion.div
                  className="h-full bg-cyan-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${(totalLow / total) * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{project.total_findings} total findings</p>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default TopProjects;
