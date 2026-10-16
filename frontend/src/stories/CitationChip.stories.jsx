import { CitationChip } from "../components/reports/CitationChip";

export default {
  title: "AI/CitationChip",
  component: CitationChip,
  argTypes: {
    pending: { control: "boolean" },
  },
};

const CITATION = {
  n: 1,
  header: "CWE-89: SQL Injection",
  source: "cwe",
  source_id: "CWE-89",
  cwe_id: "89",
  text: "Use parameterized queries.",
};

export const Hydrated = { args: { n: 1, citation: CITATION, onClick: () => {} } };
export const Pending = { args: { n: 2, citation: null, pending: true } };
export const NoHeader = {
  args: { n: 3, citation: { ...CITATION, header: null }, onClick: () => {} },
};
