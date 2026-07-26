import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownTrayIcon, ClockIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";
import AuditFilters from "./AuditFilters";
import AuditTable from "./AuditTable";

const AuditLogs = () => {
  const [filters, setFilters] = useState({
    event_types: [],
    users: [],
    start_date: "",
    end_date: "",
    search: "",
    severity: "",
  });
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedLog, setExpandedLog] = useState(null);

  const { data: auditData, isLoading } = useQuery({
    queryKey: ["auditLogs", filters, page, limit],
    queryFn: () =>
      enterpriseAPI.getAuditLogs({
        ...filters,
        skip: (page - 1) * limit,
        limit,
      }),
    placeholderData: (previousData) => previousData,
  });

  const { data: usersData } = useQuery({
    queryKey: ["auditUsers"],
    queryFn: () => enterpriseAPI.getAuditUsers(),
  });

  const handleExport = async (format = "json") => {
    try {
      toast.loading("Exporting audit logs...");
      const data = await enterpriseAPI.exportAuditLogs({ ...filters, format });

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: format === "json" ? "application/json" : "text/csv",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.dismiss();
      toast.success(`Audit logs exported as ${format.toUpperCase()}`);
    } catch {
      toast.dismiss();
      toast.error("Failed to export audit logs");
    }
  };

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto">
        <PageHeader
          title="Audit Logs"
          description="Comprehensive audit trail for compliance and security monitoring"
          icon={ClockIcon}
          breadcrumb={["Audit Logs"]}
          actions={
            <button
              onClick={() => handleExport("json")}
              className="flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-xl text-white text-sm lg:text-base font-semibold shadow-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              <ArrowDownTrayIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              <span>Export</span>
            </button>
          }
        />

        <AuditFilters
          filters={filters}
          setFilters={setFilters}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
          usersData={usersData}
        />

        <AuditTable
          auditData={auditData}
          isLoading={isLoading}
          expandedLog={expandedLog}
          setExpandedLog={setExpandedLog}
          limit={limit}
          page={page}
          setPage={setPage}
        />
      </div>
    </PageContainer>
  );
};

export default AuditLogs;
