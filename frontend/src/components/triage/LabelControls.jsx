import {
  ArrowUturnLeftIcon,
  CheckCircleIcon,
  MinusCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { Badge } from "../ui/StyleComponents";
import { LABEL_OPTIONS, UNTRIAGE_VALUE, displayLabel } from "../../utils/labels";

const OPTION_ICONS = {
  accepted: CheckCircleIcon,
  false_positive: XCircleIcon,
  dismissed: MinusCircleIcon,
};

const ACTIVE_CLASSES = {
  accepted: "bg-emerald-500/20 text-emerald-300 border-emerald-500/50",
  false_positive: "bg-rose-500/20 text-rose-300 border-rose-500/50",
  dismissed: "bg-gray-500/25 text-gray-200 border-gray-500/50",
};

const IDLE_CLASSES =
  "bg-gray-800/60 text-gray-300 border-gray-600/60 hover:border-gray-500 hover:text-white";

export function LabelControls({ value = null, onChange, compact = false, disabled = false }) {
  const handle = (optionValue) => {
    if (disabled) return;
    onChange?.(optionValue === value ? UNTRIAGE_VALUE : optionValue);
  };

  return (
    <div role="group" aria-label="Triage label" className="flex flex-wrap items-center gap-2">
      {LABEL_OPTIONS.map((option) => {
        const Icon = OPTION_ICONS[option.value];
        const isActive = value === option.value;
        const a11y = isActive ? `Your label: ${option.past}` : `Label as ${option.label}`;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            aria-label={a11y}
            title={a11y}
            disabled={disabled}
            onClick={() => handle(option.value)}
            className={`inline-flex items-center justify-center gap-1.5 rounded-lg border font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:opacity-50 ${
              compact ? "h-7 w-7" : "px-3 py-1.5 text-sm"
            } ${isActive ? ACTIVE_CLASSES[option.value] : IDLE_CLASSES}`}
          >
            <Icon className="h-4 w-4" />
            {!compact && option.label}
          </button>
        );
      })}

      {value && !compact && (
        <button
          type="button"
          disabled={disabled}
          onClick={() => onChange?.(UNTRIAGE_VALUE)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:opacity-50"
        >
          <ArrowUturnLeftIcon className="h-4 w-4" />
          Untriage
        </button>
      )}

      {value && !compact && <Badge variant="info">Your label: {displayLabel(value)}</Badge>}
    </div>
  );
}
