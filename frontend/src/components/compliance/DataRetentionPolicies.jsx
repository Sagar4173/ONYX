/**
 * DataRetentionPolicies Component - Enterprise Data Lifecycle Management
 * CRUD interface for retention policies with compliance support
 */
import React, { useState } from "react";
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
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI } from "../../services/api";

const DataRetentionPolicies = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [formData, setFormData] = useState({
    policy_type: "scan_results",
    retention_days: 365,
    action: "archive",
    enabled: true,
    compliance_requirement: "",
  });

  // Policy types
  const policyTypes = [
    { value: "scan_results", label: "Scan Results", icon: DocumentTextIcon },
    { value: "audit_logs", label: "Audit Logs", icon: ShieldCheckIcon },
    { value: "user_data", label: "User Data", icon: "👤" },
    { value: "reports", label: "Reports", icon: FolderIcon },
    {
      value: "vulnerability_data",
      label: "Vulnerability Data",
      icon: ExclamationTriangleIcon,
    },
    {
      value: "compliance_records",
      label: "Compliance Records",
      icon: CheckCircleIcon,
    },
    { value: "backup_data", label: "Backup Data", icon: ArchiveBoxIcon },
  ];

  // Retention actions
  const retentionActions = [
    {
      value: "delete",
      label: "Delete",
      color: "text-red-400",
      description: "Permanently delete data",
    },
    {
      value: "archive",
      label: "Archive",
      color: "text-blue-400",
      description: "Move to archive storage",
    },
    {
      value: "compress",
      label: "Compress",
      color: "text-green-400",
      description: "Compress and store",
    },
    {
      value: "anonymize",
      label: "Anonymize",
      color: "text-yellow-400",
      description: "Remove PII and retain",
    },
  ];

  // Fetch policies
  const { data: policiesData, isLoading } = useQuery({
    queryKey: ["retentionPolicies"],
    queryFn: () => enterpriseAPI.getRetentionPolicies(),
  });

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
    },
  });

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
    },
  });

  // Delete policy mutation
  const deletePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.deleteRetentionPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries(["retentionPolicies"]);
      toast.success("Retention policy deleted successfully");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete policy");
    },
  });

  // Execute policy mutation
  const executePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.executeRetentionPolicy,
    onSuccess: (data) => {
      toast.success(`Policy executed: ${data.items_processed} items processed`);
      queryClient.invalidateQueries(["retentionPolicies"]);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to execute policy");
    },
  });

  const resetForm = () => {
    setFormData({
      policy_type: "scan_results",
      retention_days: 365,
      action: "archive",
      enabled: true,
      compliance_requirement: "",
    });
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
      compliance_requirement: policy.compliance_requirement || "",
    });
    setShowCreateModal(true);
  };

  const handleDelete = (policyId) => {
    if (
      window.confirm("Are you sure you want to delete this retention policy?")
    ) {
      deletePolicyMutation.mutate(policyId);
    }
  };

  const handleExecute = (policyId) => {
    if (window.confirm("Execute this retention policy now?")) {
      executePolicyMutation.mutate(policyId);
    }
  };

  const getActionColor = (action) => {
    const actionConfig = retentionActions.find((a) => a.value === action);
    return actionConfig?.color || "text-gray-400";
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 lg:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div className="flex items-center gap-3 lg:gap-4">
              <div className="p-2.5 lg:p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl lg:rounded-2xl shadow-lg flex-shrink-0">
                <ArchiveBoxIcon className="w-6 h-6 lg:w-8 lg:h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl lg:text-4xl font-bold text-white mb-1 lg:mb-2">
                  Data Retention Policies
                </h1>
                <p className="text-sm lg:text-base text-gray-400">
                  Automated data lifecycle management with compliance support
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setEditingPolicy(null);
                resetForm();
                setShowCreateModal(true);
              }}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all w-fit"
            >
              <PlusIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Create Policy</span>
            </button>
          </div>
        </div>

        {/* Policies Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {isLoading ? (
            <div className="col-span-2 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading retention policies...</p>
            </div>
          ) : policiesData?.policies?.length === 0 ? (
            <div className="col-span-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center">
              <ArchiveBoxIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400 text-lg mb-2">
                No retention policies found
              </p>
              <p className="text-gray-500 text-sm">
                Create your first policy to get started
              </p>
            </div>
          ) : (
            policiesData?.policies?.map((policy) => (
              <div
                key={policy.id}
                className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all"
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
                <div className="flex gap-2 pt-4 border-t border-white/10">
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
              </div>
            ))
          )}
        </div>

        {/* Create/Edit Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    {editingPolicy ? "Edit" : "Create"} Retention Policy
                  </h2>
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      setEditingPolicy(null);
                      resetForm();
                    }}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                  >
                    <XCircleIcon className="w-6 h-6 text-gray-400" />
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Policy Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Policy Type *
                    </label>
                    <select
                      value={formData.policy_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          policy_type: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      {policyTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Retention Days */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Retention Period (Days) *
                    </label>
                    <input
                      type="number"
                      value={formData.retention_days}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          retention_days: parseInt(e.target.value),
                        })
                      }
                      min="1"
                      max="3650"
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                    <p className="mt-2 text-sm text-gray-400">
                      Common periods: 30 days, 90 days, 1 year (365), 7 years
                      (2555)
                    </p>
                  </div>

                  {/* Action */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Retention Action *
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {retentionActions.map((action) => (
                        <button
                          key={action.value}
                          type="button"
                          onClick={() =>
                            setFormData({ ...formData, action: action.value })
                          }
                          className={`p-4 border rounded-xl text-left transition-all ${
                            formData.action === action.value
                              ? "bg-blue-500/20 border-blue-500/50"
                              : "bg-white/5 border-white/10 hover:bg-white/10"
                          }`}
                        >
                          <p className={`font-medium ${action.color}`}>
                            {action.label}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {action.description}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Compliance Requirement */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Compliance Requirement (Optional)
                    </label>
                    <input
                      type="text"
                      value={formData.compliance_requirement}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          compliance_requirement: e.target.value,
                        })
                      }
                      placeholder="e.g., SOX, HIPAA, GDPR"
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Enabled Toggle */}
                  <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div>
                      <p className="font-medium text-white">Enable Policy</p>
                      <p className="text-sm text-gray-400">
                        Activate this retention policy immediately
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.enabled}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            enabled: e.target.checked,
                          })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                    </label>
                  </div>

                  {/* Form Actions */}
                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateModal(false);
                        setEditingPolicy(null);
                        resetForm();
                      }}
                      className="flex-1 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium transition-all"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={
                        createPolicyMutation.isLoading ||
                        updatePolicyMutation.isLoading
                      }
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 rounded-xl text-white font-semibold shadow-lg transition-all disabled:opacity-50"
                    >
                      {editingPolicy ? "Update" : "Create"} Policy
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataRetentionPolicies;
