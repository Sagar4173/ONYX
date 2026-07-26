import {
  InformationCircleIcon,
  ExclamationTriangleIcon,
  DocumentIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";
import { SeverityBadge } from "./ReportBadges";

const FindingCard = ({ finding, index }) => {
  const isPlaceholder = finding.metadata?.is_placeholder;
  const isExampleFile = finding.metadata?.is_example_file;
  const isLikelyReal = finding.metadata?.is_likely_real !== false;
  const isSecretFinding =
    finding.scanner?.toLowerCase() === "gitleaks" ||
    finding.title?.toLowerCase().includes("secret") ||
    finding.title?.toLowerCase().includes("credential");

  return (
    <div
      key={index}
      className={`glass-container rounded-xl p-6 ${
        isSecretFinding && !isLikelyReal
          ? "border-l-4 border-l-cyan-500 bg-cyan-900/10"
          : isSecretFinding && isExampleFile && isLikelyReal
            ? "border-l-4 border-l-orange-500 bg-orange-900/10"
            : ""
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2 flex-wrap gap-2">
            <SeverityBadge severity={finding.severity} />
            <span className="text-sm text-gray-400">{finding.scanner}</span>

            {isSecretFinding && !isLikelyReal && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                <InformationCircleIcon className="h-3 w-3 mr-1" />
                {isPlaceholder ? "Placeholder Credential" : "Example File"}
              </span>
            )}

            {isSecretFinding && isLikelyReal && isExampleFile && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">
                <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                Verify - May Be Real
              </span>
            )}
          </div>

          <h4 className="text-lg font-semibold text-white mb-2">{finding.title}</h4>

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
            <div className="flex items-center text-sm text-gray-400 mb-2">
              <DocumentIcon className="h-4 w-4 mr-1" />
              {finding.file_path}
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
    </div>
  );
};

export default FindingCard;
