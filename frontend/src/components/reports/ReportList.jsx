import { motion } from "framer-motion";
import { ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { Button, Skeleton, EmptyState } from "../ui/StyleComponents";
import ReportListItem from "./ReportListItem";
import ReportGridCard from "./ReportGridCard";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};

const LoadingList = () => (
  <div className="space-y-3">
    {Array.from({ length: 5 }).map((_, i) => (
      <div
        key={i}
        className="flex items-center gap-4 bg-gray-800/30 border border-gray-800/50 rounded-xl p-4"
      >
        <Skeleton className="!w-12 !h-12 !rounded-2xl" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="title" className="!w-1/3" />
          <Skeleton variant="text" className="!w-1/2" />
          <Skeleton variant="text" className="!w-1/4" />
        </div>
        <Skeleton variant="button" />
      </div>
    ))}
  </div>
);

const LoadingGrid = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="bg-gray-800/30 border border-gray-800/50 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="!w-16 !h-16 !rounded-full" />
          <Skeleton className="!w-16 !h-6 !rounded-md" />
        </div>
        <Skeleton variant="title" className="!w-2/3 mb-2" />
        <Skeleton variant="text" className="!w-1/2 mb-3" />
        <Skeleton variant="text" className="!w-1/4" />
      </div>
    ))}
  </div>
);

const ReportList = ({
  reports,
  pagination,
  onPageChange,
  onPerPageChange,
  isLoading,
  error,
  onRetry,
  viewMode = "list",
}) => {
  if (error) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex p-4 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
          <DocumentTextIcon className="w-10 h-10 text-red-400" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Failed to load reports</h3>
        <p className="text-gray-400 text-sm mb-4">{error.message || "An error occurred."}</p>
        <Button variant="primary" onClick={onRetry}>
          Try Again
        </Button>
      </div>
    );
  }

  if (isLoading) return viewMode === "grid" ? <LoadingGrid /> : <LoadingList />;

  if (!reports || reports.length === 0) {
    return (
      <EmptyState
        icon={DocumentTextIcon}
        title="No reports found"
        description="Reports will appear here once scans are completed."
      />
    );
  }

  return (
    <div>
      {viewMode === "grid" ? (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          variants={container}
          initial="hidden"
          animate="show"
        >
          {reports.map((report) => (
            <ReportGridCard key={report.id} report={report} />
          ))}
        </motion.div>
      ) : (
        <motion.div className="space-y-3" variants={container} initial="hidden" animate="show">
          {reports.map((report) => (
            <ReportListItem key={report.id} report={report} />
          ))}
        </motion.div>
      )}

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
              className="px-2 py-1 bg-gray-800 border border-gray-700/50 rounded-lg text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 [&>option]:bg-gray-800"
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
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
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
                    className={`w-8 h-8 rounded-lg text-sm font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
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
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 disabled:opacity-30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              <ChevronRightIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportList;
