import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon, ArchiveBoxIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI } from "../../services/api";
import { EmptyState } from "../../styles/components";
import { PageContainer, PageHeader } from "../../layouts";
import RetentionPolicyCard from "./RetentionPolicyCard";
import RetentionFormModal from "./RetentionFormModal";
import RetentionConfirmDialog from "./RetentionConfirmDialog";

const INITIAL_FORM = {
  policy_type: "scan_results",
  retention_days: 365,
  action: "archive",
  enabled: true,
  compliance_requirement: "",
};

const DataRetentionPolicies = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const {
    data: policiesData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["retentionPolicies"],
    queryFn: () => enterpriseAPI.getRetentionPolicies(),
  });

  const createPolicyMutation = useMutation({
    mutationFn: enterpriseAPI.createRetentionPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["retentionPolicies"] });
      toast.success("Retention policy created successfully");
      setShowCreateModal(false);
      setFormData(INITIAL_FORM);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to create policy");
    },
  });

  const updatePolicyMutation = useMutation({
    mutationFn: ({ id, data }) => enterpriseAPI.updateRetentionPolicy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["retentionPolicies"] });
      toast.success("Retention policy updated successfully");
      setEditingPolicy(null);
      setShowCreateModal(false);
      setFormData(INITIAL_FORM);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to update policy");
    },
  });

  const deletePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.deleteRetentionPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["retentionPolicies"] });
      toast.success("Retention policy deleted successfully");
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to delete policy");
    },
  });

  const executePolicyMutation = useMutation({
    mutationFn: enterpriseAPI.executeRetentionPolicy,
    onSuccess: (data) => {
      toast.success(`Policy executed: ${data.items_processed} items processed`);
      queryClient.invalidateQueries({ queryKey: ["retentionPolicies"] });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to execute policy");
    },
  });

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

  const closeModal = () => {
    setShowCreateModal(false);
    setEditingPolicy(null);
    setFormData(INITIAL_FORM);
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        <PageHeader
          title="Data Retention Policies"
          description="Automated data lifecycle management with compliance support"
          icon={ArchiveBoxIcon}
          breadcrumb={["Data Retention"]}
          actions={
            <button
              onClick={() => {
                setEditingPolicy(null);
                setFormData(INITIAL_FORM);
                setShowCreateModal(true);
              }}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white text-sm lg:text-base font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              <PlusIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Create Policy</span>
            </button>
          }
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {isError ? (
            <div className="col-span-2 p-12 text-center">
              <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
              </div>
              <p className="text-gray-400 mb-4">Failed to load retention policies</p>
              <button
                type="button"
                onClick={() => refetch()}
                className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                Try Again
              </button>
            </div>
          ) : isLoading ? (
            <div className="col-span-2 p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
              <p className="text-gray-400">Loading retention policies...</p>
            </div>
          ) : !policiesData?.policies?.length ? (
            <div className="col-span-2">
              <EmptyState
                icon={<ArchiveBoxIcon className="h-12 w-12" />}
                title="No retention policies found"
                description="Create your first policy to get started"
              />
            </div>
          ) : (
            policiesData.policies.map((policy) => (
              <RetentionPolicyCard
                key={policy.id}
                policy={policy}
                onExecute={handleExecute}
                onEdit={handleEdit}
                onDelete={handleDelete}
                isExecuting={executePolicyMutation.isPending}
                isDeleting={deletePolicyMutation.isPending}
              />
            ))
          )}
        </div>

        <RetentionFormModal
          isOpen={showCreateModal}
          onClose={closeModal}
          formData={formData}
          setFormData={setFormData}
          editingPolicy={editingPolicy}
          onSubmit={handleSubmit}
          isPending={createPolicyMutation.isPending || updatePolicyMutation.isPending}
        />

        <RetentionConfirmDialog
          confirmDialog={confirmDialog}
          onClose={() => setConfirmDialog(null)}
        />
      </div>
    </PageContainer>
  );
};

export default DataRetentionPolicies;
