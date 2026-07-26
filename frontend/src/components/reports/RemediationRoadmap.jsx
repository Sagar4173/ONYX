import {
  RocketLaunchIcon,
  SparklesIcon,
  ClockIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";

const priorityColors = {
  immediate: {
    bg: "bg-red-500",
    border: "border-red-500",
    text: "text-red-400",
    label: "Immediate",
  },
  short_term: {
    bg: "bg-orange-500",
    border: "border-orange-500",
    text: "text-orange-400",
    label: "Short-term",
  },
  medium_term: {
    bg: "bg-yellow-500",
    border: "border-yellow-500",
    text: "text-yellow-400",
    label: "Medium-term",
  },
  long_term: {
    bg: "bg-cyan-500",
    border: "border-cyan-500",
    text: "text-cyan-400",
    label: "Long-term",
  },
};

const aiRemediationPlan = (aiAnalysis) => (
  <div className="glass-container rounded-xl p-6">
    <h4 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
      <SparklesIcon className="h-5 w-5 text-purple-400" />
      AI-Generated Remediation Plan
    </h4>
    <div className="relative">
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-green-500 via-yellow-500 to-cyan-500" />
      <div className="space-y-6">
        {aiAnalysis.remediation_roadmap.map((item, idx) => {
          const priority = priorityColors[item.priority] || priorityColors.medium_term;
          return (
            <div key={idx} className="relative pl-16">
              <div
                className={`absolute left-4 w-5 h-5 rounded-full ${priority.bg} border-4 border-gray-800`}
              />
              <div className={`glass-container rounded-xl p-5 border-l-4 ${priority.border}`}>
                <div className="flex flex-wrap items-center gap-3 mb-3">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold ${priority.bg}/20 ${priority.text}`}
                  >
                    {priority.label}
                  </span>
                  {item.category && (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400">
                      {item.category}
                    </span>
                  )}
                  {item.effort && (
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400">
                      ⏱️ {item.effort}
                    </span>
                  )}
                </div>
                <h5 className="text-white font-semibold mb-2">{item.action || item.title}</h5>
                <p className="text-gray-400 text-sm mb-3">{item.description}</p>
                {item.impact && (
                  <div className="flex items-start gap-2 text-sm">
                    <span className="text-green-400 font-medium">Impact:</span>
                    <span className="text-gray-300">{item.impact}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  </div>
);

const staticTimeline = ({ getFilteredFindings }) => {
  const criticalHigh = getFilteredFindings().filter(
    (f) => f.severity === "critical" || f.severity === "high"
  );
  const medium = getFilteredFindings().filter((f) => f.severity === "medium");
  const lowInfo = getFilteredFindings().filter(
    (f) => f.severity === "low" || f.severity === "info"
  );

  const FindingList = ({
    findings,
    severity: _severity,
    icon: Icon,
    iconColor,
    emptyColor: _emptyColor,
    emptyText,
  }) => {
    const shown = findings.slice(0, 5);
    const remaining = findings.length - 5;

    return (
      <div className="space-y-2">
        {shown.map((finding, idx) => (
          <div key={idx} className="flex items-start gap-2 text-sm">
            <Icon className={`h-4 w-4 mt-0.5 flex-shrink-0 ${iconColor}`} />
            <span className="text-gray-300">{finding.title || finding.message}</span>
          </div>
        ))}
        {remaining > 0 && <p className="text-xs text-gray-500 pl-6">+{remaining} more issues</p>}
        {findings.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-green-400">
            <CheckCircleIcon className="h-4 w-4" />
            {emptyText}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="glass-container rounded-xl p-6">
      <h4 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
        <ClockIcon className="h-5 w-5 text-cyan-400" />
        Prioritized Remediation Timeline
      </h4>
      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-red-500 via-yellow-500 to-green-500" />

        <div className="relative pl-16 pb-8">
          <div className="absolute left-4 w-5 h-5 rounded-full bg-red-500 border-4 border-gray-800" />
          <div className="glass-container rounded-xl p-5 border-l-4 border-red-500">
            <div className="flex items-center gap-3 mb-3">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400">
                Immediate (0-48 hours)
              </span>
              <span className="text-xs text-gray-500">Phase 1</span>
            </div>
            <h5 className="text-white font-semibold mb-3">Critical & High Severity Issues</h5>
            <FindingList
              findings={criticalHigh}
              icon={ExclamationCircleIcon}
              iconColor={
                criticalHigh.some((f) => f.severity === "critical")
                  ? "text-red-400"
                  : "text-orange-400"
              }
              emptyText="No critical or high severity issues found"
            />
          </div>
        </div>

        <div className="relative pl-16 pb-8">
          <div className="absolute left-4 w-5 h-5 rounded-full bg-yellow-500 border-4 border-gray-800" />
          <div className="glass-container rounded-xl p-5 border-l-4 border-yellow-500">
            <div className="flex items-center gap-3 mb-3">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400">
                Short-term (1-2 weeks)
              </span>
              <span className="text-xs text-gray-500">Phase 2</span>
            </div>
            <h5 className="text-white font-semibold mb-3">Medium Severity Issues</h5>
            <FindingList
              findings={medium}
              icon={ExclamationCircleIcon}
              iconColor="text-yellow-400"
              emptyText="No medium severity issues found"
            />
          </div>
        </div>

        <div className="relative pl-16">
          <div className="absolute left-4 w-5 h-5 rounded-full bg-green-500 border-4 border-gray-800" />
          <div className="glass-container rounded-xl p-5 border-l-4 border-green-500">
            <div className="flex items-center gap-3 mb-3">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400">
                Long-term (1+ month)
              </span>
              <span className="text-xs text-gray-500">Phase 3</span>
            </div>
            <h5 className="text-white font-semibold mb-3">Low Severity & Improvements</h5>
            <FindingList
              findings={lowInfo}
              icon={InformationCircleIcon}
              iconColor="text-cyan-400"
              emptyText="No low severity issues found"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const quickWins = (
  <div className="glass-container rounded-xl p-6">
    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
      <SparklesIcon className="h-5 w-5 text-yellow-400" />
      Quick Wins
    </h4>
    <div className="space-y-3">
      {[
        "Enable dependency vulnerability scanning in CI/CD",
        "Add security linting to pre-commit hooks",
        "Configure SAST tools for automated code review",
        "Implement secret scanning in repositories",
      ].map((item, idx) => (
        <div key={idx} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
          <CheckCircleIcon className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
          <span className="text-gray-300 text-sm">{item}</span>
        </div>
      ))}
    </div>
  </div>
);

const bestPractices = (
  <div className="glass-container rounded-xl p-6">
    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
      <ShieldCheckIcon className="h-5 w-5 text-cyan-400" />
      Security Best Practices
    </h4>
    <div className="space-y-3">
      {[
        "Implement least privilege access controls",
        "Enable multi-factor authentication (MFA)",
        "Conduct regular security training for developers",
        "Establish incident response procedures",
      ].map((item, idx) => (
        <div key={idx} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
          <LightBulbIcon className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <span className="text-gray-300 text-sm">{item}</span>
        </div>
      ))}
    </div>
  </div>
);

const RemediationRoadmap = ({ aiAnalysis, getFilteredFindings }) => {
  const criticalHigh = getFilteredFindings().filter(
    (f) => f.severity === "critical" || f.severity === "high"
  );
  const medium = getFilteredFindings().filter((f) => f.severity === "medium");
  const lowInfo = getFilteredFindings().filter(
    (f) => f.severity === "low" || f.severity === "info"
  );

  return (
    <div className="space-y-6">
      <div className="glass-container rounded-xl p-6 bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <RocketLaunchIcon className="h-6 w-6 text-green-400" />
              Remediation Roadmap
            </h3>
            <p className="text-gray-400 mt-1">
              Prioritized action plan to resolve security vulnerabilities
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{criticalHigh.length}</div>
              <div className="text-xs text-gray-400">Critical/High</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{medium.length}</div>
              <div className="text-xs text-gray-400">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-cyan-400">{lowInfo.length}</div>
              <div className="text-xs text-gray-400">Low/Info</div>
            </div>
          </div>
        </div>
      </div>

      {aiAnalysis?.remediation_roadmap?.length > 0
        ? aiRemediationPlan(aiAnalysis)
        : staticTimeline({ getFilteredFindings })}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {quickWins}
        {bestPractices}
      </div>
    </div>
  );
};

export default RemediationRoadmap;
