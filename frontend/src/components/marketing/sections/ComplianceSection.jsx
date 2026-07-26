import { complianceFrameworks } from "../landingPageData";

const complianceStandards = [
  { name: "OWASP Top 10", icon: "🛡️", desc: "Mapping" },
  { name: "NIST 800-53", icon: "🏛️", desc: "Controls" },
  { name: "ISO 27001", icon: "📋", desc: "Framework" },
  { name: "PCI-DSS", icon: "💳", desc: "Checks" },
  { name: "HIPAA", icon: "🏥", desc: "Rules" },
  { name: "SOC 2", icon: "🔒", desc: "Controls" },
];

const ComplianceSection = () => (
  <>
    <section className="py-16 border-b border-gray-800/50 bg-gray-900/20">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-gray-500 text-sm uppercase tracking-widest mb-10">
          Compliance Frameworks We Support
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
          {complianceStandards.map((standard) => (
            <div
              key={standard.name}
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:border-cyan-500/30 hover:bg-gray-800/50 transition-all group cursor-default"
            >
              <span className="text-3xl group-hover:scale-110 transition-transform">
                {standard.icon}
              </span>
              <span className="text-sm font-semibold text-white tracking-wide">
                {standard.name}
              </span>
              <span className="text-xs text-cyan-400 font-medium">{standard.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </section>

    <section className="py-24 border-y border-gray-800/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h3 className="text-2xl font-bold text-white mb-4">Automated Compliance</h3>
          <p className="text-gray-400">
            Meet regulatory requirements with automated checks and reports
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-6">
          {complianceFrameworks.map((framework) => (
            <div
              key={framework.name}
              className="flex items-center gap-3 px-6 py-3 rounded-xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all"
            >
              <span className="text-2xl">{framework.icon}</span>
              <span className="font-medium text-gray-300">{framework.name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  </>
);

export default ComplianceSection;
