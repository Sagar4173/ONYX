import { Button } from "../components/ui/StyleComponents";

export default {
  title: "Components/Button",
  component: Button,
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "danger", "ghost", "outline"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    children: { control: "text" },
    disabled: { control: "boolean" },
    isLoading: { control: "boolean" },
    gradient: { control: "boolean" },
  },
};

export const Primary = {
  args: {
    children: "Primary Button",
    variant: "primary",
  },
};

export const Secondary = {
  args: {
    children: "Secondary Button",
    variant: "secondary",
  },
};

export const Danger = {
  args: {
    children: "Delete",
    variant: "danger",
  },
};

export const Ghost = {
  args: {
    children: "Ghost Button",
    variant: "ghost",
  },
};

export const Outline = {
  args: {
    children: "Outline Button",
    variant: "outline",
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

export const Loading = {
  args: {
    children: "Saving...",
    isLoading: true,
  },
};

export const Disabled = {
  args: {
    children: "Disabled",
    disabled: true,
  },
};

export const Gradient = {
  args: {
    children: "Get Started",
    gradient: true,
  },
};

export const WithIcons = {
  args: {
    children: "Settings",
    leftIcon: <span>⚙</span>,
  },
};
