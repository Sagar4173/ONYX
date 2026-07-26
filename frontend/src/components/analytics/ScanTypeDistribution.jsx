import { CodeBracketIcon, EyeIcon, CubeIcon, ServerIcon } from "@heroicons/react/24/outline";

const scanTypes = [
  {
    key: "sast",
    label: "Static Analysis",
    icon: CodeBracketIcon,
    color: "from-blue-500 to-cyan-500",
  },
  {
    key: "secrets",
    label: "Secret Detection",
    icon: EyeIcon,
    color: "from-purple-500 to-pink-500",
  },
  {
    key: "container",
    label: "Container Scan",
    icon: CubeIcon,
    color: "from-green-500 to-emerald-500",
  },
  {
    key: "infrastructure",
    label: "Infrastructure",
    icon: ServerIcon,
    color: "from-orange-500 to-red-500",
  },
];

const getCount = (data, key) => {
  if (!data) return 0;
  if (typeof data[key] === "number") return data[key];
  if (data[key]?.total_runs) return data[key].total_runs;
  const scannerNames = {
    sast: ["semgrep", "bandit", "eslint"],
    secrets: ["gitleaks", "trufflehog"],
    container: ["trivy", "grype"],
    infrastructure: ["checkov", "tfsec"],
  };
  let count = 0;
  scannerNames[key]?.forEach((scanner) => {
    if (data[scanner]?.total_runs) count += data[scanner].total_runs;
  });
  return count;
};

const ScanTypeDistribution = ({ data }) => (
  <div className="grid grid-cols-2 gap-4">
    {scanTypes.map((type) => {
      const count = getCount(data, type.key);
      return (
        <div
          key={type.key}
          className="p-4 rounded-xl bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 transition-all group"
        >
          <div
            className={`inline-flex p-2.5 rounded-xl bg-gradient-to-r ${type.color} mb-3 group-hover:scale-110 transition-transform`}
          >
            <type.icon className="h-5 w-5 text-white" />
          </div>
          <p className="text-2xl font-bold text-white">{count}</p>
          <p className="text-sm text-gray-400">{type.label}</p>
        </div>
      );
    })}
  </div>
);

export default ScanTypeDistribution;
