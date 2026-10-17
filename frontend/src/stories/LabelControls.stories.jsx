import { useState } from "react";
import { LabelControls } from "../components/triage/LabelControls";

export default {
  title: "Triage/LabelControls",
  component: LabelControls,
};

function Stateful(args) {
  const [value, setValue] = useState(args.value ?? null);
  return <LabelControls {...args} value={value} onChange={setValue} />;
}

export const FullUntriaged = { render: Stateful, args: { value: null } };
export const FullAccepted = { render: Stateful, args: { value: "accepted" } };
export const FullFalsePositive = { render: Stateful, args: { value: "false_positive" } };
export const Compact = { render: Stateful, args: { compact: true, value: "dismissed" } };
export const Disabled = { render: Stateful, args: { value: "accepted", disabled: true } };
