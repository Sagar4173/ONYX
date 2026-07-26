import { useMutation } from "@tanstack/react-query";
import { adminAPI } from "../../services/api";
import { useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

const statuses = ["active", "inactive", "suspended", "pending_verification"];

const AdminStatusModal = ({ user, onClose }) => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ userId, status }) => adminAPI.updateUserStatus(userId, status),
    onSuccess: () => {
      toast.success("User status updated successfully");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update status");
    },
  });

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-white mb-4">Change User Status</h3>
        <p className="text-gray-400 mb-4">
          Updating status for <span className="text-white font-medium">{user.username}</span>
        </p>
        <div className="space-y-2 mb-6">
          {statuses.map((status) => (
            <button
              key={status}
              onClick={() => mutation.mutate({ userId: user.id, status })}
              disabled={mutation.isPending}
              className={`w-full p-3 rounded-lg border text-left transition-colors ${
                user.status === status
                  ? "border-cyan-500 bg-cyan-500/20 text-white"
                  : "border-gray-700 hover:border-gray-600 text-gray-400 hover:text-white"
              }`}
            >
              <span className="capitalize">{status.replace("_", " ")}</span>
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="w-full py-2 text-gray-400 hover:text-white transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default AdminStatusModal;
