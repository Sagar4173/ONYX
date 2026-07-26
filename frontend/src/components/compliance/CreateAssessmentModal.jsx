import { Button, Modal } from "../../styles/components";
import { frameworks } from "./complianceHelpers";

const CreateAssessmentModal = ({
  isOpen,
  onClose,
  formData,
  setFormData,
  projectsData,
  onSubmit,
  isPending,
}) => (
  <Modal
    size="lg"
    isOpen={isOpen}
    onClose={onClose}
    title="Create Compliance Assessment"
    footer={
      <>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button
          type="submit"
          form="assessment-form"
          gradient
          isLoading={isPending}
          disabled={formData.frameworks.length === 0}
        >
          Start Assessment
        </Button>
      </>
    }
  >
    <form id="assessment-form" onSubmit={onSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Select Project *</label>
        <select
          value={formData.project_id}
          onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
          className="w-full px-4 py-3 bg-gray-800/30 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 appearance-none cursor-pointer"
          required
        >
          <option value="" disabled>
            Choose a project...
          </option>
          {(projectsData?.projects || []).map((project) => (
            <option key={project.id || project._id} value={project.id || project._id}>
              {project.name}
              {project.repository?.url ? ` — ${project.repository.url}` : ""}
            </option>
          ))}
        </select>
        {(!projectsData?.projects || projectsData.projects.length === 0) && (
          <p className="mt-2 text-xs text-yellow-400">
            No projects found. Create a project first to run compliance assessments.
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-3">Select Frameworks *</label>
        <div className="grid grid-cols-2 gap-3">
          {frameworks.map((framework) => (
            <button
              key={framework.id}
              type="button"
              onClick={() => {
                const newFrameworks = formData.frameworks.includes(framework.id)
                  ? formData.frameworks.filter((f) => f !== framework.id)
                  : [...formData.frameworks, framework.id];
                setFormData({ ...formData, frameworks: newFrameworks });
              }}
              className={`p-4 border rounded-xl text-left transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                formData.frameworks.includes(framework.id)
                  ? `bg-gradient-to-r ${framework.color} border-transparent`
                  : "bg-gray-800/30 border-gray-700/50 hover:bg-gray-700/50"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">{framework.icon}</span>
                <span className="font-medium text-white">{framework.name}</span>
              </div>
              <p className="text-xs text-gray-300 opacity-80">{framework.description}</p>
            </button>
          ))}
        </div>
        <p className="mt-2 text-sm text-gray-400">Select at least one framework for assessment</p>
      </div>
    </form>
  </Modal>
);

export default CreateAssessmentModal;
