import { SparklesIcon } from "@heroicons/react/24/outline";
import { Badge, Button } from "../ui/StyleComponents";
import { useAIFeatures } from "../../hooks/useAIFeatures";

const STATUS_BADGES = {
  dry_run: { variant: "info", label: "Dry run" },
  awaiting_approval: { variant: "info", label: "Awaiting approval" },
  pr_created: { variant: "success", label: "PR opened" },
  verified: { variant: "success", label: "Verified" },
};

const EXPLAIN_COPY =
  "Approval flow disabled (AUTO_FIX_REQUIRES_APPROVAL=false) — auto-fix is unavailable without review.";

export function FixTriggerCard({ fix, scanId, findingId }) {
  const { data: features } = useAIFeatures();
  const approvalRequired = features?.auto_fix_requires_approval !== false;
  const badge = fix.run ? STATUS_BADGES[fix.run.status] : null;

  return (
    <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4">
      <div className="flex items-center justify-between gap-2 mb-1">
        <h2 className="text-sm font-semibold text-white">Fix-PR</h2>
        {badge && <Badge variant={badge.variant}>{badge.label}</Badge>}
        {!badge && fix.error && <Badge variant="danger">Last attempt failed</Badge>}
      </div>
      <p className="text-xs text-gray-500 mb-3">
        Generate a patch with the fix agent, review the diff, then approve the pull request.
      </p>
      <Button
        size="sm"
        className="w-full"
        isLoading={fix.isProposing}
        disabled={!approvalRequired}
        title={!approvalRequired ? EXPLAIN_COPY : undefined}
        leftIcon={<SparklesIcon className="w-4 h-4" />}
        onClick={() => fix.propose({ scanId, findingId })}
      >
        {fix.run ? "Propose again" : "Propose fix"}
      </Button>
      {!approvalRequired && <p className="text-xs text-gray-500 mt-2">{EXPLAIN_COPY}</p>}
    </div>
  );
}
