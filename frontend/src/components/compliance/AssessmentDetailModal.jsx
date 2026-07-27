import { motion } from "framer-motion";
import { Card, Modal } from "../ui/StyleComponents";
import { formatDate, getFrameworkInfo, getScoreColor } from "./complianceHelpers";

const AssessmentDetailModal = ({ assessment, onClose }) => {
  if (!assessment) return null;

  return (
    <Modal size="xl" isOpen={!!assessment} onClose={onClose} title="Assessment Details">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.08 } },
          }}
          className="grid grid-cols-2 gap-4 mb-6"
        >
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="bg-gray-800/30 rounded-xl p-4"
          >
            <p className="text-sm text-gray-400 mb-1">Project ID</p>
            <p className="text-lg font-semibold text-white">{assessment.project_id}</p>
          </motion.div>
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="bg-gray-800/30 rounded-xl p-4"
          >
            <p className="text-sm text-gray-400 mb-1">Status</p>
            <p className="text-lg font-semibold text-white capitalize">{assessment.status}</p>
          </motion.div>
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="bg-gray-800/30 rounded-xl p-4"
          >
            <p className="text-sm text-gray-400 mb-1">Overall Score</p>
            <p
              className={`text-2xl font-bold ${assessment.overall_score >= 70 ? "text-green-400" : "text-yellow-400"}`}
            >
              {assessment.overall_score?.toFixed(1)}%
            </p>
          </motion.div>
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 10 },
              visible: { opacity: 1, y: 0 },
            }}
            className="bg-gray-800/30 rounded-xl p-4"
          >
            <p className="text-sm text-gray-400 mb-1">Assessment Date</p>
            <p className="text-sm font-medium text-white">{formatDate(assessment.assessment_date)}</p>
          </motion.div>
        </motion.div>

        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Framework Results</h3>
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
            }}
            className="space-y-4"
          >
            {assessment.framework_results?.map((result) => {
              const frameworkInfo = getFrameworkInfo(result.framework);
              return (
                <motion.div
                  key={result.framework}
                  variants={{
                    hidden: { opacity: 0, y: 15 },
                    visible: { opacity: 1, y: 0 },
                  }}
                >
                  <Card className="bg-gray-800/30">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{frameworkInfo?.icon}</span>
                        <div>
                          <h4 className="font-semibold text-white">{frameworkInfo?.name}</h4>
                          <p className="text-sm text-gray-400">{frameworkInfo?.fullName}</p>
                        </div>
                      </div>
                      <div className={`px-4 py-2 rounded-lg ${getScoreColor(result.score)}`}>
                        <p className="text-2xl font-bold">{result.score?.toFixed(0)}%</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-400">{result.passed_controls}</p>
                        <p className="text-xs text-gray-400">Passed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-400">{result.failed_controls}</p>
                        <p className="text-xs text-gray-400">Failed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-400">{result.total_controls}</p>
                        <p className="text-xs text-gray-400">Total</p>
                      </div>
                    </div>

                    {result.recommendations?.length > 0 && (
                      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                        <p className="text-sm font-medium text-yellow-400 mb-2">Recommendations</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          {result.recommendations.slice(0, 3).map((rec, idx) => (
                            <li key={idx}>• {rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </motion.div>
    </Modal>
  );
};

export default AssessmentDetailModal;
