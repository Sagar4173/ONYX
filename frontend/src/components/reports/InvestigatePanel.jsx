import { useState } from "react";
import { AIStateBlock } from "../common/AIStateBlock";
import {
  Alert,
  Button,
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
  Skeleton,
  Textarea,
} from "../ui/StyleComponents";
import { useAIFeatures } from "../../hooks/useAIFeatures";
import { useInvestigate } from "../../hooks/useInvestigate";
import { useLabelFinding } from "../../hooks/useLabelFinding";
import { InvestigateReport } from "./InvestigateReport";

const MAX_QUESTION = 2000;

function readRetryAfter(error) {
  const header = error?.response?.headers?.["retry-after"];
  const parsed = parseInt(header, 10);
  return Number.isNaN(parsed) ? null : Math.max(0, parsed);
}

function errorDetail(error) {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : null;
}

export function InvestigatePanel({
  reportId,
  scanId,
  findingId,
  findingIds = [],
  currentLabel = null,
}) {
  const { data: features, isLoading: featuresLoading } = useAIFeatures();
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState(null);
  const query = useInvestigate({ scanId, findingId, question: submitted });
  const { labelFinding, isPending: isLabelPending } = useLabelFinding({ reportId, scanId });

  const enabled = Boolean(features?.investigate_agent_enabled);
  const status = query.error?.response?.status;
  const running = submitted !== null && query.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Investigate</CardTitle>
        <CardDescription>Read-only agent analysis of this finding.</CardDescription>
      </CardHeader>

      <div className="space-y-3">
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={MAX_QUESTION}
          rows={3}
          placeholder="Optional: ask a specific question (e.g. “Is this reachable from untrusted input?”)"
          aria-label="Investigation question"
          disabled={running || (!featuresLoading && !enabled)}
        />

        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500">
            {question.length}/{MAX_QUESTION}
          </p>
          <Button
            onClick={() => setSubmitted(question.trim())}
            disabled={!enabled || featuresLoading || running}
          >
            {running ? "Investigating..." : "Investigate"}
          </Button>
        </div>

        {!featuresLoading && !enabled && (
          <AIStateBlock
            variant="disabled"
            title="Investigate agent disabled"
            description="An administrator has turned off the investigate agent."
          />
        )}

        {running && (
          <div className="space-y-3" role="status" aria-live="polite">
            <Skeleton variant="card" />
            <Skeleton variant="card" />
          </div>
        )}

        {!running && (status === 400 || status === 403) && (
          <div role="alert">
            <Alert variant="warning" title="Question blocked by safety screening">
              {errorDetail(query.error) || "Rewrite the question without instruction-like content."}
            </Alert>
          </div>
        )}

        {!running && status === 404 && (
          <AIStateBlock
            variant="error"
            title="Finding no longer available"
            description="This finding is no longer part of the report."
          />
        )}

        {!running && status === 429 && (
          <AIStateBlock
            variant="rate_limited"
            quotaRetryAfter={readRetryAfter(query.error)}
            onQuotaRetry={() => query.refetch()}
          />
        )}

        {!running && status === 503 && (
          <AIStateBlock
            variant="error"
            title="Investigation temporarily unavailable"
            description={
              errorDetail(query.error) || "The investigation service is unavailable right now."
            }
            onRetry={() => query.refetch()}
          />
        )}

        {!running && status === 502 && (
          <AIStateBlock
            variant="error"
            title="Investigation failed"
            description={
              errorDetail(query.error) || "The investigate agent hit an unexpected error."
            }
          />
        )}

        {!running && query.error && !status && (
          <AIStateBlock
            variant="error"
            title="Investigation failed"
            description={query.error.message}
            onRetry={() => query.refetch()}
          />
        )}

        {!running && query.data && (
          <InvestigateReport
            data={query.data}
            reportId={reportId}
            findingIds={findingIds}
            currentLabel={currentLabel}
            onAgreeFp={() => labelFinding({ findingId, label: "false_positive" })}
            isLabelPending={isLabelPending}
          />
        )}
      </div>
    </Card>
  );
}
