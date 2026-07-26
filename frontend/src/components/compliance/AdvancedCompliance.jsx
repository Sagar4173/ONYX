import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheckIcon, PlusIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI, projectsAPI } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";
import FrameworkFilter from "./FrameworkFilter";
import FrameworkSummaryCards from "./FrameworkSummaryCards";
import AssessmentsList from "./AssessmentsList";
import AssessmentDetailModal from "./AssessmentDetailModal";
import CreateAssessmentModal from "./CreateAssessmentModal";

const AdvancedCompliance = () => {
  const queryClient = useQueryClient();
  const [selectedFramework, setSelectedFramework] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [formData, setFormData] = useState({ project_id: "", frameworks: [] });

  const {
    data: assessmentsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["complianceAssessments", selectedFramework],
    queryFn: () =>
      enterpriseAPI.getComplianceAssessments({
        framework: selectedFramework !== "all" ? selectedFramework : undefined,
      }),
  });

  const { data: projectsData } = useQuery({
    queryKey: ["projectsList"],
    queryFn: () => projectsAPI.getProjects({ limit: 100 }),
  });

  const { data: summaryData } = useQuery({
    queryKey: ["complianceFrameworkSummary"],
    queryFn: () => enterpriseAPI.getComplianceFrameworkSummary(),
  });

  const createAssessmentMutation = useMutation({
    mutationFn: enterpriseAPI.createComplianceAssessment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["complianceAssessments"] });
      queryClient.invalidateQueries({ queryKey: ["complianceFrameworkSummary"] });
      toast.success("Compliance assessment started");
      setShowCreateModal(false);
      setFormData({ project_id: "", frameworks: [] });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Failed to create assessment");
    },
  });

  const exportAssessmentMutation = useMutation({
    mutationFn: enterpriseAPI.exportComplianceReport,
    onSuccess: (data, variables) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compliance-report-${variables.assessmentId}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Compliance report exported");
    },
    onError: () => {
      toast.error("Failed to export report");
    },
  });

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        <PageHeader
          title="Advanced Compliance"
          description="Multi-framework compliance assessments and reporting"
          icon={ShieldCheckIcon}
          breadcrumb={["Compliance"]}
          actions={
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              <PlusIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>New Assessment</span>
            </button>
          }
        />

        <FrameworkFilter
          selectedFramework={selectedFramework}
          setSelectedFramework={setSelectedFramework}
        />
        <FrameworkSummaryCards summaryData={summaryData} />

        <AssessmentsList
          assessmentsData={assessmentsData}
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          onViewAssessment={setSelectedAssessment}
          onExportAssessment={(assessmentId) => exportAssessmentMutation.mutate({ assessmentId })}
          selectedFramework={selectedFramework}
        />

        <AssessmentDetailModal
          assessment={selectedAssessment}
          onClose={() => setSelectedAssessment(null)}
        />

        <CreateAssessmentModal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false);
            setFormData({ project_id: "", frameworks: [] });
          }}
          formData={formData}
          setFormData={setFormData}
          projectsData={projectsData}
          onSubmit={(e) => {
            e.preventDefault();
            createAssessmentMutation.mutate(formData);
          }}
          isPending={createAssessmentMutation.isPending}
        />
      </div>
    </PageContainer>
  );
};

export default AdvancedCompliance;
