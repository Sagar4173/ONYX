import { useState } from "react";
import { Modal, Button } from "../styles/components";

export default {
  title: "Components/Modal",
  component: Modal,
  argTypes: {
    isOpen: { control: "boolean" },
    title: { control: "text" },
    size: {
      control: "select",
      options: ["sm", "md", "lg", "xl", "full"],
    },
  },
};

export const Default = {
  render: (args) => {
    const [open, setOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open Modal</Button>
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>
          <p>Modal content goes here.</p>
        </Modal>
      </>
    );
  },
  args: {
    title: "Example Modal",
  },
};

export const Small = {
  render: (args) => {
    const [open, setOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open Small Modal</Button>
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>
          <p>Small modal content.</p>
        </Modal>
      </>
    );
  },
  args: {
    title: "Small Modal",
    size: "sm",
  },
};

export const Large = {
  render: (args) => {
    const [open, setOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open Large Modal</Button>
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>
          <p>Large modal content with plenty of space.</p>
        </Modal>
      </>
    );
  },
  args: {
    title: "Large Modal",
    size: "lg",
  },
};
