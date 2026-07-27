import { AnimatePresence } from "framer-motion";
import {
  FolderIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArchiveBoxIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { Button, Skeleton, EmptyState } from "../ui/StyleComponents";
import ProjectCard from "./ProjectCard";
import ProjectRow from "./ProjectRow";

const LoadingGrid = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="bg-gray-800/30 border border-gray-800/50 rounded-xl p-4 space-y-3">
        <Skeleton variant="title" className="!w-3/4" />
        <Skeleton variant="text" className="!w-full" />
        <Skeleton variant="text" className="!w-1/2" />
        <div className="flex items-center gap-2 pt-2">
          <Skeleton className="!w-12 !h-12 !rounded-full" />
          <Skeleton variant="text" className="!w-20" />
        </div>
      </div>
    ))}
  </div>
);

const LoadingList = () => (
  <div className="space-y-2">
    {Array.from({ length: 5 }).map((_, i) => (
      <div
        key={i}
        className="flex items-center gap-4 bg-gray-800/30 border border-gray-800/50 rounded-xl p-4"
      >
        <Skeleton className="!w-4 !h-4 !rounded" />
        <Skeleton className="!w-3 !h-3 !rounded-full" />
        <div className="flex-1 space-y-1">
          <Skeleton variant="title" className="!w-1/3" />
          <Skeleton variant="text" className="!w-1/2" />
        </div>
        <Skeleton className="!w-12 !h-4" />
        <Skeleton className="!w-16 !h-4" />
        <Skeleton className="!w-8 !h-4" />
      </div>
    ))}
  </div>
);

const ProjectGrid = ({
  projects = [],
  viewMode = "grid",
  pagination,
  onPageChange,
  onPerPageChange,
  selectedIds = new Set(),
  onSelectionChange,
  onView,
  onEdit,
  onDelete,
  onBulkArchive,
  onBulkDelete,
  isLoading,
  isFetching,
  error,
  onRetry,
}) => {
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <FolderIcon className="w-10 h-10 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Failed to load projects</h3>
        <p className="text-gray-400 text-sm mb-4">
          {error.message || "An error occurred while fetching projects."}
        </p>
        <Button variant="primary" onClick={onRetry}>
          Try Again
        </Button>
      </div>
    );
  }

  if (isLoading) {
    return viewMode === "grid" ? <LoadingGrid /> : <LoadingList />;
  }

  if (!projects || projects.length === 0) {
    return (
      <EmptyState
        icon={FolderIcon}
        title="No projects found"
        description="Get started by creating your first security scanning project."
        action={
          <Button variant="primary" gradient onClick={() => onView?.({ action: "create" })}>
            Create Project
          </Button>
        }
      />
    );
  }

  const toggleSelect = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelectionChange?.(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === projects.length) {
      onSelectionChange?.(new Set());
    } else {
      onSelectionChange?.(new Set(projects.map((p) => p.id)));
    }
  };

  return (
    <div>
      {/* Bulk actions bar */}
      {selectedIds.size > 0 && (
        <div
          className="sticky top-0 z-10 mb-4 flex items-center justify-between px-4 py-3
          bg-gray-800/90 backdrop-blur-xl border border-gray-700/50 rounded-xl"
        >
          <span className="text-sm text-gray-300">{selectedIds.size} selected</span>
          <div className="flex items-center gap-2">
            {onBulkArchive && (
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<ArchiveBoxIcon className="w-4 h-4" />}
                onClick={() => onBulkArchive(selectedIds)}
              >
                Archive
              </Button>
            )}
            {onBulkDelete && (
              <Button
                variant="danger"
                size="sm"
                leftIcon={<TrashIcon className="w-4 h-4" />}
                onClick={() => onBulkDelete(selectedIds)}
              >
                Delete
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Select all toggle for list view */}
      {viewMode === "list" && (
        <div className="flex items-center gap-4 px-4 py-2 mb-2">
          <input
            type="checkbox"
            checked={selectedIds.size === projects.length && projects.length > 0}
            onChange={toggleSelectAll}
            className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
          />
          <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">
            Select All
          </span>
        </div>
      )}

      {/* Grid/List content */}
      <div
        className={
          viewMode === "grid" ? "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4" : "space-y-1"
        }
      >
        <AnimatePresence mode="popLayout">
          {projects.map((project) =>
            viewMode === "grid" ? (
              <ProjectCard
                key={project.id}
                project={project}
                selected={selectedIds.has(project.id)}
                onSelect={toggleSelect}
                onView={onView}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ) : (
              <ProjectRow
                key={project.id}
                project={project}
                selected={selectedIds.has(project.id)}
                onSelect={toggleSelect}
                onView={onView}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            )
          )}
        </AnimatePresence>
      </div>

      {/* Refetching overlay */}
      {isFetching && !isLoading && (
        <div className="flex justify-center py-4">
          <div className="w-5 h-5 border-2 border-gray-600 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-800/50">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              Showing {(pagination.page - 1) * pagination.perPage + 1}–
              {Math.min(pagination.page * pagination.perPage, pagination.total)} of{" "}
              {pagination.total}
            </span>
            <select
              value={pagination.perPage}
              onChange={(e) => onPerPageChange?.(Number(e.target.value))}
              className="px-2 py-1 bg-gray-800 border border-gray-700/50 rounded-lg text-xs text-gray-300
                focus:outline-none focus:ring-1 focus:ring-cyan-500/50 [&>option]:bg-gray-800"
            >
              <option value={12}>12 / page</option>
              <option value={24}>24 / page</option>
              <option value={48}>48 / page</option>
            </select>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange?.(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeftIcon className="w-4 h-4" />
            </button>
            {Array.from({ length: pagination.totalPages }, (_, i) => i + 1)
              .filter(
                (p) => p === 1 || p === pagination.totalPages || Math.abs(p - pagination.page) <= 1
              )
              .map((p, idx, arr) => (
                <span key={p} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== p - 1 && (
                    <span className="px-1 text-gray-600 text-xs">...</span>
                  )}
                  <button
                    onClick={() => onPageChange?.(p)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                      p === pagination.page
                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                        : "text-gray-400 hover:text-white hover:bg-gray-800"
                    }`}
                  >
                    {p}
                  </button>
                </span>
              ))}
            <button
              onClick={() => onPageChange?.(pagination.page + 1)}
              disabled={pagination.page >= pagination.totalPages}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRightIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectGrid;
