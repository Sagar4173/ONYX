import { motion } from "framer-motion";
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon } from "@heroicons/react/24/outline";
import { toast } from "react-hot-toast";
import { Button } from "../../styles/components";
import { PageContainer, PageHeader } from "../../layouts/UIComponents";
import { projectsAPI } from "../../services/api";
import { UsersIcon } from "@heroicons/react/24/outline";
import ProjectStatsBar from "./ProjectStatsBar";
import ProjectFilters from "./ProjectFilters";
import ProjectGrid from "./ProjectGrid";
import ProjectForm from "./ProjectForm";
import ProjectDeleteDialog from "./ProjectDeleteDialog";

const ProjectManagement = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // View state
  const [viewMode, setViewMode] = useState("grid");

  // Filter + sort state
  const [filters, setFilters] = useState({ search: "", status: "", category: "", priority: "" });
  const [sort, setSort] = useState({ field: "name" });

  // Pagination state
  const [pagination, setPagination] = useState({ page: 1, perPage: 24 });

  // Selection
  const [selectedIds, setSelectedIds] = useState(new Set());

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [deletingProject, setDeletingProject] = useState(null);

  // Data
  const {
    data: projectsData,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: ["projects", filters, sort, pagination],
    queryFn: () =>
      projectsAPI
        .getProjects({
          ...filters,
          sort_by: sort.field,
          page: pagination.page,
          per_page: pagination.perPage,
        })
        .then((res) => res.data || res),
  });

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["projectAnalytics"],
    queryFn: () => projectsAPI.getAnalyticsOverview().then((res) => res.data || res),
  });

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: (id) => projectsAPI.deleteProject(id),
    onSuccess: () => {
      toast.success("Project deleted");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
      setDeletingProject(null);
    },
    onError: (err) => toast.error(err.message || "Failed to delete project"),
  });

  const bulkArchiveMutation = useMutation({
    mutationFn: (ids) =>
      Promise.all(ids.map((id) => projectsAPI.updateProject(id, { status: "archived" }))),
    onSuccess: () => {
      toast.success("Projects archived");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setSelectedIds(new Set());
    },
    onError: (err) => toast.error(err.message || "Failed to archive projects"),
  });

  const projects = projectsData?.projects ?? projectsData ?? [];
  const paginationInfo = projectsData?.pagination || {
    page: 1,
    perPage: 24,
    total: projects.length,
    totalPages: 1,
    has_more: false,
  };

  const handleView = useCallback(
    (project) => {
      if (project?.action === "create") {
        setShowCreateModal(true);
        return;
      }
      if (project?.id) navigate(`/project/${project.id}`);
    },
    [navigate]
  );

  const handleCreate = () => setShowCreateModal(true);
  const handleEdit = (project) => setEditingProject(project);
  const handleDelete = (project) => setDeletingProject(project);

  const handleFilterChange = (next) => {
    setFilters(next);
    setPagination((prev) => ({ ...prev, page: 1 }));
    setSelectedIds(new Set());
  };

  const handleSortChange = (next) => {
    setSort(next);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleBulkDelete = (ids) => {
    if (window.confirm(`Delete ${ids.size} selected projects?`)) {
      Promise.all([...ids].map((id) => projectsAPI.deleteProject(id)))
        .then(() => {
          toast.success(`Deleted ${ids.size} projects`);
          queryClient.invalidateQueries({ queryKey: ["projects"] });
          queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
          setSelectedIds(new Set());
        })
        .catch((err) => toast.error(err.message || "Failed to delete projects"));
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title="Projects"
        description="Manage your security scanning projects"
        icon={UsersIcon}
        breadcrumb={["Projects"]}
        actions={
          <Button
            variant="primary"
            gradient
            leftIcon={<PlusIcon className="w-5 h-5" />}
            onClick={handleCreate}
          >
            New Project
          </Button>
        }
      />

      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.08 } },
        }}
      >
        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <ProjectStatsBar analytics={analytics} isLoading={analyticsLoading} />
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <ProjectFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            sort={sort}
            onSortChange={handleSortChange}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            categories={templates?.categories}
            priorities={templates?.priorities}
            total={paginationInfo.total}
          />
        </motion.div>

        <motion.div
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <ProjectGrid
            projects={projects}
            viewMode={viewMode}
            pagination={paginationInfo}
            onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))}
            onPerPageChange={(perPage) => setPagination((prev) => ({ ...prev, perPage, page: 1 }))}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onView={handleView}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onBulkArchive={(ids) => bulkArchiveMutation.mutate([...ids])}
            onBulkDelete={handleBulkDelete}
            isLoading={isLoading}
            isFetching={isFetching}
            error={error}
            onRetry={refetch}
          />
        </motion.div>
      </motion.div>

      <ProjectForm
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        project={null}
        onSuccess={() => {
          setShowCreateModal(false);
        }}
      />

      {editingProject && (
        <ProjectForm
          isOpen={!!editingProject}
          onClose={() => setEditingProject(null)}
          project={editingProject}
          onSuccess={() => setEditingProject(null)}
        />
      )}

      <ProjectDeleteDialog
        project={deletingProject}
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={() => deleteMutation.mutate(deletingProject.id)}
        isLoading={deleteMutation.isPending}
      />
    </PageContainer>
  );
};

export default ProjectManagement;
