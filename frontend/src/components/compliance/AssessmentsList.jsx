import { motion } from "framer-motion";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";
import { Card, EmptyState } from "../ui/StyleComponents";
import { formatDate, getFrameworkInfo } from "./complianceHelpers";

const FrameworkResultCard = ({ result }) => {
  const frameworkInfo = getFrameworkInfo(result.framework);
  const isPassing = result.score >= 70;

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, scale: 0.95 },
        visible: { opacity: 1, scale: 1 },
      }}
    >
      <Card className="bg-gray-800/30">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{frameworkInfo?.icon}</span>
        <span className="text-sm font-medium text-white">{frameworkInfo?.name}</span>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className={`text-2xl font-bold ${isPassing ? "text-green-400" : "text-yellow-400"}`}>
            {result.score?.toFixed(0)}%
          </p>
          <p className="text-xs text-gray-400">
            {result.passed_controls}/{result.total_controls} controls
          </p>
        </div>
        <div className="w-12 h-12">
          <svg className="transform -rotate-90" viewBox="0 0 36 36">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke={isPassing ? "#4ade80" : "#fbbf24"}
              strokeWidth="3"
              strokeDasharray={`${result.score}, 100`}
            />
          </svg>
        </div>
      </div>
    </Card>
    </motion.div>
  );
};

const AssessmentsList = ({
  assessmentsData,
  isLoading,
  isError,
  onRetry,
  onViewAssessment,
  onExportAssessment,
}) => {
  if (isError) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-xl overflow-hidden"
      >
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-xl font-semibold text-white">Compliance Assessments</h2>
        </div>
        <div className="p-12 text-center">
          <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
          </div>
          <p className="text-gray-400 mb-4">Failed to load assessments</p>
          <button
            type="button"
            onClick={onRetry}
            className="rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 px-4 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
          >
            Try Again
          </button>
        </div>
      </motion.div>
    );
  }

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-xl overflow-hidden"
      >
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-xl font-semibold text-white">Compliance Assessments</h2>
        </div>
        <div className="p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading assessments...</p>
        </div>
      </motion.div>
    );
  }

  if (!assessmentsData?.assessments?.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-xl overflow-hidden"
      >
        <div className="p-6 border-b border-gray-700/50">
          <h2 className="text-xl font-semibold text-white">Compliance Assessments</h2>
        </div>
        <EmptyState
          icon={<ShieldCheckIcon className="h-12 w-12" />}
          title="No assessments found"
          description="Create your first compliance assessment"
        />
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-xl overflow-hidden"
    >
      <div className="p-6 border-b border-gray-700/50">
        <h2 className="text-xl font-semibold text-white">Compliance Assessments</h2>
      </div>
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.06 } },
        }}
        className="divide-y divide-gray-700/50"
      >
        {assessmentsData.assessments.map((assessment) => (
          <motion.div
            key={assessment.id}
            variants={{
              hidden: { opacity: 0, x: -10 },
              visible: { opacity: 1, x: 0 },
            }}
            className="p-6 hover:bg-gray-800/30 transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">
                    Project: {assessment.project_id}
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      assessment.status === "completed"
                        ? "bg-green-500/20 text-green-400"
                        : assessment.status === "in_progress"
                          ? "bg-yellow-500/20 text-yellow-400"
                          : "bg-gray-500/20 text-gray-400"
                    }`}
                  >
                    {assessment.status}
                  </span>
                </div>
                <p className="text-sm text-gray-400">
                  Assessed: {formatDate(assessment.assessment_date)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onViewAssessment(assessment)}
                  className="p-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/30 rounded-lg text-cyan-400 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                >
                  <EyeIcon className="w-5 h-5" />
                </button>
                <button
                  onClick={() => onExportAssessment(assessment.id)}
                  className="p-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded-lg text-green-400 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
                >
                  <ArrowDownTrayIcon className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {assessment.framework_results?.map((result) => (
                <FrameworkResultCard key={result.framework} result={result} />
              ))}
            </div>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
};

export default AssessmentsList;
