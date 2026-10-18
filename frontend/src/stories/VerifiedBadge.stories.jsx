import { VerifiedBadge } from "../components/reports/VerifiedBadge";

export default {
  title: "AI/VerifiedBadge",
  component: VerifiedBadge,
  decorators: [
    (Story) => (
      <div className="max-w-2xl bg-gray-900 p-6">
        <Story />
      </div>
    ),
  ],
};

export const SignatureMoment = {
  args: { verification: { verified: true, remaining: [], total_findings: 1 } },
};

export const NoTotal = {
  args: { verification: { verified: true, remaining: [], total_findings: null } },
};
