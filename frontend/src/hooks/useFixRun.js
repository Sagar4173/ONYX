import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { autoFixApprove, autoFixPropose } from "../services/aiClient";

const MAX_HISTORY = 10;
const EMPTY_STATE = { run: null, error: null, history: [] };
const CACHE_MS = 30 * 60 * 1000;

const keyFor = (scanId, findingId) => ["fix-run", scanId, findingId];

export function classifyFixError(error) {
  const status = error?.response?.status ?? 0;
  const rawDetail = error?.response?.data?.detail;
  const detail =
    typeof rawDetail === "string" && rawDetail ? rawDetail : error?.message || "Request failed.";
  const kind =
    status === 0
      ? "network"
      : status === 404
        ? "not_found"
        : (status === 400 || status === 409) && /no pending fix|already approved/i.test(detail)
          ? "race"
          : status === 400
            ? "rejected"
            : "server";
  return { status, detail, kind };
}

const PROPOSE_TOASTS = {
  dry_run: "Dry run complete — no changes persisted",
  awaiting_approval: "Fix proposed — awaiting your approval",
  pr_created: "Pull request opened",
  verified: "Fix verified by re-scan",
};

export function useFixRun({ scanId, findingId }) {
  const queryClient = useQueryClient();
  const queryKey = keyFor(scanId, findingId);

  const { data } = useQuery({
    queryKey,
    queryFn: () => EMPTY_STATE,
    enabled: false,
    staleTime: Infinity,
    gcTime: CACHE_MS,
    retry: false,
    refetchInterval: false,
    refetchOnReconnect: false,
  });

  const update = (vars, updater) => {
    queryClient.setQueryData(keyFor(vars.scanId, vars.findingId), (prev) =>
      updater(prev ?? EMPTY_STATE)
    );
  };

  const withHistory = (prev, action, status, ok) => ({
    ...prev,
    history: [...(prev.history ?? []), { at: Date.now(), action, status, ok }].slice(-MAX_HISTORY),
  });

  const propose = useMutation({
    mutationFn: (vars) => {
      if (!vars?.scanId || !vars?.findingId)
        throw new Error("Fix run requires scanId and findingId");
      return autoFixPropose({ scanId: vars.scanId, findingId: vars.findingId });
    },
    retry: false,
    onSuccess: (run, vars) => {
      update(vars, (prev) =>
        withHistory({ ...prev, run, error: null }, "propose", run.status, true)
      );
      toast.success(PROPOSE_TOASTS[run.status] ?? "Fix status updated");
    },
    onError: (error, vars) => {
      const classified = classifyFixError(error);
      update(vars, (prev) =>
        withHistory({ ...prev, run: null, error: classified }, "propose", "error", false)
      );
    },
  });

  const approve = useMutation({
    mutationFn: (vars) => {
      if (!vars?.scanId || !vars?.findingId)
        throw new Error("Fix run requires scanId and findingId");
      return autoFixApprove({ scanId: vars.scanId, findingId: vars.findingId });
    },
    retry: false,
    onSuccess: (run, vars) => {
      update(vars, (prev) =>
        withHistory(
          { ...prev, run: { ...run, diff: run.diff || prev.run?.diff || "" }, error: null },
          "approve",
          run.status,
          true
        )
      );
      toast.success(run.status === "verified" ? "Fix verified by re-scan" : "Pull request opened");
    },
    onError: (error, vars) => {
      const classified = classifyFixError(error);
      const staleRun = classified.kind === "race" || classified.kind === "not_found";
      update(vars, (prev) =>
        withHistory(
          { ...prev, run: staleRun ? null : prev.run, error: classified },
          "approve",
          "error",
          false
        )
      );
    },
  });

  const reject = () => {
    if (!scanId || !findingId) return;
    update({ scanId, findingId }, (prev) =>
      withHistory({ ...prev, run: null, error: null }, "reject", "dismissed", true)
    );
    toast.success("Proposal rejected — nothing was applied");
  };

  const state = data ?? EMPTY_STATE;
  return {
    run: state.run,
    error: state.error,
    history: state.history,
    propose: propose.mutate,
    approve: approve.mutate,
    reject,
    isProposing: propose.isPending && propose.variables?.findingId === findingId,
    isApproving: approve.isPending && approve.variables?.findingId === findingId,
  };
}
