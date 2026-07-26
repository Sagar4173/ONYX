import { useState } from "react";
import {
  ExclamationTriangleIcon,
  TrashIcon,
  ShieldExclamationIcon,
} from "@heroicons/react/24/outline";
import { Button, Modal } from "../../styles/components";

const DeleteProjectModal = ({
  isOpen,
  onClose,
  projectName,
  totalScans,
  deleteConfirmText,
  setDeleteConfirmText,
  onConfirm,
  isPending,
}) => {
  const [step, setStep] = useState(1);
  const [nameConfirm, setNameConfirm] = useState("");

  const handleClose = () => {
    setStep(1);
    setNameConfirm("");
    setDeleteConfirmText("");
    onClose();
  };

  const handleDelete = () => {
    if (step === 1) {
      setStep(2);
    } else {
      onConfirm();
    }
  };

  const canProceed = step === 1 ? nameConfirm === projectName : deleteConfirmText === "DELETE";

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={step === 1 ? "Delete Project" : "Final Confirmation"}
      size="sm"
    >
      <div className="text-center">
        <div
          className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4 ${step === 1 ? "bg-red-500/20" : "bg-orange-500/20"}`}
        >
          {step === 1 ? (
            <ExclamationTriangleIcon className="h-10 w-10 text-red-400" />
          ) : (
            <ShieldExclamationIcon className="h-10 w-10 text-orange-400 animate-pulse" />
          )}
        </div>

        {step === 1 ? (
          <>
            <p className="text-gray-300 font-medium mb-2">
              You are about to delete{" "}
              <span className="text-red-400 font-semibold">"{projectName}"</span>
            </p>
            <p className="text-gray-500 text-sm mb-4">
              This action is irreversible. Proceed with caution.
            </p>

            <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 mb-6 text-left">
              <p className="text-red-300 text-sm font-medium mb-2">This will permanently delete:</p>
              <ul className="text-red-200/80 text-sm space-y-1.5 ml-4">
                <li>The project and all its configuration</li>
                <li>All scan reports and vulnerability findings ({totalScans} scans)</li>
                <li>All webhook events and history</li>
                <li>All team member associations</li>
              </ul>
              <p className="text-red-400 text-sm font-bold mt-3 text-center">
                This cannot be undone!
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-2">
                Type the project name{" "}
                <span className="text-red-400 font-mono font-bold">{projectName}</span> to proceed:
              </label>
              <input
                type="text"
                value={nameConfirm}
                onChange={(e) => setNameConfirm(e.target.value)}
                className="w-full px-4 py-3 bg-gray-800/50 border border-red-800/30 rounded-xl text-white text-center font-mono text-sm focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50"
                placeholder={projectName}
              />
            </div>

            <div className="flex space-x-3">
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                variant="danger"
                disabled={!canProceed}
                onClick={handleDelete}
                className="flex-1"
              >
                Continue <TrashIcon className="w-4 h-4 ml-1.5 inline" />
              </Button>
            </div>
          </>
        ) : (
          <>
            <p className="text-gray-300 font-medium mb-2">Are you absolutely sure?</p>
            <p className="text-gray-500 text-sm mb-6">
              You are about to permanently delete{" "}
              <span className="text-red-400 font-semibold">"{projectName}"</span> with all{" "}
              {totalScans} associated scans.
            </p>

            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-2">
                Type <span className="text-red-400 font-mono font-bold">DELETE</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="w-full px-4 py-3 bg-gray-800/50 border border-orange-800/30 rounded-xl text-white text-center font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50"
                placeholder="DELETE"
              />
            </div>

            <div className="flex space-x-3">
              <Button variant="ghost" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button
                variant="danger"
                isLoading={isPending}
                disabled={!canProceed}
                onClick={handleDelete}
                className="flex-1"
              >
                {isPending ? "Deleting..." : "Delete Forever"}
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};

export default DeleteProjectModal;
