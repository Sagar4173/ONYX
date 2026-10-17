import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { triageAPI } from "../../services/api";
import toast from "react-hot-toast";
import { Badge, AnimatedCounter } from "../ui/StyleComponents";
import { LabelControls } from "../triage/LabelControls";
import { ShortcutOverlay, KeyboardHintStrip } from "../triage/ShortcutOverlay";
import { useLabelFinding } from "../../hooks/useLabelFinding";
import { useRowSelection } from "../../hooks/useRowSelection";
import { useBulkLabel } from "../../hooks/useBulkLabel";
import { useTriageShortcuts } from "../../hooks/useTriageShortcuts";
import { LABEL_OPTIONS, displayLabel } from "../../utils/labels";

const PRIORITY_COLORS = {
  immediate: {
    bg: "bg-red-500/20",
    text: "text-red-400",
    border: "border-red-500/30",
    bar: "bg-red-500",
  },
  high: {
    bg: "bg-orange-500/20",
    text: "text-orange-400",
    border: "border-orange-500/30",
    bar: "bg-orange-500",
  },
  medium: {
    bg: "bg-yellow-500/20",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    bar: "bg-yellow-500",
  },
  low: {
    bg: "bg-cyan-500/20",
    text: "text-cyan-400",
    border: "border-cyan-500/30",
    bar: "bg-cyan-500",
  },
  informational: {
    bg: "bg-gray-500/20",
    text: "text-gray-400",
    border: "border-gray-500/30",
    bar: "bg-gray-500",
  },
};

const SCORE_COLORS = [
  { threshold: 80, class: "text-red-400 bg-red-500/20 border-red-500/30" },
  { threshold: 60, class: "text-orange-400 bg-orange-500/20 border-orange-500/30" },
  { threshold: 40, class: "text-yellow-400 bg-yellow-500/20 border-yellow-500/30" },
  { threshold: 20, class: "text-cyan-400 bg-cyan-500/20 border-cyan-500/30" },
  { threshold: 0, class: "text-gray-400 bg-gray-500/20 border-gray-500/30" },
];

function getScoreColor(score) {
  for (const c of SCORE_COLORS) {
    if (score >= c.threshold) return c.class;
  }
  return SCORE_COLORS[SCORE_COLORS.length - 1].class;
}

function ScoreBadge({ score, rank }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getScoreColor(score)}`}
      title={`AI score — rank #${rank}`}
    >
      <AnimatedCounter value={score} decimals={1} />
      <span className="sr-only">AI score</span>
    </span>
  );
}

function BreakdownBar({ label, value, max = 100, color }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-gray-400">{label}</span>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-300`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-gray-300">{value.toFixed(1)}</span>
    </div>
  );
}

function ContextEditor({ context, onChange, onRescore, loading }) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs text-gray-400 mb-1">Asset Criticality</label>
        <select
          value={context.asset_criticality}
          onChange={(e) => onChange({ ...context, asset_criticality: e.target.value })}
          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Data Classification</label>
        <select
          value={context.data_classification}
          onChange={(e) => onChange({ ...context, data_classification: e.target.value })}
          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200"
        >
          <option value="public">Public</option>
          <option value="internal">Internal</option>
          <option value="confidential">Confidential</option>
          <option value="restricted">Restricted</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Exposure Level</label>
        <select
          value={context.exposure_level}
          onChange={(e) => onChange({ ...context, exposure_level: e.target.value })}
          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200"
        >
          <option value="isolated">Isolated</option>
          <option value="internal_network">Internal Network</option>
          <option value="internet_facing">Internet Facing</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1">Compliance Frameworks</label>
        <div className="flex flex-wrap gap-1">
          {["PCI_DSS", "GDPR", "HIPAA", "SOC2", "ISO_27001"].map((fw) => (
            <label key={fw} className="flex items-center gap-1 text-xs text-gray-300">
              <input
                type="checkbox"
                checked={context.compliance_frameworks.includes(fw)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...context.compliance_frameworks, fw]
                    : context.compliance_frameworks.filter((f) => f !== fw);
                  onChange({ ...context, compliance_frameworks: next });
                }}
                className="rounded border-gray-600"
              />
              {fw}
            </label>
          ))}
        </div>
      </div>
      <button
        onClick={onRescore}
        disabled={loading}
        className="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 rounded text-sm font-medium transition-colors"
      >
        {loading ? "Re-scoring..." : "Re-score"}
      </button>
    </div>
  );
}

export default function TriageDashboard({ scanId, reportId = scanId }) {
  const [expandedId, setExpandedId] = useState(null);
  const [cursorId, setCursorId] = useState(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [context, setContext] = useState({
    asset_criticality: "medium",
    data_classification: "internal",
    exposure_level: "internal_network",
    compliance_frameworks: [],
  });
  const [rescoreLoading, setRescoreLoading] = useState(false);

  const selection = useRowSelection();
  const { labelFinding, isPending: labelPending } = useLabelFinding({ reportId, scanId });
  const { applyLabels } = useBulkLabel({ reportId, scanId });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["triage", scanId, context],
    queryFn: () => triageAPI.getTriage(scanId),
    enabled: !!scanId,
  });

  const findings = data?.ranked_findings ?? [];
  const orderedIds = findings.map((f) => f.finding_id);

  const moveCursor = (delta) => {
    if (!orderedIds.length) return;
    setCursorId((prev) => {
      const idx = prev && orderedIds.includes(prev) ? orderedIds.indexOf(prev) : -1;
      const base = idx === -1 ? (delta > 0 ? -1 : orderedIds.length) : idx;
      const next = Math.min(Math.max(base + delta, 0), orderedIds.length - 1);
      return orderedIds[next];
    });
  };

  useTriageShortcuts({
    enabled: !!data,
    onLabel: (label) => {
      if (!cursorId) {
        toast.error("No row focused — press J first");
        return;
      }
      labelFinding({ findingId: cursorId, label });
    },
    onMove: moveCursor,
    onToggleHelp: () => setHelpOpen((open) => !open),
  });

  useEffect(() => {
    if (!cursorId) return;
    const row = document.getElementById(`triage-row-${cursorId}`);
    row?.scrollIntoView?.({ block: "nearest" });
  }, [cursorId]);

  const handleRescore = async () => {
    setRescoreLoading(true);
    try {
      const result = await triageAPI.rescoreTriage(scanId, context);
      toast.success("Triage re-scored with updated context");
      refetch();
    } catch (err) {
      toast.error("Failed to re-score triage");
    } finally {
      setRescoreLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-20 text-red-400">
        <p>Failed to load triage data</p>
        <button onClick={() => refetch()} className="mt-2 text-sm text-indigo-400 hover:underline">
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { priority_counts: counts, executive_summary: summary, total_findings: total } = data;
  const maxCount = Math.max(...Object.values(counts), 1);

  return (
    <div className="space-y-6">
      {/* Header + Context toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Intelligent Triage</h3>
          <p className="text-sm text-gray-400">{total} findings ranked by business impact</p>
        </div>
        <button
          onClick={() => setShowContext(!showContext)}
          className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded transition-colors"
        >
          {showContext ? "Hide Context" : "Business Context"}
        </button>
      </div>

      {/* Executive summary */}
      {summary && (
        <div className="p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg">
          <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>
        </div>
      )}

      <div className="flex gap-6">
        {/* Main content */}
        <div className="flex-1 space-y-4">
          {/* Priority distribution bars */}
          <div className="p-4 bg-gray-800/30 rounded-lg border border-gray-700/50">
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
              Priority Distribution
            </h4>
            <div className="space-y-1.5">
              {Object.entries(PRIORITY_COLORS).map(([key, colors]) => (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <span className={`w-3 h-3 rounded-full ${colors.bg} ${colors.border} border`} />
                  <span className="w-24 text-gray-400 capitalize">{key}</span>
                  <div className="flex-1 h-3 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${colors.bar} transition-all`}
                      style={{ width: `${((counts[key] || 0) / maxCount) * 100}%` }}
                    />
                  </div>
                  <span className="w-6 text-right text-gray-300 font-medium">
                    {counts[key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Ranked findings list */}
          {findings.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No findings to display.</p>
          ) : (
            <div className="space-y-2">
              {selection.count > 0 && (
                <div
                  role="group"
                  aria-label="Bulk label actions"
                  className="flex flex-wrap items-center gap-3 p-3 bg-gray-800/60 border border-gray-700/60 rounded-lg"
                >
                  <span className="text-sm text-gray-300">{selection.count} selected</span>
                  {LABEL_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className="px-3 py-1.5 rounded-lg border border-gray-600/60 bg-gray-800/60 text-sm text-gray-300 hover:text-white hover:border-gray-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
                      onClick={async () => {
                        await applyLabels([...selection.selectedIds], option.value);
                        selection.clear();
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="px-3 py-1.5 text-sm text-gray-400 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded-lg"
                    onClick={selection.clear}
                  >
                    Clear
                  </button>
                </div>
              )}

              {findings.map((f, idx) => {
                const pc =
                  PRIORITY_COLORS[f.priority.toLowerCase()] || PRIORITY_COLORS.informational;
                const isExpanded = expandedId === f.finding_id;
                const isCursor = cursorId === f.finding_id;
                return (
                  <motion.div
                    layout
                    key={f.finding_id}
                    id={`triage-row-${f.finding_id}`}
                    onClick={(e) => {
                      if (e.target.closest("a, button, input, label")) return;
                      setExpandedId(isExpanded ? null : f.finding_id);
                      setCursorId(f.finding_id);
                    }}
                    className={`bg-gray-800/30 border rounded-lg overflow-hidden transition-colors hover:border-gray-600/50 ${
                      isCursor ? "border-cyan-500/50 ring-1 ring-cyan-500/40" : "border-gray-700/50"
                    }`}
                  >
                    <div className="flex items-center gap-3 p-3">
                      <input
                        type="checkbox"
                        aria-label={`Select ${f.title}`}
                        checked={selection.isSelected(f.finding_id)}
                        readOnly
                        onClick={(e) => {
                          e.stopPropagation();
                          selection.toggle(f.finding_id, { shift: e.shiftKey, orderedIds });
                        }}
                        className="rounded border-gray-600 bg-gray-800 focus-visible:ring-2 focus-visible:ring-cyan-500"
                      />

                      <span className="text-xs text-gray-500 w-5 shrink-0">
                        #{idx + 1}
                        <span className="sr-only"> AI rank</span>
                      </span>

                      <ScoreBadge score={f.composite_score} rank={idx + 1} />

                      <span
                        className={`px-1.5 py-0.5 rounded text-xs font-medium border shrink-0 ${pc.bg} ${pc.text} ${pc.border}`}
                      >
                        {f.priority}
                      </span>

                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">
                          <Link
                            to={`/report/${reportId}/finding/${f.finding_id}`}
                            className="hover:text-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {f.title}
                          </Link>
                        </p>
                        <p className="text-xs text-gray-500 truncate">{f.file_path}</p>
                      </div>

                      {f.triage_label && (
                        <Badge variant="info" className="shrink-0">
                          Your label: {displayLabel(f.triage_label)}
                        </Badge>
                      )}

                      {f.sla_deadline && (
                        <span className="text-xs text-gray-500 shrink-0">
                          SLA: {f.sla_deadline}
                        </span>
                      )}

                      <button
                        type="button"
                        aria-expanded={isExpanded}
                        aria-label={`${isExpanded ? "Collapse" : "Expand"} details for ${f.title}`}
                        onClick={() => {
                          setExpandedId(isExpanded ? null : f.finding_id);
                          setCursorId(f.finding_id);
                        }}
                        className="p-1 rounded hover:bg-gray-700/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 shrink-0"
                      >
                        <svg
                          className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="px-3 pb-3 space-y-3 border-t border-gray-700/50 pt-3">
                        <div className="space-y-1">
                          <h5 className="text-xs font-medium text-gray-400 uppercase">
                            Score Breakdown
                          </h5>
                          <BreakdownBar
                            label="Severity"
                            value={f.score_breakdown.severity}
                            color="bg-red-500"
                          />
                          <BreakdownBar
                            label="CVSS"
                            value={f.score_breakdown.cvss}
                            color="bg-purple-500"
                          />
                          <BreakdownBar
                            label="Exploitability"
                            value={f.score_breakdown.exploitability}
                            color="bg-orange-500"
                          />
                          <BreakdownBar
                            label="Business Impact"
                            value={f.score_breakdown.business_impact}
                            color="bg-blue-500"
                          />
                          <BreakdownBar
                            label="Compliance Risk"
                            value={f.score_breakdown.compliance_risk}
                            color="bg-green-500"
                          />
                          <BreakdownBar
                            label="EPSS"
                            value={f.score_breakdown.epss}
                            color="bg-pink-500"
                          />
                          <BreakdownBar
                            label="FP Adjustment"
                            value={f.score_breakdown.false_positive_adjustment * 100}
                            max={100}
                            color="bg-gray-500"
                          />
                        </div>
                        {f.ai_triage_summary && (
                          <div>
                            <h5 className="text-xs font-medium text-gray-400 uppercase mb-1">
                              AI Triage Summary
                            </h5>
                            <p className="text-sm text-gray-300 leading-relaxed">
                              {f.ai_triage_summary}
                            </p>
                          </div>
                        )}
                        <div>
                          <h5 className="text-xs font-medium text-gray-400 uppercase mb-2">
                            Your label (human truth)
                          </h5>
                          <LabelControls
                            value={f.triage_label}
                            disabled={labelPending}
                            onChange={(label) => labelFinding({ findingId: f.finding_id, label })}
                          />
                        </div>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>

        {/* Business context sidebar */}
        {showContext && (
          <div className="w-72 shrink-0">
            <div className="p-4 bg-gray-800/30 border border-gray-700/50 rounded-lg sticky top-4">
              <h4 className="text-sm font-medium text-white mb-4">Business Context</h4>
              <ContextEditor
                context={context}
                onChange={setContext}
                onRescore={handleRescore}
                loading={rescoreLoading}
              />
            </div>
          </div>
        )}
      </div>

      <ShortcutOverlay isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
      <KeyboardHintStrip />
    </div>
  );
}
