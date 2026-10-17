import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { DocumentIcon, LightBulbIcon } from "@heroicons/react/24/outline";
import { SeverityBadge } from "./ReportBadges";
import { SecretFindingChips } from "./SecretFindingChips";
import { LabelControls } from "../triage/LabelControls";
import { useLabelFinding } from "../../hooks/useLabelFinding";

const FindingCard = ({ finding, index, reportId, scanId, focused = false, onSelect }) => {
  const { labelFinding, isPending } = useLabelFinding({ reportId, scanId });
  const isExampleFile = finding.metadata?.is_example_file;
  const isLikelyReal = finding.metadata?.is_likely_real !== false;
  const isSecretFinding =
    finding.scanner?.toLowerCase() === "gitleaks" ||
    finding.title?.toLowerCase().includes("secret") ||
    finding.title?.toLowerCase().includes("credential");

  return (
    <motion.div
      key={index}
      data-finding-card
      onMouseDown={() => onSelect?.()}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      className={`glass-container rounded-xl p-4 sm:p-6 ${
        isSecretFinding && !isLikelyReal
          ? "border-l-4 border-l-cyan-500 bg-cyan-900/10"
          : isSecretFinding && isExampleFile && isLikelyReal
            ? "border-l-4 border-l-orange-500 bg-orange-900/10"
            : ""
      }${focused ? " ring-1 ring-cyan-500/50" : ""}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <SeverityBadge severity={finding.severity} />
            <span className="text-sm text-gray-400">{finding.scanner}</span>

            <SecretFindingChips finding={finding} />
          </div>

          <h4 className="text-base sm:text-lg font-semibold mb-2 break-words">
            <Link
              to={`/report/${reportId}/finding/${finding.id}`}
              className="text-white hover:text-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
            >
              {finding.title}
            </Link>
          </h4>

          <div className="mb-3" onMouseDown={(e) => e.stopPropagation()}>
            <LabelControls
              compact
              value={finding.triage_label}
              disabled={isPending}
              onChange={(label) => labelFinding({ findingId: finding.id, label })}
            />
          </div>

          {isSecretFinding && finding.metadata?.calculated_entropy && (
            <div className="flex items-center text-xs text-gray-400 mb-2">
              <span className="mr-2">Entropy:</span>
              <div className="flex items-center">
                <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden mr-2">
                  <div
                    className={`h-full ${
                      finding.metadata.calculated_entropy > 4
                        ? "bg-red-500"
                        : finding.metadata.calculated_entropy > 3
                          ? "bg-yellow-500"
                          : "bg-green-500"
                    }`}
                    style={{
                      width: `${Math.min(finding.metadata.calculated_entropy * 15, 100)}%`,
                    }}
                  />
                </div>
                <span
                  className={
                    finding.metadata.calculated_entropy > 4
                      ? "text-red-400"
                      : finding.metadata.calculated_entropy > 3
                        ? "text-yellow-400"
                        : "text-green-400"
                  }
                >
                  {finding.metadata.calculated_entropy.toFixed(2)}
                  {finding.metadata.calculated_entropy > 4
                    ? " (High - Likely Real)"
                    : finding.metadata.calculated_entropy > 3
                      ? " (Medium)"
                      : " (Low - Likely Fake)"}
                </span>
              </div>
            </div>
          )}

          <p className="text-gray-300 mb-3">{finding.description}</p>

          {finding.file_path && (
            <div className="flex items-center text-sm text-gray-400 mb-2 break-all">
              <DocumentIcon className="h-4 w-4 mr-1 flex-shrink-0" />
              <span className="min-w-0">{finding.file_path}</span>
              {finding.line_number && `:${finding.line_number}`}
            </div>
          )}

          {finding.remediation && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                isSecretFinding && !isLikelyReal
                  ? "bg-cyan-900/20 border border-cyan-500/30"
                  : "bg-green-900/20 border border-green-500/30"
              }`}
            >
              <h5
                className={`text-sm font-medium mb-2 flex items-center ${
                  isSecretFinding && !isLikelyReal ? "text-cyan-400" : "text-green-400"
                }`}
              >
                <LightBulbIcon className="h-4 w-4 mr-1" />
                {isSecretFinding && !isLikelyReal ? "Context" : "Remediation"}
              </h5>
              <p
                className={`text-sm whitespace-pre-line ${
                  isSecretFinding && !isLikelyReal ? "text-cyan-300" : "text-green-300"
                }`}
              >
                {finding.remediation}
              </p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default FindingCard;
