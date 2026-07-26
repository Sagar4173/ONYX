import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

const ProjectSettingsTab = () => (
  <div className="space-y-6">
    <h3 className="text-lg font-semibold text-white">Project Settings</h3>
    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
      <div className="flex items-start space-x-3">
        <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5" />
        <div>
          <p className="text-yellow-400 font-medium">Settings Configuration</p>
          <p className="text-yellow-300 text-sm mt-1">
            Project settings will be available in a future update. Currently, you can edit basic project information using the edit button above.
          </p>
        </div>
      </div>
    </div>
  </div>
);

export default ProjectSettingsTab;
