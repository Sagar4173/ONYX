import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { PlusIcon, FunnelIcon } from "@heroicons/react/24/outline";
import { PageContainer, PageHeader } from "../../layouts";
import { schedulesAPI } from "../../services/api";
import ScheduleCard from "./ScheduleCard";
import ScheduleForm from "./ScheduleForm";
import toast from "react-hot-toast";

const ScheduledScansPage = () => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [filterProject, setFilterProject] = useState("");

  const loadSchedules = useCallback(async () => {
    try {
      const params = {};
      if (filterProject) params.project_id = filterProject;
      const data = await schedulesAPI.listSchedules(params);
      setSchedules(data.schedules || []);
    } catch (err) {
      if (err.response?.status !== 401) {
        toast.error("Failed to load schedules");
      }
    } finally {
      setLoading(false);
    }
  }, [filterProject]);

  useEffect(() => {
    loadSchedules();
  }, [loadSchedules]);

  const handleCreate = async (data) => {
    try {
      await schedulesAPI.createSchedule(data);
      toast.success("Schedule created");
      setShowForm(false);
      loadSchedules();
    } catch (err) {
      toast.error("Failed to create schedule");
    }
  };

  const handleUpdate = async (data) => {
    if (!editingSchedule) return;
    try {
      await schedulesAPI.updateSchedule(editingSchedule.id, data);
      toast.success("Schedule updated");
      setEditingSchedule(null);
      loadSchedules();
    } catch (err) {
      toast.error("Failed to update schedule");
    }
  };

  const handleDelete = () => {
    loadSchedules();
  };

  const activeSchedules = schedules.filter((s) => s.enabled);
  const pausedSchedules = schedules.filter((s) => !s.enabled);

  if (loading) {
    return (
      <PageContainer>
        <PageHeader title="Scheduled Scans" subtitle="Automated security scanning" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-gray-800/50 rounded-xl animate-pulse" />
          ))}
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title="Scheduled Scans"
        subtitle="Cron-based automatic security scanning"
        actions={
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium hover:from-cyan-400 hover:to-blue-500 transition-all duration-200 shadow-lg shadow-cyan-500/20"
          >
            <PlusIcon className="w-4 h-4" />
            New Schedule
          </button>
        }
      />

      <div className="mb-6 flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <FunnelIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={filterProject}
            onChange={(e) => setFilterProject(e.target.value)}
            placeholder="Filter by project ID..."
            className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700/50 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 transition-all"
          />
        </div>
        <span className="text-xs text-gray-500">{schedules.length} schedule{schedules.length !== 1 ? "s" : ""}</span>
      </div>

      {schedules.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-800/80 border border-gray-700/50 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-300 mb-2">No schedules yet</h3>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            Create automated scan schedules to run security scans on your projects at regular intervals.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium hover:from-cyan-400 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/20"
          >
            <PlusIcon className="w-4 h-4" />
            Create Your First Schedule
          </button>
        </motion.div>
      ) : (
        <div className="space-y-6">
          {activeSchedules.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                Active ({activeSchedules.length})
              </h3>
              <div className="grid gap-4">
                {activeSchedules.map((schedule) => (
                  <ScheduleCard
                    key={schedule.id}
                    schedule={schedule}
                    onUpdate={loadSchedules}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </div>
          )}
          {pausedSchedules.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                Paused ({pausedSchedules.length})
              </h3>
              <div className="grid gap-4">
                {pausedSchedules.map((schedule) => (
                  <ScheduleCard
                    key={schedule.id}
                    schedule={schedule}
                    onUpdate={loadSchedules}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showForm && (
        <ScheduleForm
          onSubmit={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {editingSchedule && (
        <ScheduleForm
          initial={editingSchedule}
          onSubmit={handleUpdate}
          onCancel={() => setEditingSchedule(null)}
        />
      )}
    </PageContainer>
  );
};

export default ScheduledScansPage;
