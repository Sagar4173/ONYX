export const LABEL_OPTIONS = [
  { value: "accepted", label: "Accept", past: "Accepted" },
  { value: "false_positive", label: "False positive", past: "False positive" },
  { value: "dismissed", label: "Dismissed", past: "Dismissed" },
];

export const UNTRIAGE_VALUE = "untriaged";

export function displayLabel(label) {
  if (!label || label === UNTRIAGE_VALUE) return "Untriaged";
  const option = LABEL_OPTIONS.find((o) => o.value === label);
  return option ? option.past : label;
}

export function normalizeLabel(label) {
  return !label || label === UNTRIAGE_VALUE ? null : label;
}
