import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  ShieldExclamationIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";
import { secretHistoryAPI } from "../../services/api";

const statusColors = {
  active: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  resolved: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  dismissed: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
};

const severityColors = {
  critical: "text-red-600 dark:text-red-400",
  high: "text-orange-600 dark:text-orange-400",
  medium: "text-yellow-600 dark:text-yellow-400",
  low: "text-blue-600 dark:text-blue-400",
};

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        statusColors[status] || statusColors.dismissed
      }`}
    >
      {status === "active" && <ShieldExclamationIcon className="mr-1 h-3.5 w-3.5" />}
      {status === "resolved" && <CheckCircleIcon className="mr-1 h-3.5 w-3.5" />}
      {status === "dismissed" && <XCircleIcon className="mr-1 h-3.5 w-3.5" />}
      {status}
    </span>
  );
}

function SeverityIcon({ severity }) {
  return (
    <span className={`inline-flex items-center ${severityColors[severity] || severityColors.medium}`}>
      <ShieldExclamationIcon className="h-4 w-4" />
    </span>
  );
}

export default function SecretHistoryPanel({ projectName: propProjectName }) {
  const queryClient = useQueryClient();
  const [inputProject, setInputProject] = useState(propProjectName || "");
  const [projectName, setProjectName] = useState(propProjectName || "");
  const [filter, setFilter] = useState("active");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data: listData, isLoading: listLoading, error: listError, refetch: refetchList } = useQuery({
    queryKey: ["secret-history", projectName, filter, page],
    queryFn: () =>
      secretHistoryAPI.list(projectName, {
        limit: pageSize,
        offset: page * pageSize,
        status: filter !== "all" ? filter : undefined,
      }),
    enabled: !!projectName,
  });

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ["secret-history-summary", projectName],
    queryFn: () => secretHistoryAPI.summary(projectName),
    enabled: !!projectName,
  });

  const { data: trendsData } = useQuery({
    queryKey: ["secret-history-trends", projectName],
    queryFn: () => secretHistoryAPI.trends(projectName, 14),
    enabled: !!projectName,
  });

  const updateMutation = useMutation({
    mutationFn: ({ recordId, status }) => secretHistoryAPI.updateStatus(recordId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["secret-history"] });
      queryClient.invalidateQueries({ queryKey: ["secret-history-summary"] });
    },
  });

  const records = listData?.records || [];
  const total = listData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  const filters = ["all", "active", "resolved", "dismissed"];

  if (!projectName) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <EyeIcon className="h-16 w-16 text-gray-300 dark:text-gray-600" />
        <h2 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">Secret History</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Enter a project name to view its secret scanning history
        </p>
        <div className="mt-4 flex gap-2">
          <input
            type="text"
            value={inputProject}
            onChange={(e) => setInputProject(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setProjectName(inputProject)}
            placeholder="Project name..."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
          <button
            onClick={() => setProjectName(inputProject)}
            disabled={!inputProject.trim()}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Load
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        {summaryLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg bg-white p-4 dark:bg-gray-800">
              <div className="h-4 w-20 rounded bg-gray-200 dark:bg-gray-700" />
              <div className="mt-2 h-8 w-12 rounded bg-gray-200 dark:bg-gray-700" />
            </div>
          ))
        ) : (
          <>
            {[
              { label: "Total", value: summaryData?.total || 0, color: "text-gray-900 dark:text-white" },
              { label: "Active", value: summaryData?.active || 0, color: "text-red-600 dark:text-red-400" },
              { label: "Resolved", value: summaryData?.resolved || 0, color: "text-green-600 dark:text-green-400" },
              { label: "Dismissed", value: summaryData?.dismissed || 0, color: "text-gray-500" },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
              >
                <div className="text-sm text-gray-500 dark:text-gray-400">{item.label}</div>
                <div className={`mt-1 text-2xl font-semibold ${item.color}`}>{item.value}</div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Trends Chart */}
      {trendsData?.trends?.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-3 flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-gray-500" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">Secret Trends (Last 14 Days)</h3>
          </div>
          <div className="flex items-end gap-1" style={{ height: "80px" }}>
            {trendsData.trends.map((point, i) => {
              const maxActive = Math.max(...trendsData.trends.map((t) => t.total_active), 1);
              const heightPct = (point.total_active / maxActive) * 100;
              return (
                <div
                  key={i}
                  className="group relative flex flex-1 flex-col items-center"
                  title={`${point.date}: ${point.total_active} active`}
                >
                  <div
                    className="w-full rounded-t bg-red-400 transition-all hover:bg-red-500 dark:bg-red-600"
                    style={{ height: `${Math.max(heightPct, 2)}%` }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setPage(0);
            }}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <button
          onClick={() => refetchList()}
          className="ml-auto rounded-md bg-gray-100 p-1.5 text-gray-500 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          <ArrowPathIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Secret Records */}
      {listLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-lg bg-white p-4 dark:bg-gray-800">
              <div className="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700" />
              <div className="mt-2 h-3 w-1/2 rounded bg-gray-200 dark:bg-gray-700" />
            </div>
          ))}
        </div>
      ) : listError ? (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-900/20 dark:text-red-400">
          <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0" />
          <span>Failed to load secret history: {listError.message}</span>
        </div>
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <EyeIcon className="h-12 w-12" />
          <p className="mt-2 text-sm">No secrets found</p>
          <p className="text-xs">Secrets detected during scans will appear here</p>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    File
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Line
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Seen
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Last Seen
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
                {records.map((rec) => (
                  <tr key={rec.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="whitespace-nowrap px-4 py-3">
                      <div className="flex items-center gap-2">
                        <SeverityIcon severity={rec.severity} />
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {rec.secret_type}
                        </span>
                      </div>
                    </td>
                    <td className="max-w-[200px] truncate px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      <span title={rec.file_path}>{rec.file_path}</span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {rec.line_number}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <StatusBadge status={rec.status} />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {rec.appearance_count}x
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(rec.last_seen_at).toLocaleDateString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      {rec.status === "active" && (
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() =>
                              updateMutation.mutate({ recordId: rec.id, status: "resolved" })
                            }
                            className="rounded p-1 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20"
                            title="Mark resolved"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() =>
                              updateMutation.mutate({ recordId: rec.id, status: "dismissed" })
                            }
                            className="rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="Dismiss"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                      {rec.status === "resolved" && (
                        <button
                          onClick={() =>
                            updateMutation.mutate({ recordId: rec.id, status: "active" })
                          }
                          className="rounded p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                          title="Reopen"
                        >
                          <ShieldExclamationIcon className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} of {total}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="rounded-md bg-gray-100 px-3 py-1 text-sm text-gray-600 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-400"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="rounded-md bg-gray-100 px-3 py-1 text-sm text-gray-600 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-400"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
