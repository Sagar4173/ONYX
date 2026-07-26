import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowDownTrayIcon, ClockIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { enterpriseAPI } from "../../services/api";
import { PageContainer, PageHeader } from "../../layouts";
import ParticleBackground from "../projects/ParticleBackground";
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
  const [isExporting, setIsExporting] = useState(false);

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
      setIsExporting(true);
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
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <PageContainer>
        <div className="max-w-7xl mx-auto relative z-10">
          <PageHeader
            title="Audit Logs"
            description="Comprehensive audit trail for compliance and security monitoring"
            icon={ClockIcon}
            breadcrumb={["Audit Logs"]}
            actions={
              <button
                onClick={() => handleExport("json")}
                disabled={isExporting}
                className="inline-flex items-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                {isExporting ? (
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowDownTrayIcon className="w-4 h-4" />
                )}
                <span>{isExporting ? "Exporting..." : "Export"}</span>
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
    </div>
  );
};

export default AuditLogs;
