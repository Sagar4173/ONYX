import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowPathIcon,
  DocumentTextIcon,
  Bars3Icon,
  Squares2X2Icon,
} from "@heroicons/react/24/outline";
import { Button } from "../styles/components";
import { PageContainer, PageHeader } from "../layouts/UIComponents";
import { reportsAPI } from "../services/api";
import ReportFilters from "../components/reports/ReportFilters";
import ReportList from "../components/reports/ReportList";

const Reports = () => {
  const [viewMode, setViewMode] = useState("list");
  const [filters, setFilters] = useState({ search: "", status: "" });
  const [sort, setSort] = useState("newest");
  const [pagination, setPagination] = useState({ page: 1, perPage: 24 });

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["reports", filters, sort, pagination],
    queryFn: () =>
      reportsAPI
        .getReports({
          ...filters,
          sort_by: "created_at",
          sort_order: sort === "newest" ? "desc" : "asc",
          page: pagination.page,
          per_page: pagination.perPage,
        })
        .then((res) => res.data || res),
  });

  const reports = data?.reports ?? data ?? [];
  const paginationInfo = data?.pagination || {
    page: 1,
    perPage: 24,
    total: reports.length,
    totalPages: 1,
  };

  const handleFilterChange = (next) => {
    setFilters(next);
    setPagination((p) => ({ ...p, page: 1 }));
  };

  const handleSortChange = (next) => {
    setSort(next);
    setPagination((p) => ({ ...p, page: 1 }));
  };

  return (
    <PageContainer>
      <PageHeader
        title="Scan Reports"
        description="View detailed security scan results"
        icon={DocumentTextIcon}
        breadcrumb={["Reports"]}
        actions={
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-800/50 border border-gray-700/50 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode("list")}
                className={`p-2 rounded-md transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                  viewMode === "list"
                    ? "bg-gray-700/70 text-white"
                    : "text-gray-400 hover:text-white"
                }`}
                title="List view"
              >
                <Bars3Icon className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("grid")}
                className={`p-2 rounded-md transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 ${
                  viewMode === "grid"
                    ? "bg-gray-700/70 text-white"
                    : "text-gray-400 hover:text-white"
                }`}
                title="Grid view"
              >
                <Squares2X2Icon className="w-4 h-4" />
              </button>
            </div>
            <Button
              variant="ghost"
              leftIcon={<ArrowPathIcon className="w-4 h-4" />}
              onClick={refetch}
              isLoading={isFetching}
            >
              Refresh
            </Button>
          </div>
        }
      />

      <ReportFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        sort={sort}
        onSortChange={handleSortChange}
        total={paginationInfo.total}
      />

      <ReportList
        reports={reports}
        pagination={paginationInfo}
        onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))}
        onPerPageChange={(perPage) => setPagination((prev) => ({ ...prev, perPage, page: 1 }))}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        viewMode={viewMode}
      />
    </PageContainer>
  );
};

export default Reports;
