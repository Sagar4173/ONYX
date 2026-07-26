import { ShieldCheckIcon, InformationCircleIcon } from "@heroicons/react/24/outline";

const SecretDetectionSummary = ({ filteredFindings }) => {
  const secretFindings = filteredFindings.filter(
    (f) =>
      f.scanner?.toLowerCase() === "gitleaks" ||
      f.title?.toLowerCase().includes("secret") ||
      f.title?.toLowerCase().includes("credential")
  );
  const placeholderCount = secretFindings.filter((f) => f.metadata?.is_placeholder).length;
  const exampleFileCount = secretFindings.filter(
    (f) => f.metadata?.is_example_file && !f.metadata?.is_placeholder
  ).length;
  const realSecretCount = secretFindings.filter((f) => f.metadata?.is_likely_real !== false).length;

  if (secretFindings.length === 0) return null;

  return (
    <div className="glass-container rounded-xl p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-white flex items-center">
          <ShieldCheckIcon className="h-4 w-4 mr-2 text-purple-400" />
          Secret Detection Summary
        </h4>
        <span className="text-xs text-gray-400">
          {secretFindings.length} secret-related finding
          {secretFindings.length !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {realSecretCount > 0 && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-400">{realSecretCount}</div>
            <div className="text-xs text-red-300">Likely Real</div>
            <div className="text-xs text-gray-400 mt-1">Requires Action</div>
          </div>
        )}
        {placeholderCount > 0 && (
          <div className="bg-cyan-900/20 border border-cyan-500/30 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-cyan-400">{placeholderCount}</div>
            <div className="text-xs text-cyan-300">Placeholders</div>
            <div className="text-xs text-gray-400 mt-1">Example Values</div>
          </div>
        )}
        {exampleFileCount > 0 && (
          <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">{exampleFileCount}</div>
            <div className="text-xs text-yellow-300">In Example Files</div>
            <div className="text-xs text-gray-400 mt-1">Verify If Real</div>
          </div>
        )}
      </div>
      {placeholderCount > 0 || exampleFileCount > 0 ? (
        <p className="text-xs text-gray-400 mt-3 flex items-start">
          <InformationCircleIcon className="h-4 w-4 mr-1 flex-shrink-0 mt-0.5" />
          <span>
            Placeholder credentials in .env.example, README.md, or documentation files are flagged
            for awareness but typically don't require immediate action. Always verify secrets in
            example files aren't accidentally real.
          </span>
        </p>
      ) : null}
    </div>
  );
};

export default SecretDetectionSummary;
