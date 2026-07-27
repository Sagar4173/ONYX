import { motion, AnimatePresence } from "framer-motion";
import { ConfirmDialog } from "../../styles/components";

const RetentionConfirmDialog = ({ confirmDialog, onClose }) => {
  return (
    <AnimatePresence>
      {confirmDialog && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <ConfirmDialog
            isOpen={true}
            onClose={onClose}
            onConfirm={confirmDialog.onConfirm}
            title={confirmDialog.title}
            message={confirmDialog.message}
            confirmLabel="Delete"
            variant="danger"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default RetentionConfirmDialog;
