import { AIStateBlock } from "../components/common/AIStateBlock";

export default {
  title: "AI/AIStateBlock",
  component: AIStateBlock,
  argTypes: {
    variant: {
      control: "select",
      options: ["loading", "empty", "error", "degraded", "rate_limited", "disabled"],
    },
    title: { control: "text" },
    description: { control: "text" },
    detail: { control: "text" },
  },
};

export const Loading = { args: { variant: "loading", title: "Analyzing scan data..." } };
export const Empty = { args: { variant: "empty", title: "No results" } };
export const ErrorWithRetry = {
  args: {
    variant: "error",
    title: "Connection lost",
    detail: "stream ended mid-answer",
    onRetry: () => {},
  },
};
export const Degraded = {
  args: { variant: "degraded", description: "Falling back to the smaller model." },
};
export const Disabled = {
  args: { variant: "disabled", description: "Investigate agent is disabled." },
};
export const RateLimited = { args: { variant: "rate_limited", quotaRetryAfter: 30 } };
