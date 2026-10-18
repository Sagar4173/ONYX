import { MemoryRouter } from "react-router-dom";
import { InvestigateReport } from "../components/reports/InvestigateReport";

function envelope(overrides = {}) {
  return {
    report: {
      finding_id: "qa-f-001",
      summary:
        "The vulnerable path is reachable from the public HTTP handler and flows into a raw SQL string.",
      exploitability: "Network-reachable; requires an authenticated session but no admin role.",
      evidence: [
        "src/api/orders.py:87 - user input reaches the raw query",
        "Sibling finding qa-f-002 shares src/api/orders.py",
        "No upstream validation found",
      ],
      likely_false_positive: false,
      false_positive_reasons: [
        "Values are allow-listed upstream in settings",
        "The route sits behind admin-only middleware",
      ],
      fix_guidance: "Switch to parameterized queries via SQLAlchemy bind params.",
      confidence: "medium",
      ...overrides,
    },
    provider: "groq",
    model: "llama-3.3-70b",
    usage: { prompt_tokens: 1234, completion_tokens: 456, requests: 3 },
  };
}

export default {
  title: "AI/InvestigateReport",
  component: InvestigateReport,
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div className="max-w-2xl bg-gray-900 p-4">
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
};

export const Typical = {
  args: {
    data: envelope(),
    reportId: "qa-live-check-001",
    findingIds: ["qa-f-001", "qa-f-002"],
    currentLabel: null,
  },
};

export const LikelyFalsePositive = {
  args: {
    data: envelope({ likely_false_positive: true, confidence: "high" }),
    reportId: "qa-live-check-001",
    findingIds: ["qa-f-001", "qa-f-002"],
    currentLabel: "false_positive",
  },
};

export const NoEvidence = {
  args: {
    data: envelope({ evidence: [], false_positive_reasons: [], confidence: "low" }),
    reportId: "qa-live-check-001",
    findingIds: [],
    currentLabel: null,
  },
};
