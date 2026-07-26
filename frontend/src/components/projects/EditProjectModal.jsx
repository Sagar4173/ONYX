import { XMarkIcon, PencilIcon, InformationCircleIcon, CodeBracketIcon, ShieldCheckIcon, CheckCircleIcon, TagIcon } from "@heroicons/react/24/outline";
import { Button, Modal } from "../../styles/components";

const SCANNER_OPTIONS = [
  { value: "sast", label: "SAST", description: "Static Application Security Testing" },
  { value: "secrets", label: "Secrets", description: "Secret & credential detection" },
  { value: "dependency", label: "Dependencies", description: "Dependency vulnerability scanning" },
  { value: "container", label: "Container", description: "Container image security scanning" },
  { value: "iac", label: "IaC", description: "Infrastructure as Code scanning" },
  { value: "dast", label: "DAST", description: "Dynamic Application Security Testing" },
];

const EditProjectModal = ({ isOpen, onClose, editForm, setEditForm, tagInput, setTagInput, onAddTag, onRemoveTag, onToggleScanner, onSubmit, isPending }) => (
  <Modal size="xl" isOpen={isOpen} onClose={onClose}>
    <div className="flex items-start justify-between mb-8">
      <div className="flex items-center space-x-3">
        <div className="p-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600">
          <PencilIcon className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white">Edit Project</h2>
          <p className="text-gray-400">Update your project configuration</p>
        </div>
      </div>
      <button onClick={onClose} className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900">
        <XMarkIcon className="h-6 w-6" />
      </button>
    </div>

    <form onSubmit={onSubmit} className="space-y-8">
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <InformationCircleIcon className="h-5 w-5 text-cyan-400" />
          <span>Basic Information</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Project Name <span className="text-red-400">*</span></label>
            <input type="text" value={editForm.name} onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="My Awesome Project" className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Category</label>
            <select value={editForm.category} onChange={(e) => setEditForm((prev) => ({ ...prev, category: e.target.value }))} className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all">
              <option value="web_application">🌐 Web Application</option>
              <option value="api_service">🔌 API Service</option>
              <option value="mobile_app">📱 Mobile App</option>
              <option value="microservice">🔷 Microservice</option>
              <option value="library">📚 Library</option>
              <option value="infrastructure">🏗️ Infrastructure</option>
              <option value="other">📦 Other</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Description</label>
          <textarea value={editForm.description} onChange={(e) => setEditForm((prev) => ({ ...prev, description: e.target.value }))} placeholder="Describe your project..." rows={3} className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all resize-none" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Priority</label>
            <select value={editForm.priority} onChange={(e) => setEditForm((prev) => ({ ...prev, priority: e.target.value }))} className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all">
              <option value="low">🟢 Low</option>
              <option value="medium">🟡 Medium</option>
              <option value="high">🟠 High</option>
              <option value="critical">🔴 Critical</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Status</label>
            <select value={editForm.status} onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))} className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all">
              <option value="active">✅ Active</option>
              <option value="inactive">⏸️ Inactive</option>
              <option value="archived">📁 Archived</option>
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <CodeBracketIcon className="h-5 w-5 text-purple-400" />
          <span>Repository Configuration</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Repository URL</label>
            <input type="url" value={editForm.repository.url} onChange={(e) => setEditForm((prev) => ({ ...prev, repository: { ...prev.repository, url: e.target.value } }))} placeholder="https://github.com/user/repo" className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">Default Branch</label>
            <input type="text" value={editForm.repository.branch} onChange={(e) => setEditForm((prev) => ({ ...prev, repository: { ...prev.repository, branch: e.target.value } }))} placeholder="main" className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Access Token (for private repositories)</label>
          <input type="password" value={editForm.repository.access_token} onChange={(e) => setEditForm((prev) => ({ ...prev, repository: { ...prev.repository, access_token: e.target.value } }))} placeholder="ghp_xxxxxxxxxxxx" className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          <p className="text-xs text-gray-500 mt-2">Leave empty to keep current token</p>
        </div>
      </div>

      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <ShieldCheckIcon className="h-5 w-5 text-green-400" />
          <span>Security Scanners</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SCANNER_OPTIONS.map((scanner) => (
            <button key={scanner.value} type="button" onClick={() => onToggleScanner(scanner.value)}
              className={`p-4 rounded-xl border-2 transition-all text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                editForm.scan_config.enabled_scanners.includes(scanner.value) ? "border-cyan-500/70 bg-cyan-500/20" : "border-gray-700/50 bg-gray-800/30 hover:border-gray-600/50"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white">{scanner.label}</span>
                {editForm.scan_config.enabled_scanners.includes(scanner.value) && <CheckCircleIcon className="h-5 w-5 text-cyan-400" />}
              </div>
              <p className="text-sm text-gray-400">{scanner.description}</p>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
          <label className="flex items-center space-x-3 p-4 bg-gray-800/30 rounded-xl border border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-all">
            <input type="checkbox" checked={editForm.scan_config.auto_scan_on_push} onChange={(e) => setEditForm((prev) => ({ ...prev, scan_config: { ...prev.scan_config, auto_scan_on_push: e.target.checked } }))} className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-cyan-500 focus:ring-cyan-500/50" />
            <div>
              <p className="text-white font-medium">Auto-scan on Push</p>
              <p className="text-xs text-gray-400">Automatically scan when code is pushed</p>
            </div>
          </label>
          <label className="flex items-center space-x-3 p-4 bg-gray-800/30 rounded-xl border border-gray-700/50 cursor-pointer hover:bg-gray-800/50 transition-all">
            <input type="checkbox" checked={editForm.scan_config.fail_on_critical} onChange={(e) => setEditForm((prev) => ({ ...prev, scan_config: { ...prev.scan_config, fail_on_critical: e.target.checked } }))} className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-cyan-500 focus:ring-cyan-500/50" />
            <div>
              <p className="text-white font-medium">Fail on Critical</p>
              <p className="text-xs text-gray-400">Mark scan as failed if critical issues found</p>
            </div>
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Scan Timeout (minutes)</label>
          <input type="number" min="5" max="180" value={editForm.scan_config.scan_timeout_minutes} onChange={(e) => setEditForm((prev) => ({ ...prev, scan_config: { ...prev.scan_config, scan_timeout_minutes: parseInt(e.target.value) || 60 } }))} className="w-full md:w-48 px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
        </div>
      </div>

      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
          <TagIcon className="h-5 w-5 text-yellow-400" />
          <span>Tags</span>
        </h3>

        <div className="flex items-center space-x-2">
          <input type="text" value={tagInput} onChange={(e) => setTagInput(e.target.value)} onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), onAddTag())} placeholder="Add tags..." className="flex-1 px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all" />
          <Button type="button" onClick={onAddTag}>Add</Button>
        </div>

        {editForm.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {editForm.tags.map((tag) => (
              <span key={tag} className="px-3 py-1 bg-gray-700/50 text-gray-300 rounded-lg text-sm flex items-center space-x-2">
                <span>{tag}</span>
                <button type="button" onClick={() => onRemoveTag(tag)} className="text-gray-400 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 focus-visible:ring-inset">
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-4 pt-6 border-t border-gray-700/50">
        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
        <Button type="submit" gradient isLoading={isPending}>{isPending ? "Saving..." : "Save Changes"}</Button>
      </div>
    </form>
  </Modal>
);

export default EditProjectModal;
