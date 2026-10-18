import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";
import { reportsAPI } from "../services/api";
import { Badge, Button, EmptyState, Skeleton } from "../components/ui/StyleComponents";
import { SeverityBadge } from "../components/reports/ReportBadges";
import { SecretFindingChips } from "../components/reports/SecretFindingChips";
import { LabelControls } from "../components/triage/LabelControls";
import { InvestigatePanel } from "../components/reports/InvestigatePanel";
import { useLabelFinding } from "../hooks/useLabelFinding";
import { displayLabel } from "../utils/labels";

function findFinding(report, findingId) {
  if (!report) return null;
  const pools = [];
  if (Array.isArray(report.findings)) pools.push(report.findings);
  for (const scanResult of report.scan_results ?? []) {
    if (Array.isArray(scanResult.findings)) pools.push(scanResult.findings);
  }
  for (const pool of pools) {
    const hit = pool.find((f) => f.id === findingId);
    if (hit) return hit;
  }
  return null;
}

function allFindingIds(report) {
  const ids = new Set();
  if (Array.isArray(report?.findings)) {
    for (const finding of report.findings) ids.add(finding.id);
  }
  for (const scanResult of report?.scan_results ?? []) {
    for (const finding of scanResult.findings ?? []) ids.add(finding.id);
  }
  return [...ids];
}

function Section({ title, children }) {
  return (
    <section className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
      <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">{title}</h2>
      {children}
    </section>
  );
}

export default function FindingDetail() {
  const { reportId, findingId } = useParams();
  const navigate = useNavigate();

  const {
    data: report,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => reportsAPI.getReport(reportId),
    retry: false,
  });

  const finding = useMemo(() => findFinding(report, findingId), [report, findingId]);
  const findingIds = useMemo(() => allFindingIds(report), [report]);
  const { labelFinding, isPending } = useLabelFinding({ reportId, scanId: report?.scan_id });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-4">
        <Skeleton variant="text" className="w-32" />
        <Skeleton variant="title" />
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-6">
          <div className="space-y-4">
            <Skeleton variant="card" />
            <Skeleton variant="card" />
          </div>
          <Skeleton variant="card" />
        </div>
      </div>
    );
  }

  if (isError || !finding) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <EmptyState
          icon={<ArrowLeftIcon className="h-10 w-10" />}
          title="Finding not found"
          description="This finding is not part of the selected report."
          action={
            <Button variant="secondary" onClick={() => navigate(`/report/${reportId}`)}>
              Back to report
            </Button>
          }
        />
      </div>
    );
  }

  const cvss = finding.cvss_score;
  const location = finding.file_path
    ? `${finding.file_path}${finding.line_number ? `:${finding.line_number}` : ""}`
    : null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <Link
        to={`/report/${reportId}`}
        className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back to report
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-6 items-start">
        <div className="space-y-6">
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <SeverityBadge severity={finding.severity} />
              <span className="text-sm text-gray-400">{finding.scanner}</span>
              <SecretFindingChips finding={finding} />
              {finding.triage_label && (
                <Badge variant="info">Your label: {displayLabel(finding.triage_label)}</Badge>
              )}
            </div>

            <h1 className="text-2xl font-bold text-white break-words">{finding.title}</h1>

            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-400">
              {finding.cwe_id && <span>CWE-{finding.cwe_id}</span>}
              {finding.cve_id && <span>{finding.cve_id}</span>}
              {cvss && (
                <span title={cvss.vector_string ?? undefined}>
                  CVSS {cvss.base_score}
                  {cvss.vector_string ? ` (${cvss.vector_string})` : ""}
                </span>
              )}
              {location && <span className="font-mono break-all">{location}</span>}
            </div>
          </div>

          <Section title="Description">
            <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
              {finding.description}
            </p>
          </Section>

          {finding.code_snippet && (
            <Section title="Code context">
              <pre className="bg-gray-900/70 border border-gray-700/60 rounded-lg p-4 overflow-x-auto text-xs text-gray-200">
                <code>{finding.code_snippet}</code>
              </pre>
            </Section>
          )}

          {finding.remediation && (
            <Section title="Remediation">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
                {finding.remediation}
              </p>
            </Section>
          )}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6">
          <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4">
            <h2 className="text-sm font-semibold text-white mb-1">Triage</h2>
            <p className="text-xs text-gray-500 mb-3">
              Your label is human truth for ML — AI rank stays separate.
            </p>
            <LabelControls
              value={finding.triage_label}
              disabled={isPending}
              onChange={(label) => labelFinding({ findingId, label })}
            />
          </div>
          <InvestigatePanel
            key={`${reportId}:${findingId}`}
            reportId={reportId}
            scanId={report.scan_id}
            findingId={findingId}
            findingIds={findingIds}
            currentLabel={finding.triage_label}
          />
        </aside>
      </div>
    </div>
  );
}
