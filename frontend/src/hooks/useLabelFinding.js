import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { labelsAPI } from "../services/api";
import { displayLabel, normalizeLabel } from "../utils/labels";

function replaceFindingLabel(report, findingId, label) {
  if (!report) return report;
  const next = { ...report };
  if (Array.isArray(report.findings)) {
    next.findings = report.findings.map((f) =>
      f.id === findingId ? { ...f, triage_label: label } : f
    );
  }
  if (Array.isArray(report.scan_results)) {
    next.scan_results = report.scan_results.map((sr) =>
      Array.isArray(sr.findings)
        ? {
            ...sr,
            findings: sr.findings.map((f) =>
              f.id === findingId ? { ...f, triage_label: label } : f
            ),
          }
        : sr
    );
  }
  return next;
}

function replaceRankedLabel(triage, findingId, label) {
  if (!triage || !Array.isArray(triage.ranked_findings)) return triage;
  return {
    ...triage,
    ranked_findings: triage.ranked_findings.map((f) =>
      f.finding_id === findingId ? { ...f, triage_label: label } : f
    ),
  };
}

export function useLabelFinding({ reportId, scanId }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ findingId, label }) => labelsAPI.setFindingLabel(scanId, findingId, label),

    onMutate: async ({ findingId, label }) => {
      const normalized = normalizeLabel(label);
      await queryClient.cancelQueries({ queryKey: ["report", reportId] });
      await queryClient.cancelQueries({ queryKey: ["triage", scanId] });
      const prevReport = queryClient.getQueryData(["report", reportId]);
      const prevTriage = queryClient.getQueriesData({ queryKey: ["triage", scanId] });

      if (prevReport) {
        queryClient.setQueryData(
          ["report", reportId],
          replaceFindingLabel(prevReport, findingId, normalized)
        );
      }
      queryClient.setQueriesData({ queryKey: ["triage", scanId] }, (old) =>
        replaceRankedLabel(old, findingId, normalized)
      );
      return { prevReport, prevTriage };
    },

    onError: (error, _vars, context) => {
      if (context?.prevReport) {
        queryClient.setQueryData(["report", reportId], context.prevReport);
      }
      if (context?.prevTriage) {
        for (const [key, data] of context.prevTriage) {
          queryClient.setQueryData(key, data);
        }
      }
      toast.error("Couldn't save your label — change reverted");
    },

    onSuccess: (data, { label }) => {
      toast.success(
        normalizeLabel(label) === null
          ? "Label cleared (untriaged)"
          : `Your label: ${displayLabel(label)}`
      );
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["report", reportId] });
      queryClient.invalidateQueries({ queryKey: ["triage", scanId] });
    },
  });

  return { labelFinding: mutation.mutate, isPending: mutation.isPending };
}
