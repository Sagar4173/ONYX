import { ExclamationTriangleIcon, InformationCircleIcon } from "@heroicons/react/24/outline";

export function SecretFindingChips({ finding }) {
  const isSecretFinding =
    finding.scanner?.toLowerCase() === "gitleaks" ||
    finding.title?.toLowerCase().includes("secret") ||
    finding.title?.toLowerCase().includes("credential");

  if (!isSecretFinding) return null;

  const isPlaceholder = finding.metadata?.is_placeholder;
  const isExampleFile = finding.metadata?.is_example_file;
  const isLikelyReal = finding.metadata?.is_likely_real !== false;

  if (!isLikelyReal) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
        <InformationCircleIcon className="h-3 w-3 mr-1" />
        {isPlaceholder ? "Placeholder Credential" : "Example File"}
      </span>
    );
  }

  if (isExampleFile) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">
        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
        Verify - May Be Real
      </span>
    );
  }

  return null;
}
