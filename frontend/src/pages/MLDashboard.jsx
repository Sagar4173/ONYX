import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BeakerIcon, LockClosedIcon } from "@heroicons/react/24/outline";
import { useAuth } from "../components/auth";
import { mlAPI } from "../services/api";
import { PageContainer, PageHeader, ErrorState, LoadingState } from "../layouts/UIComponents";
import MLStatusPanel from "../components/admin/MLStatusPanel";
import MLTrainPanel from "../components/admin/MLTrainPanel";
import MLAnomaliesPanel from "../components/admin/MLAnomaliesPanel";

const MLDashboard = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "ADMIN";

  const statusQuery = useQuery({
    queryKey: ["ml-status"],
    queryFn: mlAPI.getStatus,
    enabled: isAdmin,
    refetchInterval: 30000,
    staleTime: 30000,
    retry: false,
  });

  const anomaliesQuery = useQuery({
    queryKey: ["ml-anomalies"],
    queryFn: mlAPI.getAnomalies,
    enabled: isAdmin,
    refetchInterval: 30000,
    staleTime: 30000,
    retry: false,
  });

  if (!isAdmin) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black p-4 sm:p-6 lg:p-8"
      >
        <div className="max-w-2xl mx-auto mt-20">
          <div className="bg-gray-900/50 backdrop-blur-sm border border-red-500/30 rounded-2xl p-8 text-center">
            <div className="w-20 h-20 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <LockClosedIcon className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Admin Access Required</h2>
            <p className="text-gray-400 mb-6">This area is restricted to administrators only.</p>
            <p className="text-sm text-gray-500">
              Your current role:{" "}
              <span className="text-cyan-400 font-medium">{user?.role || "Unknown"}</span>
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <PageContainer>
      <div className="max-w-7xl mx-auto relative z-10">
        <PageHeader
          title="ML Dashboard"
          description="Anomaly detection model status, training, and recent alerts"
          icon={BeakerIcon}
          breadcrumb={["Admin", "ML Dashboard"]}
        />

        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-2xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Model Status &amp; Training</h2>
          {statusQuery.isLoading ? (
            <LoadingState message="Loading ML status..." cards={3} />
          ) : statusQuery.isError ? (
            <ErrorState
              title="Failed to load ML status"
              message={statusQuery.error?.response?.data?.detail || statusQuery.error?.message}
              onRetry={() => statusQuery.refetch()}
            />
          ) : (
            <div className="space-y-6">
              <MLStatusPanel status={statusQuery.data} />
              <div className="border-t border-gray-800/50 pt-4">
                <MLTrainPanel status={statusQuery.data} />
              </div>
            </div>
          )}
        </div>

        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Anomalies</h2>
          {anomaliesQuery.isLoading ? (
            <LoadingState message="Loading anomaly data..." cards={2} />
          ) : anomaliesQuery.isError ? (
            <ErrorState
              title="Failed to load anomaly data"
              message={
                anomaliesQuery.error?.response?.data?.detail || anomaliesQuery.error?.message
              }
              onRetry={() => anomaliesQuery.refetch()}
            />
          ) : (
            <MLAnomaliesPanel data={anomaliesQuery.data} />
          )}
        </div>
      </div>
    </PageContainer>
  );
};

export default MLDashboard;
