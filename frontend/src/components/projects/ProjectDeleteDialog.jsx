import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { Modal, Button } from "../ui/StyleComponents";

const ProjectDeleteDialog = ({ project, isOpen, onClose, onConfirm, isLoading }) => {
  return (
    <Modal size="sm" isOpen={isOpen} onClose={onClose} title="">
      <div className="text-center">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <ExclamationTriangleIcon className="w-8 h-8 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Delete Project</h3>
        <p className="text-gray-400 text-sm mb-1">
          Are you sure you want to delete{" "}
          <span className="text-white font-medium">{project?.name}</span>?
        </p>
        <p className="text-gray-500 text-xs mb-6">
          This action cannot be undone. All scan data, reports, and configurations will be
          permanently removed.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} isLoading={isLoading}>
            Delete
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ProjectDeleteDialog;
