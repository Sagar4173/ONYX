import { ConfirmDialog } from "../../styles/components";

const RetentionConfirmDialog = ({ confirmDialog, onClose }) => {
  if (!confirmDialog) return null;

  return (
    <ConfirmDialog
      isOpen={true}
      onClose={onClose}
      onConfirm={confirmDialog.onConfirm}
      title={confirmDialog.title}
      message={confirmDialog.message}
      confirmLabel="Delete"
      variant="danger"
    />
  );
};

export default RetentionConfirmDialog;
