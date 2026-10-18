import { FixStatusRail } from "../components/reports/FixStatusRail";

export default {
  title: "AI/FixStatusRail",
  component: FixStatusRail,
  decorators: [
    (Story) => (
      <div className="bg-gray-900 p-6">
        <Story />
      </div>
    ),
  ],
};

export const DryRun = {
  args: { status: "dry_run" },
};

export const AwaitingApproval = {
  args: { status: "awaiting_approval" },
};

export const PrCreated = {
  args: { status: "pr_created" },
};

export const Verified = {
  args: { status: "verified" },
};
