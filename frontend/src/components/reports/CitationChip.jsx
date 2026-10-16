import { Badge } from "../ui/StyleComponents";

export const CitationChip = ({ n, citation, pending = false, onClick }) => {
  const label = pending ? `${n}…` : citation?.header || citation?.source_id || `[${n}]`;
  return (
    <button
      type="button"
      disabled={pending}
      onClick={onClick}
      aria-label={pending ? `Citation ${n} loading` : `Citation ${n}: ${label}`}
      className="mx-0.5 inline-block max-w-[12rem] align-baseline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-gray-900 rounded-full disabled:cursor-default"
    >
      <Badge variant="info" className="max-w-full truncate block">
        {label}
      </Badge>
    </button>
  );
};
