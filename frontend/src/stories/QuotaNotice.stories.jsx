import { QuotaNotice } from "../components/common/QuotaNotice";

export default {
  title: "AI/QuotaNotice",
  component: QuotaNotice,
  argTypes: {
    retryAfter: { control: "number" },
  },
};

export const WithCountdown = { args: { retryAfter: 30, onRetry: () => {} } };
export const Indeterminate = { args: { retryAfter: null } };
