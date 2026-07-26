import { Alert } from "../styles/components";

export default {
  title: "Components/Alert",
  component: Alert,
  argTypes: {
    variant: {
      control: "select",
      options: ["info", "success", "danger", "warning"],
    },
    title: { control: "text" },
    children: { control: "text" },
  },
};

export const Info = {
  args: {
    children: "This is an informational message.",
    variant: "info",
  },
};

export const Success = {
  args: {
    children: "Operation completed successfully.",
    variant: "success",
    title: "Success",
  },
};

export const Danger = {
  args: {
    children: "An error occurred while processing your request.",
    variant: "danger",
    title: "Error",
  },
};

export const Warning = {
  args: {
    children: "Please review the configuration before proceeding.",
    variant: "warning",
    title: "Warning",
    onClose: () => {},
  },
};

export const WithIcon = {
  args: {
    children: "Alert with a custom icon.",
    icon: <span>⚠</span>,
    title: "Notice",
  },
};

export const Dismissible = {
  args: {
    children: "Click the × button to dismiss this alert.",
    onClose: () => alert("Dismissed!"),
  },
};
