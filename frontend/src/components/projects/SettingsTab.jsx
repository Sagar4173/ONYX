import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { projectsAPI } from "../../services/api";

const Panel = ({ title, description, children, defaultExpanded = true }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="bg-gray-900/50 rounded-xl border border-gray-700/50 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/30 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      >
        <div className="text-left">
          <h4 className="text-white font-medium">{title}</h4>
          {description && <p className="text-gray-400 text-sm">{description}</p>}
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 border-t border-gray-700/50 pt-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const SettingsTab = () => {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const { data: project } = useQuery({ queryKey: ["project", projectId], enabled: !!projectId });

  const [form, setForm] = useState({
    name: "",
    description: "",
    priority: "medium",
    status: "active",
    category: "other",
  });

  useEffect(() => {
    if (project) {
      setForm({
        name: project.name || "",
        description: project.description || "",
        priority: project.priority || "medium",
        status: project.status || "active",
        category: project.category || "other",
      });
    }
  }, [project]);

  const updateMutation = useMutation({
    mutationFn: (data) => projectsAPI.updateProject(projectId, data),
    onSuccess: () => {
      toast.success("Settings saved");
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (err) => toast.error(err.message || "Failed to save"),
  });

  const handleSave = (section) => updateMutation.mutate(section);

  if (!project) return null;

  return (
    <div className="space-y-4 max-w-2xl">
      <Panel title="General" description="Basic project information" defaultExpanded={true}>
        <div className="grid grid-cols-2 gap-4 mb-4">
          {["name", "category", "priority", "status"].map((field) => (
            <div key={field}>
              <label className="block text-sm text-gray-300 mb-1.5 capitalize">{field}</label>
              {field === "name" ? (
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                />
              ) : (
                <select
                  value={form[field]}
                  onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                >
                  {(field === "category"
                    ? [
                        "web_application",
                        "api_service",
                        "mobile_app",
                        "microservice",
                        "library",
                        "infrastructure",
                        "other",
                      ]
                    : field === "priority"
                      ? ["low", "medium", "high", "critical"]
                      : ["active", "inactive", "archived"]
                  ).map((opt) => (
                    <option key={opt} value={opt}>
                      {opt.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              )}
            </div>
          ))}
        </div>
        <div className="mb-4">
          <label className="block text-sm text-gray-300 mb-1.5">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            rows={2}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none"
          />
        </div>
        <button
          onClick={() =>
            handleSave({
              name: form.name,
              description: form.description,
              priority: form.priority,
              status: form.status,
              category: form.category,
            })
          }
          disabled={updateMutation.isPending}
          className="px-4 py-2 bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white text-sm font-medium rounded-lg hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 transition-all disabled:opacity-50"
        >
          {updateMutation.isPending ? "Saving..." : "Save"}
        </button>
      </Panel>

      <Panel
        title="Danger Zone"
        description="Irreversible destructive actions"
        defaultExpanded={false}
      >
        <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-4">
          <p className="text-red-300 text-sm font-medium mb-2">Delete this project</p>
          <p className="text-red-200/70 text-sm mb-3">
            Permanently remove this project and all associated scans, reports, and data.
          </p>
          <button
            onClick={() => document.dispatchEvent(new CustomEvent("open-delete-modal"))}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-all"
          >
            Delete Project
          </button>
        </div>
      </Panel>
    </div>
  );
};

export default SettingsTab;
