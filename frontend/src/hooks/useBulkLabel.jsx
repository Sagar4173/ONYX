import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { labelsAPI } from "../services/api";
import { displayLabel } from "../utils/labels";

function collectPriorLabels(queryClient, reportId, scanId, findingIds) {
  const known = new Map();

  const report = queryClient.getQueryData(["report", reportId]);
  for (const f of report?.findings ?? []) known.set(f.id, f.triage_label ?? null);
  for (const sr of report?.scan_results ?? []) {
    for (const f of sr.findings ?? []) known.set(f.id, f.triage_label ?? null);
  }

  const triageEntries = queryClient.getQueriesData({ queryKey: ["triage", scanId] });
  for (const [, triage] of triageEntries) {
    for (const rf of triage?.ranked_findings ?? []) {
      if (!known.has(rf.finding_id)) known.set(rf.finding_id, rf.triage_label ?? null);
    }
  }

  return findingIds.map((id) => ({ findingId: id, label: known.get(id) ?? null }));
}

export function useBulkLabel({ reportId, scanId }) {
  const queryClient = useQueryClient();

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["report", reportId] });
    queryClient.invalidateQueries({ queryKey: ["triage", scanId] });
  }, [queryClient, reportId, scanId]);

  const applyLabels = useCallback(
    async (findingIds, label) => {
      if (!findingIds.length) return;

      const prior = collectPriorLabels(queryClient, reportId, scanId, findingIds);
      const total = findingIds.length;
      let ok = 0;

      for (const findingId of findingIds) {
        try {
          await labelsAPI.setFindingLabel(scanId, findingId, label);
          ok += 1;
        } catch (error) {
          console.error("Bulk label failed for", findingId, error);
        }
      }
      invalidate();

      const restore = async () => {
        let restored = 0;
        for (const entry of prior) {
          try {
            await labelsAPI.setFindingLabel(scanId, entry.findingId, entry.label);
            restored += 1;
          } catch (error) {
            console.error("Undo failed for", entry.findingId, error);
          }
        }
        invalidate();
        if (restored === total) {
          toast.success("Change undone");
        } else {
          toast.error(`${restored}/${total} restored`);
        }
      };

      if (ok === 0) {
        toast.error(`Couldn't label ${total} finding${total === 1 ? "" : "s"}`);
        return;
      }
      if (ok < total) {
        toast.error(`${ok}/${total} labels saved`);
      }

      toast(
        (t) => (
          <span className="flex items-center gap-3 text-sm text-gray-200">
            <span>
              Labeled {ok} finding{ok === 1 ? "" : "s"} as {displayLabel(label)}
            </span>
            <button
              type="button"
              className="font-semibold underline text-cyan-300 hover:text-cyan-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
              onClick={() => {
                toast.dismiss(t.id);
                restore();
              }}
            >
              Undo
            </button>
          </span>
        ),
        { duration: 5000 }
      );
    },
    [queryClient, reportId, scanId, invalidate]
  );

  return { applyLabels };
}
