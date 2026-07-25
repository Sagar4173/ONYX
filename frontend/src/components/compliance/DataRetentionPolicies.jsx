/**
 * DataRetentionPolicies Component - Enterprise Data Lifecycle Management
 * CRUD interface for retention policies with compliance support
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ClockIcon,
  TrashIcon,
  PencilIcon,
  PlusIcon,
  ArchiveBoxIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  FolderIcon,
  ShieldCheckIcon,
  ArrowPathIcon} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI } from "../../services/api";
import { Button, Card, EmptyState, Modal, ConfirmDialog } from "../../styles/components";
import { PageContainer, PageHeader} from "../../layouts";

const DataRetentionPolicies = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [formData, setFormData] = useState({
    policy_type: "scan_results",
    retention_days: 365,
    action: "archive",
    enabled: true,
    compliance_requirement: ""});

  // Policy types
  const policyTypes = [
    { value: "scan_results", label: "Scan Results", icon: DocumentTextIcon },
    { value: "audit_logs", label: "Audit Logs", icon: ShieldCheckIcon },
    { value: "user_data", label: "User Data", icon: "👤" },
    { value: "reports", label: "Reports", icon: FolderIcon },
    {
      value: "vulnerability_data",
      label: "Vulnerability Data",
      icon: ExclamationTriangleIcon},
    {
      value: "compliance_records",
      label: "Compliance Records",
      icon: CheckCircleIcon},
    { value: "backup_data", label: "Backup Data", icon: ArchiveBoxIcon },
  ];

  // Retention actions
  const retentionActions = [
    {
      value: "delete",
      label: "Delete",
      color: "text-red-400",
      description: "Permanently delete data"},
    {
      value: "archive",
      label: "Archive",
      color: "text-blue-400",
      description: "Move to archive storage"},
    {
      value: "compress",
      label: "Compress",
      color: "text-green-400",
      description: "Compress and store"},
    {
      value: "anonymize",
      label: "Anonymize",
      color: "text-yellow-400",
      description: "Remove PII and retain"},
  ];

  // Fetch policies
  const { data: policiesData, isLoading, isError, refetch } = useQuery({
    queryKey: ["retentionPolicies"],
    queryFn: () => enterpriseAPI.getRetentionPolicies()});

  // Create policy mutation
  const createPolicyMutation = useMutation({
    mutationFn: enterpriseAPI.createRetentionPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries(["retentionPolicies"]);
      toast.success("Retention policy created successfully");
      setShowCreateModal(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to create policy");
    }});

  // Update policy mutation
  const updatePolicyMutation = useMutation({
    mutationFn: ({ id, data }) => enterpriseAPI.updateRetentionPolicy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(["retentionPolicies"]);
      toast.success("Retention policy updated successfully");
      setEditingPolicy(null);
      resetForm();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update policy");
    }});

  // Delete policy mutation
  const deletePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.deleteRetentionPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries(["retentionPolicies"]);
      toast.success("Retention policy deleted successfully");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete policy");
    }});

  // Execute policy mutation
  const executePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.executeRetentionPolicy,
    onSuccess: (data) => {
      toast.success(`Policy executed: ${data.items_processed} items processed`);
      queryClient.invalidateQueries(["retentionPolicies"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to execute policy");
    }});

  const resetForm = () => {
    setFormData({
      policy_type: "scan_results",
      retention_days: 365,
      action: "archive",
      enabled: true,
      compliance_requirement: ""});
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editingPolicy) {
      updatePolicyMutation.mutate({ id: editingPolicy.id, data: formData });
    } else {
      createPolicyMutation.mutate(formData);
    }
  };

  const handleEdit = (policy) => {
    setEditingPolicy(policy);
    setFormData({
      policy_type: policy.policy_type,
      retention_days: policy.retention_days,
      action: policy.action,
      enabled: policy.enabled,
      compliance_requirement: policy.compliance_requirement || ""});
    setShowCreateModal(true);
  };

  const [confirmDialog, setConfirmDialog] = useState(null);

  const handleDelete = (policyId) => {
    setConfirmDialog({
      title: "Delete Policy",
      message: "Are you sure you want to delete this retention policy?",
      onConfirm: () => deletePolicyMutation.mutate(policyId),
    });
  };

  const handleExecute = (policyId) => {
    setConfirmDialog({
      title: "Execute Policy",
      message: "Execute this retention policy now?",
      onConfirm: () => executePolicyMutation.mutate(policyId),
    });
  };

  const getActionColor = (action) => {
    const actionConfig = retentionActions.find((a) => a.value === action);
    return actionConfig?.color || "text-gray-400";
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Data Retention Policies"
          description="Automated data lifecycle management with compliance support"
          icon={ArchiveBoxIcon}
          breadcrumb={["Data Retention"]}
          actions={
            <button
              onClick={() => {
                setEditingPolicy(null);
                resetForm();
                setShowCreateModal(true);
              }}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all"
            >
              <PlusIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Create Policy</span>
            </button>
          }
        />

        {/* Policies Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {isError ? (
            <div className="col-span-2 p-12 text-center">
              <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
              </div>
              <p className="text-gray-400 mb-4">Failed to load retention policies</p>
              <button type="button" onClick={() => refetch()}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-500 hover:to-blue-600 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
                Try Again
              </button>
            </div>
          ) : isLoading ? (
            <div className="col-span-2 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading retention policies...</p>
            </div>
          ) : policiesData?.policies?.length === 0 ? (
            <div className="col-span-2">
              <EmptyState
                icon={<ArchiveBoxIcon className="h-12 w-12" />}
                title="No retention policies found"
                description="Create your first policy to get started"
              />
            </div>
          ) : (
            policiesData?.policies?.map((policy) => (
              <Card
                key={policy.id}
                padding="lg"
                className="shadow-xl hover:shadow-2xl transition-all"
              >
                {/* Policy Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <FolderIcon className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">
                        {policy.policy_type.replace(/_/g, " ").toUpperCase()}
                      </h3>
                      <p className="text-sm text-gray-400">
                        Retain for {policy.retention_days} days
                      </p>
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

                {/* Policy Details */}
                <div className="space-y-3 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Action:</span>
                    <span
                      className={`text-sm font-medium ${getActionColor(
                        policy.action
                      )}`}
                    >
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
                    <span className="text-sm text-gray-300">
                      {formatDate(policy.created_at)}
                    </span>
                  </div>
                  {policy.last_executed && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-400">
                        Last Executed:
                      </span>
                      <span className="text-sm text-gray-300">
                        {formatDate(policy.last_executed)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Policy Actions */}
                <div className="flex gap-2 pt-4 border-t border-gray-700/50">
                  <button
                    onClick={() => handleExecute(policy.id)}
                    disabled={executePolicyMutation.isLoading}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded-lg text-green-400 font-medium transition-all disabled:opacity-50"
                  >
                    <ArrowPathIcon className="w-4 h-4" />
                    Execute
                  </button>
                  <button
                    onClick={() => handleEdit(policy)}
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg text-blue-400 transition-all"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(policy.id)}
                    disabled={deletePolicyMutation.isLoading}
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg text-red-400 transition-all disabled:opacity-50"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* Create/Edit Modal */}
        {showCreateModal && (
          <Modal
            isOpen={showCreateModal}
            onClose={() => { setShowCreateModal(false); setEditingPolicy(null); resetForm(); }}
            title={`${editingPolicy ? "Edit" : "Create"} Retention Policy`}
            size="lg"
            footer={
              <>
                <Button variant="ghost" onClick={() => { setShowCreateModal(false); setEditingPolicy(null); resetForm(); }}>Cancel</Button>
                <Button type="submit" form="retention-form" gradient isLoading={createPolicyMutation.isLoading || updatePolicyMutation.isLoading}>
                  {editingPolicy ? "Update" : "Create"} Policy
                </Button>
              </>
            }
          >
            <form id="retention-form" onSubmit={handleSubmit} className="space-y-6">
              {/* Policy Type */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Policy Type *</label>
                <select
                  value={formData.policy_type}
                  onChange={(e) => setFormData({ ...formData, policy_type: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 [&>option]:bg-gray-800 [&>option]:text-white"
                  required
                >
                  {policyTypes.map((type) => (
                    <option key={type.value} value={type.value} className="bg-gray-800 text-white">{type.label}</option>
                  ))}
                </select>
              </div>

              {/* Retention Days */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Retention Period (Days) *</label>
                <input
                  type="number"
                  value={formData.retention_days}
                  onChange={(e) => setFormData({ ...formData, retention_days: parseInt(e.target.value) })}
                  min="1"
                  max="3650"
                  className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                  required
                />
                <p className="mt-2 text-sm text-gray-400">Common periods: 30 days, 90 days, 1 year (365), 7 years (2555)</p>
              </div>

              {/* Action */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Retention Action *</label>
                <div className="grid grid-cols-2 gap-3">
                  {retentionActions.map((action) => (
                    <button
                      key={action.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, action: action.value })}
                      className={`p-4 border rounded-xl text-left transition-all ${
                        formData.action === action.value
                          ? "bg-blue-500/20 border-blue-500/50"
                          : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-700/50"
                      }`}
                    >
                      <p className={`font-medium ${action.color}`}>{action.label}</p>
                      <p className="text-xs text-gray-400 mt-1">{action.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Compliance Requirement */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Compliance Requirement (Optional)</label>
                <input
                  type="text"
                  value={formData.compliance_requirement}
                  onChange={(e) => setFormData({ ...formData, compliance_requirement: e.target.value })}
                  placeholder="e.g., SOX, HIPAA, GDPR"
                  className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                />
              </div>

              {/* Enabled Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-800/30 border border-gray-700/50 rounded-xl">
                <div>
                  <p className="font-medium text-white">Enable Policy</p>
                  <p className="text-sm text-gray-400">Activate this retention policy immediately</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" checked={formData.enabled} onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })} className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                </label>
              </div>
            </form>
          </Modal>
        )}

        {confirmDialog && (
          <ConfirmDialog
            isOpen={true}
            onClose={() => setConfirmDialog(null)}
            onConfirm={confirmDialog.onConfirm}
            title={confirmDialog.title}
            message={confirmDialog.message}
            confirmLabel="Delete"
            variant="danger"
          />
        )}
      </div>
    </PageContainer>
  );
};

export default DataRetentionPolicies;
