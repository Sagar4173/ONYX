import { CheckIcon } from "@heroicons/react/24/outline";

const STEPS = [
  { key: "dry_run", label: "Proposed" },
  { key: "awaiting_approval", label: "Awaiting approval" },
  { key: "pr_created", label: "PR created" },
  { key: "verified", label: "Verified" },
];

const DOT =
  "flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold";

export function FixStatusRail({ status }) {
  const index = Math.max(
    0,
    STEPS.findIndex((step) => step.key === status)
  );
  return (
    <ol className="flex flex-wrap items-center gap-x-3 gap-y-2" aria-label="Fix lifecycle">
      {STEPS.map((step, i) => {
        const state = i < index ? "done" : i === index ? "current" : "upcoming";
        return (
          <li
            key={step.key}
            className="flex items-center gap-1.5"
            aria-current={state === "current" ? "step" : undefined}
          >
            <span
              data-testid={state === "done" ? "fix-rail-done" : undefined}
              className={`${DOT} ${
                state === "done"
                  ? "bg-cyan-500/20 text-cyan-300"
                  : state === "current"
                    ? "bg-cyan-500 text-white shadow-md shadow-cyan-500/40"
                    : "bg-gray-700/60 text-gray-400"
              }`}
            >
              {state === "done" ? <CheckIcon className="h-3 w-3" /> : i + 1}
            </span>
            <span
              className={`text-xs ${
                state === "current"
                  ? "text-cyan-300 font-medium"
                  : state === "done"
                    ? "text-gray-300"
                    : "text-gray-500"
              }`}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && <span aria-hidden="true" className="h-px w-5 bg-gray-700" />}
          </li>
        );
      })}
    </ol>
  );
}
