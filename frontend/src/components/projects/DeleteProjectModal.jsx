import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import { Button, Modal } from "../../styles/components";

const DeleteProjectModal = ({ isOpen, onClose, projectName, totalScans, deleteConfirmText, setDeleteConfirmText, onConfirm, isPending }) => (
  <Modal isOpen={isOpen} onClose={onClose} title="Delete Project Permanently" size="sm">
    <div className="text-center">
      <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-4 animate-pulse">
        <ExclamationTriangleIcon className="h-10 w-10 text-red-400" />
      </div>

      <p className="text-gray-400 mb-4">
        You are about to permanently delete <span className="text-red-400 font-semibold">"{projectName}"</span>.
      </p>

      <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-4 mb-6 text-left">
        <p className="text-red-300 text-sm font-medium mb-2">⚠️ This action will permanently delete:</p>
        <ul className="text-red-200/80 text-sm space-y-1.5 ml-4">
          <li>• The project and all its configuration</li>
          <li>• All scan reports and vulnerability findings ({totalScans} scans)</li>
          <li>• All webhook events and history</li>
          <li>• All team member associations</li>
        </ul>
        <p className="text-red-400 text-sm font-bold mt-3 text-center">🚫 This action cannot be undone!</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm text-gray-400 mb-2">
          Type <span className="text-red-400 font-mono font-bold">DELETE</span> to confirm:
        </label>
        <input type="text" value={deleteConfirmText} onChange={(e) => setDeleteConfirmText(e.target.value)} className="w-full px-4 py-3 bg-gray-800/50 border border-red-800/30 rounded-xl text-white text-center font-mono focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50" placeholder="DELETE" />
      </div>

      <div className="flex space-x-3">
        <Button variant="ghost" onClick={onClose} className="flex-1">Cancel</Button>
        <Button variant="danger" isLoading={isPending} disabled={deleteConfirmText !== "DELETE"} onClick={onConfirm} className="flex-1">
          {isPending ? "Deleting..." : "Delete Forever"}
        </Button>
      </div>
    </div>
  </Modal>
);

export default DeleteProjectModal;
