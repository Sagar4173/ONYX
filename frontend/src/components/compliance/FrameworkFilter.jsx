import { frameworks } from "./complianceHelpers";

const FrameworkFilter = ({ selectedFramework, setSelectedFramework }) => (
  <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-xl lg:rounded-2xl p-3 lg:p-4 shadow-xl mb-8">
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => setSelectedFramework("all")}
        className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
          selectedFramework === "all"
            ? "bg-purple-500 text-white"
            : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
        }`}
      >
        All Frameworks
      </button>
      {frameworks.map((framework) => (
        <button
          key={framework.id}
          onClick={() => setSelectedFramework(framework.id)}
          className={`px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg text-sm lg:text-base font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
            selectedFramework === framework.id
              ? `bg-gradient-to-r ${framework.color} text-white`
              : "bg-gray-900/50 text-gray-400 hover:bg-gray-800/50"
          }`}
        >
          {framework.icon} {framework.name}
        </button>
      ))}
    </div>
  </div>
);

export default FrameworkFilter;
