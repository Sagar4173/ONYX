import { Input } from "../styles/components";

export default {
  title: "Components/Input",
  component: Input,
  argTypes: {
    label: { control: "text" },
    placeholder: { control: "text" },
    error: { control: "text" },
    hint: { control: "text" },
    disabled: { control: "boolean" },
    readOnly: { control: "boolean" },
    type: {
      control: "select",
      options: ["text", "email", "password", "number", "search"],
    },
  },
};

export const Default = {
  args: {
    placeholder: "Enter text...",
  },
};

export const WithLabel = {
  args: {
    label: "Username",
    placeholder: "Enter your username",
  },
};

export const WithError = {
  args: {
    label: "Email",
    defaultValue: "invalid",
    error: "Please enter a valid email address",
  },
};

export const WithHint = {
  args: {
    label: "Password",
    type: "password",
    hint: "Must be at least 8 characters",
  },
};

export const Disabled = {
  args: {
    label: "Disabled",
    defaultValue: "Cannot edit",
    disabled: true,
  },
};

export const ReadOnly = {
  args: {
    label: "Read Only",
    defaultValue: "Pre-filled value",
    readOnly: true,
  },
};
