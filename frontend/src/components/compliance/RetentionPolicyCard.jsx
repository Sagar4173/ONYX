import { motion } from "framer-motion";
import { FolderIcon, ArrowPathIcon, PencilIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Card } from "../ui/StyleComponents";
import { getActionColor, formatDate } from "./retentionHelpers";

const RetentionPolicyCard = ({ policy, onExecute, onEdit, onDelete, isExecuting, isDeleting }) => (
  <motion.div
    initial={{ opacity: 0, y: 15 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, ease: "easeOut" }}
  >
    <Card padding="lg" className="shadow-xl hover:shadow-2xl transition-all">
    <div className="flex items-start justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-cyan-500/20 rounded-lg">
          <FolderIcon className="w-6 h-6 text-cyan-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">
            {policy.policy_type.replace(/_/g, " ").toUpperCase()}
          </h3>
          <p className="text-sm text-gray-400">Retain for {policy.retention_days} days</p>
        </div>
      </div>
      <span
        className={`px-3 py-1 rounded-full text-xs font-medium ${
          policy.enabled
            ? "bg-green-500/20 text-green-400 border border-green-500/30"
            : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
        }`}
      >
        {policy.enabled ? "Active" : "Inactive"}
      </span>
    </div>

    <div className="space-y-3 mb-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">Action:</span>
        <span className={`text-sm font-medium ${getActionColor(policy.action)}`}>
          {policy.action.toUpperCase()}
        </span>
      </div>
      {policy.compliance_requirement && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Compliance:</span>
          <span className="text-sm font-medium text-purple-400">
            {policy.compliance_requirement}
          </span>
        </div>
      )}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">Created:</span>
        <span className="text-sm text-gray-300">{formatDate(policy.created_at)}</span>
      </div>
      {policy.last_executed && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Last Executed:</span>
          <span className="text-sm text-gray-300">{formatDate(policy.last_executed)}</span>
        </div>
      )}
    </div>

    <div className="flex gap-2 pt-4 border-t border-gray-700/50">
      <button
        onClick={() => onExecute(policy.id)}
        disabled={isExecuting}
        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded-lg text-green-400 font-medium transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <ArrowPathIcon className="w-4 h-4" />
        Execute
      </button>
      <button
        onClick={() => onEdit(policy)}
        className="flex items-center justify-center gap-2 px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/30 rounded-lg text-cyan-400 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <PencilIcon className="w-4 h-4" />
      </button>
      <button
        onClick={() => onDelete(policy.id)}
        disabled={isDeleting}
        className="flex items-center justify-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg text-red-400 transition-all disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <TrashIcon className="w-4 h-4" />
      </button>
    </div>
  </Card>
  </motion.div>
);

export default RetentionPolicyCard;
