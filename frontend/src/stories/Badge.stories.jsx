import { Badge, SeverityBadge } from "../components/ui/StyleComponents";

export default {
  title: "Components/Badge",
  component: Badge,
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "primary", "success", "danger", "warning", "info"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    children: { control: "text" },
  },
};

export const Default = {
  args: {
    children: "Badge",
  },
};

export const Primary = {
  args: {
    children: "Primary",
    variant: "primary",
  },
};

export const Success = {
  args: {
    children: "Passed",
    variant: "success",
  },
};

export const Danger = {
  args: {
    children: "Failed",
    variant: "danger",
  },
};

export const Warning = {
  args: {
    children: "Pending",
    variant: "warning",
  },
};

export const Small = {
  args: {
    children: "Small",
    size: "sm",
  },
};

export const Large = {
  args: {
    children: "Large",
    size: "lg",
  },
};

export const SeverityCritical = {
  render: () => <SeverityBadge severity="critical" />,
};

export const SeverityHigh = {
  render: () => <SeverityBadge severity="high" />,
};

export const SeverityMedium = {
  render: () => <SeverityBadge severity="medium" />,
};

export const SeverityLow = {
  render: () => <SeverityBadge severity="low" />,
};
