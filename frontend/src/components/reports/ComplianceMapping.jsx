import {
  ShieldCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";

export const ComplianceMapping = ({
  COMPLIANCE_STANDARDS,
  selectedStandards,
  onToggleStandard,
  getFilteredFindings,
  mapFindingToCompliance,
}) => {
  return (
    <div className="space-y-6">
      <div className="glass-container rounded-xl p-6 bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <ShieldCheckIcon className="h-6 w-6 text-blue-400" />
              Compliance Analysis
            </h3>
            <p className="text-gray-400 mt-1">
              Map security findings against industry compliance frameworks
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.keys(COMPLIANCE_STANDARDS).map((std) => (
              <button
                key={std}
                onClick={() => onToggleStandard(std)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  selectedStandards.includes(std)
                    ? "bg-blue-600 text-white"
                    : "bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-white"
                }`}
              >
                {COMPLIANCE_STANDARDS[std].icon} {std}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div id="compliance-section">
        {selectedStandards.map((standardKey) => {
          const standard = COMPLIANCE_STANDARDS[standardKey];
          const allFindings = getFilteredFindings();

          const categoryCompliance = {};
          Object.keys(standard.categories).forEach((cat) => {
            categoryCompliance[cat] = { findings: [], compliant: true, riskLevel: "low" };
          });

          allFindings.forEach((finding) => {
            const mappedCats = mapFindingToCompliance(finding, standardKey);
            mappedCats.forEach((cat) => {
              if (categoryCompliance[cat]) {
                categoryCompliance[cat].findings.push(finding);
                categoryCompliance[cat].compliant = false;
                if (finding.severity === "critical" || finding.severity === "high") {
                  categoryCompliance[cat].riskLevel = finding.severity;
                } else if (categoryCompliance[cat].riskLevel === "low" && finding.severity === "medium") {
                  categoryCompliance[cat].riskLevel = "medium";
                }
              }
            });
          });

          const totalCategories = Object.keys(standard.categories).length;
          const compliantCategories = Object.values(categoryCompliance).filter((c) => c.compliant).length;
          const complianceRate = ((compliantCategories / totalCategories) * 100).toFixed(0);

          return (
            <div key={standardKey} className="glass-container rounded-xl overflow-hidden">
              <div className={`p-6 border-b border-gray-700/50 bg-gradient-to-r ${
                standardKey === "OWASP"
                  ? "from-orange-900/30 to-red-900/30"
                  : standardKey === "NIST"
                  ? "from-blue-900/30 to-cyan-900/30"
                  : "from-purple-900/30 to-pink-900/30"
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-4xl">{standard.icon}</span>
                    <div>
                      <h4 className="text-lg font-bold text-white">{standard.name}</h4>
                      <p className="text-sm text-gray-400">{standard.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${
                      complianceRate >= 80 ? "text-green-400" : complianceRate >= 50 ? "text-yellow-400" : "text-red-400"
                    }`}>
                      {complianceRate}%
                    </div>
                    <div className="text-sm text-gray-400">Compliance Rate</div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div className={`h-full transition-all duration-500 ${
                      complianceRate >= 80 ? "bg-green-500" : complianceRate >= 50 ? "bg-yellow-500" : "bg-red-500"
                    }`} style={{ width: `${complianceRate}%` }} />
                  </div>
                  <div className="flex justify-between mt-2 text-xs text-gray-500">
                    <span>{compliantCategories}/{totalCategories} Controls Compliant</span>
                    <span>{allFindings.length} Related Findings</span>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(standard.categories).map(([catKey, catName]) => {
                    const catData = categoryCompliance[catKey];
                    const isCompliant = catData.compliant;
                    const findingCount = catData.findings.length;

                    return (
                      <div key={catKey} className={`p-4 rounded-lg border transition-all duration-200 ${
                        isCompliant
                          ? "bg-green-900/10 border-green-500/30 hover:border-green-500/50"
                          : "bg-red-900/10 border-red-500/30 hover:border-red-500/50"
                      }`}>
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className={`p-1.5 rounded-lg ${
                              isCompliant ? "bg-green-500/20" : "bg-red-500/20"
                            }`}>
                              {isCompliant ? (
                                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                              ) : (
                                <XCircleIcon className="h-5 w-5 text-red-400" />
                              )}
                            </div>
                            <div>
                              <div className="font-medium text-white">{catKey}</div>
                              <div className="text-sm text-gray-400">{catName}</div>
                            </div>
                          </div>
                          {!isCompliant && (
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              catData.riskLevel === "critical"
                                ? "bg-red-500/20 text-red-400"
                                : catData.riskLevel === "high"
                                ? "bg-orange-500/20 text-orange-400"
                                : "bg-yellow-500/20 text-yellow-400"
                            }`}>
                              {findingCount} issue{findingCount > 1 ? "s" : ""}
                            </span>
                          )}
                        </div>

                        {!isCompliant && catData.findings.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-700/50">
                            <div className="space-y-2">
                              {catData.findings.slice(0, 3).map((finding, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-sm">
                                  <span className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                                    finding.severity === "critical"
                                      ? "bg-red-500"
                                      : finding.severity === "high"
                                      ? "bg-orange-500"
                                      : finding.severity === "medium"
                                      ? "bg-yellow-500"
                                      : "bg-blue-500"
                                  }`} />
                                  <span className="text-gray-300 truncate">
                                    {finding.title || finding.message}
                                  </span>
                                </div>
                              ))}
                              {catData.findings.length > 3 && (
                                <div className="text-xs text-gray-500 pl-4">
                                  +{catData.findings.length - 3} more findings
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass-container rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <LightBulbIcon className="h-5 w-5 text-yellow-400" />
          Compliance Recommendations
        </h4>
        <div className="space-y-3">
          {[
            {
              priority: "Critical",
              color: "red",
              text: "Address all critical and high severity findings to meet baseline compliance requirements.",
            },
            {
              priority: "High",
              color: "orange",
              text: "Implement secure coding practices and code review processes to prevent injection vulnerabilities.",
            },
            {
              priority: "Medium",
              color: "yellow",
              text: "Enable comprehensive security logging and monitoring for NIST DE (Detect) compliance.",
            },
            {
              priority: "Low",
              color: "blue",
              text: "Document security procedures and conduct regular compliance assessments.",
            },
          ].map((rec, idx) => {
            const colorClasses = {
              red: { bg: "bg-red-500/10", border: "border-red-500/20", badge: "bg-red-500/20 text-red-400" },
              orange: { bg: "bg-orange-500/10", border: "border-orange-500/20", badge: "bg-orange-500/20 text-orange-400" },
              amber: { bg: "bg-amber-500/10", border: "border-amber-500/20", badge: "bg-amber-500/20 text-amber-400" },
              blue: { bg: "bg-blue-500/10", border: "border-blue-500/20", badge: "bg-blue-500/20 text-blue-400" },
              green: { bg: "bg-green-500/10", border: "border-green-500/20", badge: "bg-green-500/20 text-green-400" },
            };
            const cc = colorClasses[rec.color] || colorClasses.blue;
            return (
            <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg ${cc.bg} border ${cc.border}`}>
              <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-semibold ${cc.badge}`}>
                {rec.priority}
              </span>
              <span className="text-gray-300 text-sm print:text-gray-700">{rec.text}</span>
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
