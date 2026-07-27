import { motion } from "framer-motion";
import {
  SparklesIcon,
  ExclamationTriangleIcon,
  FireIcon,
  LightBulbIcon,
  CheckCircleIcon,
  CodeBracketIcon as CodeIcon,
  DocumentTextIcon,
  ChartBarIcon,
  BoltIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

export const AISection = ({ aiAnalysis, aiLoading, aiError }) => {
  return (
    <div className="space-y-6">
      {aiLoading ? (
        <div className="glass-container rounded-xl p-8 text-center">
          <svg
            className="h-8 w-8 text-cyan-400 animate-spin mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-gray-400">Loading AI analysis...</p>
        </div>
      ) : aiAnalysis && aiAnalysis.has_analysis ? (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.05 } },
          }}
        >
          {/* Security Score Dashboard */}
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 15 },
              visible: { opacity: 1, y: 0 },
            }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {/* Security Score */}
            <div className="glass-container rounded-xl p-6 text-center">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Security Score</h4>
              <div className="relative inline-flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-gray-700"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className={
                      (aiAnalysis.security_score || 0) >= 80
                        ? "text-green-500"
                        : (aiAnalysis.security_score || 0) >= 50
                          ? "text-yellow-500"
                          : "text-red-500"
                    }
                    strokeDasharray={`${(aiAnalysis.security_score || 0) * 2.51} 251`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="absolute text-2xl font-bold text-white">
                  {aiAnalysis.security_score || "N/A"}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2">out of 100</p>
            </div>

            {/* Risk Level */}
            <div className="glass-container rounded-xl p-6 text-center">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Risk Level</h4>
              <div
                className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${
                  aiAnalysis.risk_level === "CRITICAL"
                    ? "bg-red-500/20 border-2 border-red-500"
                    : aiAnalysis.risk_level === "HIGH"
                      ? "bg-orange-500/20 border-2 border-orange-500"
                      : aiAnalysis.risk_level === "MEDIUM"
                        ? "bg-yellow-500/20 border-2 border-yellow-500"
                        : "bg-green-500/20 border-2 border-green-500"
                }`}
              >
                <span
                  className={`text-lg font-bold ${
                    aiAnalysis.risk_level === "CRITICAL"
                      ? "text-red-400"
                      : aiAnalysis.risk_level === "HIGH"
                        ? "text-orange-400"
                        : aiAnalysis.risk_level === "MEDIUM"
                          ? "text-yellow-400"
                          : "text-green-400"
                  }`}
                >
                  {aiAnalysis.risk_level || "N/A"}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Risk Score: {aiAnalysis.risk_score || "N/A"}/100
              </p>
            </div>

            {/* Fix Time Estimate */}
            <div className="glass-container rounded-xl p-6 text-center">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Estimated Fix Time</h4>
              <div className="flex items-center justify-center w-24 h-24 mx-auto bg-cyan-500/20 rounded-full border-2 border-cyan-500">
                <ClockIcon className="h-10 w-10 text-cyan-400" />
              </div>
              <p className="text-sm font-medium text-white mt-3">
                {aiAnalysis.estimated_fix_time || "N/A"}
              </p>
            </div>
          </motion.div>

          {/* Executive Summary */}
          {aiAnalysis.executive_summary && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2 text-cyan-400" />
                Executive Summary
              </h3>
              <p className="text-gray-300 leading-relaxed whitespace-pre-line">
                {aiAnalysis.executive_summary}
              </p>
            </motion.div>
          )}

          {/* Risk Assessment */}
          {aiAnalysis.overall_risk_assessment && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 mr-2 text-amber-400" />
                Risk Assessment
              </h3>
              <p className="text-gray-300 leading-relaxed">{aiAnalysis.overall_risk_assessment}</p>
            </motion.div>
          )}

          {/* Priority Findings */}
          {aiAnalysis.priority_findings?.length > 0 && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <FireIcon className="h-5 w-5 mr-2 text-red-400" />
                Priority Findings
              </h3>
              <ul className="space-y-3">
                {aiAnalysis.priority_findings.map((finding, index) => (
                  <li key={index} className="flex items-start">
                    <span className="flex-shrink-0 w-6 h-6 bg-red-500 text-white text-xs rounded-full flex items-center justify-center mr-3 mt-0.5">
                      {index + 1}
                    </span>
                    <span className="text-gray-300">{finding}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Recommendations */}
          {aiAnalysis.priority_recommendations?.length > 0 && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-400" />
                Recommendations
              </h3>
              <ul className="space-y-3">
                {aiAnalysis.priority_recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start">
                    <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-300">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Secure Code Examples */}
          {aiAnalysis.secure_code_examples &&
            Object.keys(aiAnalysis.secure_code_examples).length > 0 && (
              <motion.div
                variants={{
                  hidden: { opacity: 0, y: 15 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="glass-container rounded-xl p-6"
              >
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <CodeIcon className="h-5 w-5 mr-2 text-green-400" />
                  Secure Code Examples
                </h3>
                <div className="space-y-4">
                  {Object.entries(aiAnalysis.secure_code_examples).map(([key, example], index) => (
                    <div key={index} className="bg-gray-900/50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">{key}</h4>
                      <pre className="text-sm text-green-300 overflow-x-auto">
                        <code>{example}</code>
                      </pre>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

          {/* Compliance Impact */}
          {aiAnalysis.compliance_impact && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2 text-purple-400" />
                Compliance Impact
              </h3>
              {typeof aiAnalysis.compliance_impact === "string" ? (
                <p className="text-gray-300 leading-relaxed">{aiAnalysis.compliance_impact}</p>
              ) : (
                <div className="space-y-4">
                  {aiAnalysis.compliance_impact.overall_impact && (
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-400 font-medium">Overall Impact:</span>
                      <span
                        className={`px-2 py-1 rounded text-sm font-medium ${
                          aiAnalysis.compliance_impact.overall_impact.toLowerCase().includes("high")
                            ? "bg-red-500/20 text-red-400"
                            : aiAnalysis.compliance_impact.overall_impact
                                  .toLowerCase()
                                  .includes("medium")
                                ? "bg-yellow-500/20 text-yellow-400"
                                : "bg-green-500/20 text-green-400"
                        }`}
                      >
                        {aiAnalysis.compliance_impact.overall_impact}
                      </span>
                    </div>
                  )}
                  {aiAnalysis.compliance_impact.frameworks_affected && (
                    <div>
                      <span className="text-gray-400 font-medium">Frameworks Affected:</span>
                      <p className="text-gray-300 mt-1">
                        {aiAnalysis.compliance_impact.frameworks_affected}
                      </p>
                    </div>
                  )}
                  {aiAnalysis.compliance_impact.analysis && (
                    <div>
                      <span className="text-gray-400 font-medium">Analysis:</span>
                      <p className="text-gray-300 mt-1 leading-relaxed">
                        {aiAnalysis.compliance_impact.analysis}
                      </p>
                    </div>
                  )}
                  {aiAnalysis.compliance_impact.required_actions && (
                    <div>
                      <span className="text-gray-400 font-medium">Required Actions:</span>
                      <p className="text-gray-300 mt-1">
                        {aiAnalysis.compliance_impact.required_actions}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* Threat Categories */}
          {aiAnalysis.threat_categories && Object.keys(aiAnalysis.threat_categories).length > 0 && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <ChartBarIcon className="h-5 w-5 mr-2 text-orange-400" />
                Threat Categories Breakdown
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(aiAnalysis.threat_categories).map(([category, count]) => (
                  <div key={category} className="bg-gray-800/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{count}</p>
                    <p className="text-sm text-gray-400">{category}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Attack Vectors */}
          {aiAnalysis.attack_vectors?.length > 0 && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <BoltIcon className="h-5 w-5 mr-2 text-red-400" />
                Potential Attack Vectors
              </h3>
              <div className="space-y-3">
                {aiAnalysis.attack_vectors.map((vector, index) => (
                  <div
                    key={index}
                    className="flex items-start bg-red-900/20 border border-red-500/30 rounded-lg p-3"
                  >
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-300">{vector}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Remediation Roadmap */}
          {aiAnalysis.remediation_roadmap?.length > 0 && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2 text-green-400" />
                Remediation Roadmap
              </h3>
              <div className="space-y-4">
                {aiAnalysis.remediation_roadmap.map((phase, index) => (
                  <div key={index} className="border border-gray-700 rounded-lg overflow-hidden">
                    <div
                      className={`p-4 flex items-center justify-between ${
                        phase.priority === "CRITICAL"
                          ? "bg-red-900/30"
                          : phase.priority === "HIGH"
                            ? "bg-orange-900/30"
                            : phase.priority === "MEDIUM"
                              ? "bg-yellow-900/30"
                              : "bg-green-900/30"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-bold ${
                            phase.priority === "CRITICAL"
                              ? "bg-red-500 text-white"
                              : phase.priority === "HIGH"
                                ? "bg-orange-500 text-white"
                                : phase.priority === "MEDIUM"
                                  ? "bg-yellow-500 text-black"
                                  : "bg-green-500 text-white"
                          }`}
                        >
                          Phase {phase.phase}
                        </span>
                        <span className="font-semibold text-white">{phase.title}</span>
                      </div>
                      <span className="text-sm text-gray-400">{phase.timeline}</span>
                    </div>
                    <div className="p-4 bg-gray-800/30">
                      <ul className="space-y-2">
                        {phase.tasks?.map((task, taskIndex) => (
                          <li key={taskIndex} className="flex items-start">
                            <CheckCircleIcon className="h-4 w-4 text-gray-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-300 text-sm">{task}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Model Info */}
          {aiAnalysis.model_used && (
            <motion.div
              variants={{
                hidden: { opacity: 0, y: 10 },
                visible: { opacity: 1, y: 0 },
              }}
              className="glass-container rounded-xl p-4 bg-gray-800/30"
            >
              <p className="text-xs text-gray-500 text-center">
                🤖 Analysis generated by{" "}
                <span className="text-cyan-400">{aiAnalysis.model_used}</span>
                {aiAnalysis.generated_at &&
                  ` on ${new Date(aiAnalysis.generated_at).toLocaleString()}`}
              </p>
            </motion.div>
          )}
        </motion.div>
      ) : (
        <div className="glass-container rounded-xl p-8 text-center">
          <SparklesIcon className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">AI Analysis Not Available</h3>
          <p className="text-gray-400 mb-4">
            {aiError
              ? "Failed to load AI analysis. Please try again later."
              : "AI analysis has not been generated for this report yet."}
          </p>
          <p className="text-sm text-gray-500">
            AI analysis is automatically generated when a scan completes. If you're seeing this
            message, the analysis may still be processing or may not have been triggered.
          </p>
        </div>
      )}
    </div>
  );
};
