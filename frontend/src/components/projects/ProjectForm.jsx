import { motion } from "framer-motion";
import { useReducer, useEffect } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { XMarkIcon, PlusIcon } from "@heroicons/react/24/outline";
import { toast } from "react-hot-toast";
import { Modal, Button } from "../../styles/components";
import { projectsAPI } from "../../services/api";

const INITIAL_STATE = {
  name: "",
  description: "",
  category: "other",
  priority: "medium",
  repository: { url: "", branch: "main", access_token: "", scan_paths: ["/"], exclude_paths: [] },
  scan_config: {
    enabled_scanners: ["sast", "secrets"],
    auto_scan_on_push: false,
    scan_timeout_minutes: 60,
    fail_on_critical: false,
  },
  tags: [],
};

function formReducer(state, action) {
  switch (action.type) {
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    case "SET_REPO_FIELD":
      return { ...state, repository: { ...state.repository, [action.field]: action.value } };
    case "SET_SCAN_FIELD":
      return { ...state, scan_config: { ...state.scan_config, [action.field]: action.value } };
    case "TOGGLE_SCANNER":
      return {
        ...state,
        scan_config: {
          ...state.scan_config,
          enabled_scanners: state.scan_config.enabled_scanners.includes(action.scanner)
            ? state.scan_config.enabled_scanners.filter((s) => s !== action.scanner)
            : [...state.scan_config.enabled_scanners, action.scanner],
        },
      };
    case "ADD_TAG":
      if (!action.tag.trim() || state.tags.includes(action.tag.trim())) return state;
      return { ...state, tags: [...state.tags, action.tag.trim()] };
    case "REMOVE_TAG":
      return { ...state, tags: state.tags.filter((t) => t !== action.tag) };
    case "RESET":
      return { ...INITIAL_STATE };
    case "LOAD_PROJECT":
      return {
        ...INITIAL_STATE,
        name: action.project.name || "",
        description: action.project.description || "",
        category: action.project.category || "other",
        priority: action.project.priority || "medium",
        repository: {
          url: action.project.repository_url || "",
          branch: action.project.repository?.branch || "main",
          access_token: "",
          scan_paths: action.project.repository?.scan_paths || ["/"],
          exclude_paths: action.project.repository?.exclude_paths || [],
        },
        scan_config: {
          enabled_scanners: action.project.scan_config?.enabled_scanners || ["sast", "secrets"],
          auto_scan_on_push: action.project.scan_config?.auto_scan_on_push || false,
          scan_timeout_minutes: action.project.scan_config?.scan_timeout_minutes || 60,
          fail_on_critical: action.project.scan_config?.fail_on_critical || false,
        },
        tags: action.project.tags || [],
      };
    default:
      return state;
  }
}

const scanners = [
  { value: "sast", label: "SAST", description: "Static code analysis" },
  { value: "secrets", label: "Secrets", description: "Credential detection" },
  { value: "dependency", label: "Dependencies", description: "Vulnerable packages" },
  { value: "container", label: "Container", description: "Image scanning" },
  { value: "iac", label: "IaC", description: "Infrastructure as Code" },
];

const ProjectForm = ({ isOpen, onClose, project, onSuccess }) => {
  const [state, dispatch] = useReducer(formReducer, INITIAL_STATE);
  const queryClient = useQueryClient();

  const { data: templates } = useQuery({
    queryKey: ["projectTemplates"],
    queryFn: projectsAPI.getTemplateCategories,
  });

  useEffect(() => {
    if (project) {
      dispatch({ type: "LOAD_PROJECT", project });
    } else {
      dispatch({ type: "RESET" });
    }
  }, [project, isOpen]);

  const mutation = useMutation({
    mutationFn: project
      ? (data) => projectsAPI.updateProject(project.id, data)
      : (data) => projectsAPI.createProject(data),
    onSuccess: (data) => {
      toast.success(project ? "Project updated successfully!" : "Project created successfully!");
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projectAnalytics"] });
      onSuccess?.(data);
      onClose();
    },
    onError: (error) => {
      toast.error(error.message || `Failed to ${project ? "update" : "create"} project`);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!state.name.trim() || !state.repository.url.trim()) {
      toast.error("Project name and repository URL are required");
      return;
    }
    mutation.mutate(state);
  };

  return (
    <Modal size="xl" isOpen={isOpen} onClose={onClose} title="">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600">
            <PlusIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">
              {project ? "Edit Project" : "Create New Project"}
            </h2>
            <p className="text-gray-400 text-sm">
              {project ? "Update project configuration" : "Set up a new security scanning project"}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all"
        >
          <XMarkIcon className="w-6 h-6" />
        </button>
      </div>

      <motion.form
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.06 } },
        }}
        onSubmit={handleSubmit}
        className="space-y-6"
      >
        {/* Basic Information */}
        <motion.fieldset
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <legend className="text-lg font-semibold text-white mb-4">Basic Information</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Project Name *</label>
              <input
                type="text"
                value={state.name}
                onChange={(e) =>
                  dispatch({ type: "SET_FIELD", field: "name", value: e.target.value })
                }
                placeholder="My Awesome Project"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
              <select
                value={state.category}
                onChange={(e) =>
                  dispatch({ type: "SET_FIELD", field: "category", value: e.target.value })
                }
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
              >
                {templates?.categories?.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={state.description}
              onChange={(e) =>
                dispatch({ type: "SET_FIELD", field: "description", value: e.target.value })
              }
              placeholder="Describe your project..."
              rows={3}
              className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none transition-all"
            />
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
            <select
              value={state.priority}
              onChange={(e) =>
                dispatch({ type: "SET_FIELD", field: "priority", value: e.target.value })
              }
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700/50 rounded-xl text-white
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 [&>option]:bg-gray-800 [&>option]:text-white"
            >
              {templates?.priorities?.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
        </motion.fieldset>

        {/* Repository Configuration */}
        <motion.fieldset
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <legend className="text-lg font-semibold text-white mb-4">Repository</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Repository URL *
              </label>
              <input
                type="url"
                value={state.repository.url}
                onChange={(e) =>
                  dispatch({ type: "SET_REPO_FIELD", field: "url", value: e.target.value })
                }
                placeholder="https://github.com/org/project"
                required
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Branch</label>
              <input
                type="text"
                value={state.repository.branch}
                onChange={(e) =>
                  dispatch({ type: "SET_REPO_FIELD", field: "branch", value: e.target.value })
                }
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Access Token</label>
              <input
                type="password"
                value={state.repository.access_token}
                onChange={(e) =>
                  dispatch({ type: "SET_REPO_FIELD", field: "access_token", value: e.target.value })
                }
                placeholder="Optional"
                autoComplete="off"
                className="w-full px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400
                  focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
              />
            </div>
          </div>
        </motion.fieldset>

        {/* Security Scanners */}
        <motion.fieldset
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <legend className="text-lg font-semibold text-white mb-4">Security Scanners</legend>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {scanners.map((scanner) => {
              const isEnabled = state.scan_config.enabled_scanners.includes(scanner.value);
              return (
                <button
                  key={scanner.value}
                  type="button"
                  onClick={() => dispatch({ type: "TOGGLE_SCANNER", scanner: scanner.value })}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    isEnabled
                      ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                      : "bg-gray-800/50 border-gray-700/50 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  <div className="text-xs font-semibold">{scanner.label}</div>
                  <div className="text-[10px] opacity-70">{scanner.description}</div>
                </button>
              );
            })}
          </div>
        </motion.fieldset>

        {/* Scan Config */}
        <motion.fieldset
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <legend className="text-lg font-semibold text-white mb-4">Scan Configuration</legend>
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={state.scan_config.auto_scan_on_push}
                onChange={(e) =>
                  dispatch({
                    type: "SET_SCAN_FIELD",
                    field: "auto_scan_on_push",
                    value: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0"
              />
              <span className="text-sm text-gray-300">Auto-scan on push</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={state.scan_config.fail_on_critical}
                onChange={(e) =>
                  dispatch({
                    type: "SET_SCAN_FIELD",
                    field: "fail_on_critical",
                    value: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0"
              />
              <span className="text-sm text-gray-300">Fail build on critical findings</span>
            </label>
          </div>
        </motion.fieldset>

        {/* Tags */}
        <motion.fieldset
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <legend className="text-lg font-semibold text-white mb-4">Tags</legend>
          <div className="flex items-center gap-2 mb-3">
            <input
              type="text"
              placeholder="Add a tag..."
              id="tag-input"
              className="flex-1 px-4 py-2.5 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 text-sm
                focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  const input = e.target;
                  dispatch({ type: "ADD_TAG", tag: input.value });
                  input.value = "";
                }
              }}
            />
          </div>
          {state.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs
                  bg-gray-800 text-gray-300 border border-gray-700/50"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => dispatch({ type: "REMOVE_TAG", tag })}
                    className="hover:text-white transition-colors"
                  >
                    <XMarkIcon className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </motion.fieldset>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-700/50">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>
            {project ? "Save Changes" : "Create Project"}
          </Button>
        </div>
      </motion.form>
    </Modal>
  );
};

export default ProjectForm;
