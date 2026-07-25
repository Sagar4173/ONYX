/**
 * AdvancedCompliance Component - Multi-Framework Compliance Dashboard
 * Comprehensive compliance assessments for SOX, HIPAA, ISO 27001, PCI DSS, GDPR, SOC2, NIST, CIS, OWASP
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ShieldCheckIcon,
  XCircleIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  EyeIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI, projectsAPI } from "../../services/api";
import { Button, Card, EmptyState, Modal } from "../../styles/components";
import { PageContainer, PageHeader} from "../../layouts";

const AdvancedCompliance = () => {
  const queryClient = useQueryClient();
  const [selectedFramework, setSelectedFramework] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [formData, setFormData] = useState({
    project_id: "",
    frameworks: []});

  // Compliance frameworks
  const frameworks = [
    {
      id: "sox",
      name: "SOX",
      fullName: "Sarbanes-Oxley Act",
      description: "Financial reporting and internal controls",
      color: "from-blue-500 to-cyan-500",
      icon: "💼"},
    {
      id: "hipaa",
      name: "HIPAA",
      fullName: "Health Insurance Portability and Accountability Act",
      description: "Healthcare data privacy and security",
      color: "from-green-500 to-emerald-500",
      icon: "🏥"},
    {
      id: "iso27001",
      name: "ISO 27001",
      fullName: "ISO/IEC 27001",
      description: "Information security management",
      color: "from-purple-500 to-pink-500",
      icon: "🔒"},
    {
      id: "pci_dss",
      name: "PCI DSS",
      fullName: "Payment Card Industry Data Security Standard",
      description: "Payment card data protection",
      color: "from-orange-500 to-red-500",
      icon: "💳"},
    {
      id: "gdpr",
      name: "GDPR",
      fullName: "General Data Protection Regulation",
      description: "EU data protection and privacy",
      color: "from-blue-500 to-indigo-500",
      icon: "🇪🇺"},
    {
      id: "soc2",
      name: "SOC 2",
      fullName: "Service Organization Control 2",
      description: "Service provider security controls",
      color: "from-teal-500 to-cyan-500",
      icon: "🛡️"},
    {
      id: "nist",
      name: "NIST",
      fullName: "NIST Cybersecurity Framework",
      description: "Risk-based cybersecurity guidance",
      color: "from-indigo-500 to-purple-500",
      icon: "🔐"},
    {
      id: "cis",
      name: "CIS",
      fullName: "CIS Controls",
      description: "Cybersecurity best practices",
      color: "from-yellow-500 to-orange-500",
      icon: "⚡"},
    {
      id: "owasp",
      name: "OWASP",
      fullName: "OWASP Top 10",
      description: "Web application security risks",
      color: "from-red-500 to-pink-500",
      icon: "🌐"},
  ];

  // Fetch assessments
  const { data: assessmentsData, isLoading, isError, refetch } = useQuery({
    queryKey: ["complianceAssessments", selectedFramework],
    queryFn: () =>
      enterpriseAPI.getComplianceAssessments({
        framework: selectedFramework !== "all" ? selectedFramework : undefined})});

  // Fetch projects for dropdown
  const { data: projectsData } = useQuery({
    queryKey: ["projectsList"],
    queryFn: () => projectsAPI.getProjects({ limit: 100 }),
  });

  // Fetch framework summary
  const { data: summaryData, isError: summaryError } = useQuery({
    queryKey: ["complianceFrameworkSummary"],
    queryFn: () => enterpriseAPI.getComplianceFrameworkSummary()});

  // Create assessment mutation
  const createAssessmentMutation = useMutation({
    mutationFn: enterpriseAPI.createComplianceAssessment,
    onSuccess: () => {
      queryClient.invalidateQueries(["complianceAssessments"]);
      queryClient.invalidateQueries(["complianceFrameworkSummary"]);
      toast.success("Compliance assessment started");
      setShowCreateModal(false);
      resetForm();
    },
    onError: (error) => {
      toast.error(
        error.response?.data?.detail || "Failed to create assessment"
      );
    }});

  // Export assessment mutation
  const exportAssessmentMutation = useMutation({
    mutationFn: enterpriseAPI.exportComplianceReport,
    onSuccess: (data, variables) => {
      // Create download
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json"});
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
    onError: (error) => {
      toast.error("Failed to export report");
    }});

  const resetForm = () => {
    setFormData({
      project_id: "",
      frameworks: []});
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    createAssessmentMutation.mutate(formData);
  };

  const getScoreColor = (score) => {
    if (score >= 90) return "text-green-400 bg-green-500/20";
    if (score >= 70) return "text-yellow-400 bg-yellow-500/20";
    if (score >= 50) return "text-orange-400 bg-orange-500/20";
    return "text-red-400 bg-red-500/20";
  };

  const getScoreGradient = (score) => {
    if (score >= 90) return "from-green-500 to-emerald-500";
    if (score >= 70) return "from-yellow-500 to-orange-500";
    if (score >= 50) return "from-orange-500 to-red-500";
    return "from-red-500 to-pink-500";
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? "N/A" : date.toLocaleString();
  };

  const getFrameworkInfo = (frameworkId) => {
    return frameworks.find((f) => f.id === frameworkId);
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <PageHeader
          title="Advanced Compliance"
          description="Multi-framework compliance assessments and reporting"
          icon={ShieldCheckIcon}
          breadcrumb={["Compliance"]}
          actions={
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all"
            >
              <PlusIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>New Assessment</span>
            </button>
          }
        />

        {/* Framework Filter */}
        <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-xl lg:rounded-2xl p-3 lg:p-4 shadow-xl mb-8">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedFramework("all")}
              className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all ${
                selectedFramework === "all"
                  ? "bg-purple-500 text-white"
                  : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
              }`}
            >
              All Frameworks
            </button>
            {frameworks.map((framework) => (
              <button
                key={framework.id}
                onClick={() => setSelectedFramework(framework.id)}
                className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all ${
                  selectedFramework === framework.id
                    ? `bg-gradient-to-r ${framework.color} text-white`
                    : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
                }`}
              >
                {framework.icon} {framework.name}
              </button>
            ))}
          </div>
        </div>

        {/* Framework Summary Cards */}
        {summaryData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {frameworks.slice(0, 3).map((framework) => {
              const summary = summaryData.frameworks?.find(
                (f) => f.framework === framework.id
              );
              return (
                <Card
                  key={framework.id}
                  padding="lg"
                  className="shadow-xl"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{framework.icon}</span>
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {framework.name}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {summary?.total_assessments || 0} assessments
                        </p>
                      </div>
                    </div>
                  </div>
                  {summary && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Avg Score:</span>
                        <span
                          className={`font-semibold ${
                            summary.average_score >= 70
                              ? "text-green-400"
                              : "text-yellow-400"
                          }`}
                        >
                          {summary.average_score?.toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700/50 rounded-full h-2">
                        <div
                          className={`bg-gradient-to-r ${getScoreGradient(
                            summary.average_score
                          )} h-2 rounded-full transition-all`}
                          style={{ width: `${summary.average_score}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}

        {/* Assessments List */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl shadow-xl overflow-hidden">
          <div className="p-6 border-b border-gray-700/50">
            <h2 className="text-xl font-semibold text-white">
              Compliance Assessments
            </h2>
          </div>

          {isError ? (
            <div className="p-12 text-center">
              <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
              </div>
              <p className="text-gray-400 mb-4">Failed to load assessments</p>
              <button type="button" onClick={() => refetch()}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-500 hover:to-blue-600 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
                Try Again
              </button>
            </div>
          ) : isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading assessments...</p>
            </div>
          ) : assessmentsData?.assessments?.length === 0 ? (
            <EmptyState
              icon={<ShieldCheckIcon className="h-12 w-12" />}
              title="No assessments found"
              description="Create your first compliance assessment"
            />
          ) : (
            <div className="divide-y divide-gray-700/50">
              {assessmentsData?.assessments?.map((assessment) => (
                <div
                  key={assessment.id}
                  className="p-6 hover:bg-gray-800/30 transition-colors"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          Project: {assessment.project_id}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            assessment.status === "completed"
                              ? "bg-green-500/20 text-green-400"
                              : assessment.status === "in_progress"
                              ? "bg-yellow-500/20 text-yellow-400"
                              : "bg-gray-500/20 text-gray-400"
                          }`}
                        >
                          {assessment.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400">
                        Assessed: {formatDate(assessment.assessment_date)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedAssessment(assessment)}
                        className="p-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 rounded-lg text-blue-400 transition-all"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() =>
                          exportAssessmentMutation.mutate({
                            assessmentId: assessment.id})
                        }
                        className="p-2 bg-green-500/20 hover:bg-green-500/30 border border-green-500/30 rounded-lg text-green-400 transition-all"
                      >
                        <ArrowDownTrayIcon className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Framework Results */}
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {assessment.framework_results?.map((result) => {
                      const frameworkInfo = getFrameworkInfo(result.framework);
                      return (
                        <Card
                          key={result.framework}
                          className="bg-gray-800/30"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">
                              {frameworkInfo?.icon}
                            </span>
                            <span className="text-sm font-medium text-white">
                              {frameworkInfo?.name}
                            </span>
                          </div>
                          <div className="flex items-end justify-between">
                            <div>
                              <p
                                className={`text-2xl font-bold ${
                                  result.score >= 70
                                    ? "text-green-400"
                                    : "text-yellow-400"
                                }`}
                              >
                                {result.score?.toFixed(0)}%
                              </p>
                              <p className="text-xs text-gray-400">
                                {result.passed_controls}/{result.total_controls}{" "}
                                controls
                              </p>
                            </div>
                            <div className="w-12 h-12">
                              <svg
                                className="transform -rotate-90"
                                viewBox="0 0 36 36"
                              >
                                <path
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke="rgba(255,255,255,0.1)"
                                  strokeWidth="3"
                                />
                                <path
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                  fill="none"
                                  stroke={
                                    result.score >= 70 ? "#4ade80" : "#fbbf24"
                                  }
                                  strokeWidth="3"
                                  strokeDasharray={`${result.score}, 100`}
                                />
                              </svg>
                            </div>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Assessment Details Modal */}
        {selectedAssessment && (
          <Modal size="xl" isOpen={!!selectedAssessment} onClose={() => setSelectedAssessment(null)} title="Assessment Details">
            {/* Assessment Info */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-800/30 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Project ID</p>
                <p className="text-lg font-semibold text-white">
                  {selectedAssessment.project_id}
                </p>
              </div>
              <div className="bg-gray-800/30 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Status</p>
                <p className="text-lg font-semibold text-white capitalize">
                  {selectedAssessment.status}
                </p>
              </div>
              <div className="bg-gray-800/30 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Overall Score</p>
                <p className={`text-2xl font-bold ${selectedAssessment.overall_score >= 70 ? "text-green-400" : "text-yellow-400"}`}>
                  {selectedAssessment.overall_score?.toFixed(1)}%
                </p>
              </div>
              <div className="bg-gray-800/30 rounded-xl p-4">
                <p className="text-sm text-gray-400 mb-1">Assessment Date</p>
                <p className="text-sm font-medium text-white">
                  {formatDate(selectedAssessment.assessment_date)}
                </p>
              </div>
            </div>

            {/* Framework Results Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Framework Results</h3>
              {selectedAssessment.framework_results?.map((result) => {
                const frameworkInfo = getFrameworkInfo(result.framework);
                return (
                  <Card key={result.framework} className="bg-gray-800/30">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{frameworkInfo?.icon}</span>
                        <div>
                          <h4 className="font-semibold text-white">{frameworkInfo?.name}</h4>
                          <p className="text-sm text-gray-400">{frameworkInfo?.fullName}</p>
                        </div>
                      </div>
                      <div className={`px-4 py-2 rounded-lg ${getScoreColor(result.score)}`}>
                        <p className="text-2xl font-bold">{result.score?.toFixed(0)}%</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-400">{result.passed_controls}</p>
                        <p className="text-xs text-gray-400">Passed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-400">{result.failed_controls}</p>
                        <p className="text-xs text-gray-400">Failed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-400">{result.total_controls}</p>
                        <p className="text-xs text-gray-400">Total</p>
                      </div>
                    </div>

                    {result.recommendations?.length > 0 && (
                      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                        <p className="text-sm font-medium text-yellow-400 mb-2">Recommendations</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          {result.recommendations.slice(0, 3).map((rec, idx) => (
                            <li key={idx}>• {rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          </Modal>
        )}

        {/* Create Assessment Modal */}
        {showCreateModal && (
          <Modal
            size="lg"
            isOpen={showCreateModal}
            onClose={() => { setShowCreateModal(false); resetForm(); }}
            title="Create Compliance Assessment"
            footer={
              <>
                <Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" form="assessment-form" gradient isLoading={createAssessmentMutation.isPending} disabled={formData.frameworks.length === 0}>
                  Start Assessment
                </Button>
              </>
            }
          >
            <form id="assessment-form" onSubmit={handleSubmit} className="space-y-6">
              {/* Project Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Select Project *
                </label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none cursor-pointer"
                  required
                >
                  <option value="" disabled className="bg-gray-800 text-gray-400">
                    Choose a project...
                  </option>
                  {(projectsData?.projects || []).map((project) => (
                    <option key={project.id || project._id} value={project.id || project._id} className="bg-gray-800 text-white">
                      {project.name}{project.repository?.url ? ` — ${project.repository.url}` : ""}
                    </option>
                  ))}
                </select>
                {(!projectsData?.projects || projectsData.projects.length === 0) && (
                  <p className="mt-2 text-xs text-yellow-400">
                    No projects found. Create a project first to run compliance assessments.
                  </p>
                )}
              </div>

              {/* Frameworks */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Select Frameworks *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {frameworks.map((framework) => (
                    <button
                      key={framework.id}
                      type="button"
                      onClick={() => {
                        const newFrameworks = formData.frameworks.includes(framework.id)
                          ? formData.frameworks.filter((f) => f !== framework.id)
                          : [...formData.frameworks, framework.id];
                        setFormData({ ...formData, frameworks: newFrameworks });
                      }}
                      className={`p-4 border rounded-xl text-left transition-all ${
                        formData.frameworks.includes(framework.id)
                          ? `bg-gradient-to-r ${framework.color} border-transparent`
                          : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-700/50"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xl">{framework.icon}</span>
                        <span className="font-medium text-white">{framework.name}</span>
                      </div>
                      <p className="text-xs text-gray-300 opacity-80">{framework.description}</p>
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-sm text-gray-400">Select at least one framework for assessment</p>
              </div>
            </form>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
};

export default AdvancedCompliance;
