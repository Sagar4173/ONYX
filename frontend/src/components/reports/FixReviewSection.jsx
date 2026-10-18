import { useState } from "react";
import { ArrowTopRightOnSquareIcon } from "@heroicons/react/24/outline";
import {
  Alert,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Code,
  ConfirmDialog,
} from "../ui/StyleComponents";
import { AIStateBlock } from "../common/AIStateBlock";
import { useAIFeatures } from "../../hooks/useAIFeatures";
import { FixDiffViewer } from "./FixDiffViewer";
import { FixStatusRail } from "./FixStatusRail";
import { VerifiedBadge } from "./VerifiedBadge";

const ERROR_COPY = {
  race: {
    title: "Already handled elsewhere",
    description:
      "This proposal was already approved or replaced in another session. Refresh the finding to see the current state.",
  },
  not_found: {
    title: "Finding no longer available",
    description: "This finding is not part of the report any more.",
  },
  rejected: {
    title: "Auto-fix could not run",
    description: "The fix agent or a safety gate rejected this attempt.",
  },
  server: {
    title: "Auto-fix service error",
    description: "The auto-fix service failed while processing this request.",
  },
  network: {
    title: "Network error",
    description: "Could not reach the auto-fix service. Check your connection and try again.",
  },
};

function PrCard({ run }) {
  if (!run.pr_url && !run.branch) return null;
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      {run.pr_url && (
        <a
          href={run.pr_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
        >
          PR #{run.pr_number ?? "open"}
          <ArrowTopRightOnSquareIcon className="w-4 h-4" />
        </a>
      )}
      {run.branch && <Code inline>{run.branch}</Code>}
    </div>
  );
}

function VerificationNotice({ verification }) {
  if (!verification || verification.verified === true) return null;
  if (verification.verified === false) {
    return (
      <Alert variant="warning" title="Not verified by re-scan">
        The re-scan still detects this finding on the fix branch.
        {Array.isArray(verification.remaining) && verification.remaining.length > 0 && (
          <span className="block mt-1 font-mono text-xs opacity-75">
            {verification.remaining.join(" · ")}
          </span>
        )}
      </Alert>
    );
  }
  return (
    <Alert variant="warning" title="Verification could not run">
      {verification.error || "The re-scan of the fix branch did not complete."}
    </Alert>
  );
}

export function FixReviewSection({ fix, scanId, findingId, filePath }) {
  const { data: features } = useAIFeatures();
  const [dialog, setDialog] = useState(null);
  const approvalRequired = features?.auto_fix_requires_approval !== false;
  const { run, error, isProposing } = fix;

  if (!isProposing && !run && !error) return null;

  const retryable = error && error.kind !== "race" && error.kind !== "not_found";
  const proposeAgain = () => fix.propose({ scanId, findingId });

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Fix-PR review</CardTitle>
          {run && <FixStatusRail status={run.status} />}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && run && (
          <Alert
            variant="warning"
            role="alert"
            title={ERROR_COPY[error.kind]?.title ?? "Auto-fix failed"}
          >
            {ERROR_COPY[error.kind]?.description}{" "}
            <span className="block mt-1 font-mono text-xs opacity-75">{error.detail}</span>
          </Alert>
        )}

        {!run && error && (
          <AIStateBlock
            variant="error"
            title={ERROR_COPY[error.kind]?.title ?? "Auto-fix failed"}
            description={ERROR_COPY[error.kind]?.description}
            detail={error.detail}
            onRetry={retryable ? proposeAgain : undefined}
            retryLabel="Propose again"
          />
        )}

        {isProposing && (
          <AIStateBlock
            variant="loading"
            title="Running the fix agent — the repo is cloned and the patch is validated. This can take up to a minute."
          />
        )}

        {run && !isProposing && (
          <>
            {Array.isArray(run.gate_failures) &&
              run.gate_failures.map((failure) => (
                <Alert key={failure} variant="danger" title="Safety gate failure">
                  {failure}
                </Alert>
              ))}

            {run.status === "dry_run" && (
              <Alert variant="info" title="Dry-run mode">
                AUTO_FIX_DRY_RUN is enabled server-side: this patch was generated and gated but
                nothing was persisted, and it cannot be applied from here.
              </Alert>
            )}

            {run.diff ? <FixDiffViewer diff={run.diff} /> : null}

            {run.status === "awaiting_approval" && approvalRequired && (
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => setDialog("approve")}>Approve & open PR</Button>
                <Button variant="outline" onClick={() => setDialog("reject")}>
                  Reject
                </Button>
              </div>
            )}

            {run.status === "dry_run" && (
              <div className="space-y-2">
                <Button
                  disabled
                  title="Dry-run mode is enabled (AUTO_FIX_DRY_RUN) — the server never applies the patch."
                >
                  Apply fix
                </Button>
                <p className="text-xs text-gray-500">
                  Apply is unavailable while dry-run mode is on.
                </p>
              </div>
            )}

            {(run.status === "pr_created" || run.status === "verified") && (
              <div className="space-y-3">
                {run.status === "verified" && <VerifiedBadge verification={run.verification} />}
                <PrCard run={run} />
                <VerificationNotice verification={run.verification} />
              </div>
            )}

            {run.model_used && (
              <p className="text-xs text-gray-500 pt-1">🤖 Fix by {run.model_used}</p>
            )}
          </>
        )}
      </CardContent>

      <ConfirmDialog
        isOpen={dialog === "approve"}
        onClose={() => setDialog(null)}
        onConfirm={() => {
          setDialog(null);
          fix.approve({ scanId, findingId });
        }}
        title="Open a pull request?"
        message={`This creates a branch with the patch to ${filePath} and opens a PR. Type APPROVE to confirm.`}
        confirmLabel="Open pull request"
        confirmText="APPROVE"
        requireTypeToConfirm
        variant="primary"
      />
      <ConfirmDialog
        isOpen={dialog === "reject"}
        onClose={() => setDialog(null)}
        onConfirm={() => {
          setDialog(null);
          fix.reject();
        }}
        title="Reject this proposal?"
        message="Nothing is applied to your repository. You can propose a new fix at any time."
        confirmLabel="Reject proposal"
        variant="danger"
      />
    </Card>
  );
}
