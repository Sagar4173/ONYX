import { motion, AnimatePresence } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { adminAPI } from "../../services/api";
import { useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

const roles = ["admin", "security_manager", "developer", "viewer"];

const AdminRoleModal = ({ user, onClose }) => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ userId, role }) => adminAPI.updateUserRole(userId, role),
    onSuccess: () => {
      toast.success("User role updated successfully");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard-stats"] });
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update role");
    },
  });

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="bg-gray-900 border border-gray-700/50 rounded-2xl p-6 w-full max-w-md shadow-2xl shadow-cyan-500/10"
          onClick={(e) => e.stopPropagation()}
        >
        <h3 className="text-lg font-semibold text-white mb-4">Change User Role</h3>
        <p className="text-gray-400 mb-4">
          Updating role for <span className="text-white font-medium">{user.username}</span>
        </p>
        <div className="space-y-2 mb-6">
          {roles.map((role) => (
            <button
              key={role}
              onClick={() => mutation.mutate({ userId: user.id, role })}
              disabled={mutation.isPending}
              className={`w-full p-3 rounded-lg border text-left transition-colors ${
                user.role === role
                  ? "border-cyan-500 bg-cyan-500/20 text-white"
                  : "border-gray-700/50 hover:border-gray-600 text-gray-400 hover:text-white"
              }`}
            >
              <span className="capitalize">{role.replace("_", " ")}</span>
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="w-full py-2 text-gray-400 hover:text-white transition-colors"
        >
          Cancel
        </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AdminRoleModal;
