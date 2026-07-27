import { motion } from "framer-motion";
import { Button, Modal } from "../ui/StyleComponents";
import { policyTypes, retentionActions } from "./retentionHelpers";

const RetentionFormModal = ({
  isOpen,
  onClose,
  formData,
  setFormData,
  editingPolicy,
  onSubmit,
  isPending,
}) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    title={`${editingPolicy ? "Edit" : "Create"} Retention Policy`}
    size="lg"
    footer={
      <>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button type="submit" form="retention-form" gradient isLoading={isPending}>
          {editingPolicy ? "Update" : "Create"} Policy
        </Button>
      </>
    }
  >
    <form id="retention-form" onSubmit={onSubmit} className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <label className="block text-sm font-medium text-gray-300 mb-2">Policy Type *</label>
        <select
          value={formData.policy_type}
          onChange={(e) => setFormData({ ...formData, policy_type: e.target.value })}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          required
        >
          {policyTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.05 }}
      >
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Retention Period (Days) *
        </label>
        <input
          type="number"
          value={formData.retention_days}
          onChange={(e) => setFormData({ ...formData, retention_days: parseInt(e.target.value) })}
          min="1"
          max="3650"
          className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
          required
        />
        <p className="mt-2 text-sm text-gray-400">
          Common periods: 30 days, 90 days, 1 year (365), 7 years (2555)
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.1 }}
      >
        <label className="block text-sm font-medium text-gray-300 mb-2">Retention Action *</label>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            visible: { transition: { staggerChildren: 0.05 } },
          }}
          className="grid grid-cols-2 gap-3"
        >
          {retentionActions.map((action) => (
            <motion.div
              key={action.value}
              variants={{
                hidden: { opacity: 0, scale: 0.95 },
                visible: { opacity: 1, scale: 1 },
              }}
            >
              <button
                type="button"
                onClick={() => setFormData({ ...formData, action: action.value })}
                className={`w-full p-4 border rounded-xl text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                  formData.action === action.value
                    ? "bg-cyan-500/20 border-cyan-500/50"
                    : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-700/50"
                }`}
              >
                <p className={`font-medium ${action.color}`}>{action.label}</p>
                <p className="text-xs text-gray-400 mt-1">{action.description}</p>
              </button>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.15 }}
      >
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Compliance Requirement (Optional)
        </label>
        <input
          type="text"
          value={formData.compliance_requirement}
          onChange={(e) => setFormData({ ...formData, compliance_requirement: e.target.value })}
          placeholder="e.g., SOX, HIPAA, GDPR"
          className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: 0.2 }}
        className="flex items-center justify-between p-4 bg-gray-800/30 border border-gray-700/50 rounded-xl"
      >
        <div>
          <p className="font-medium text-white">Enable Policy</p>
          <p className="text-sm text-gray-400">Activate this retention policy immediately</p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={formData.enabled}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500" />
        </label>
      </motion.div>
    </form>
  </Modal>
);

export default RetentionFormModal;
