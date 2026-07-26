import { useMemo } from "react";
import { CommandLineIcon } from "@heroicons/react/24/outline";
import { scanners } from "../landingPageData";

const tabs = [
  { id: "all", label: "All Tools", count: 10 },
  { id: "sast", label: "SAST", count: 3 },
  { id: "secrets", label: "Secrets", count: 1 },
  { id: "sca", label: "SCA", count: 1 },
  { id: "dast", label: "DAST", count: 2 },
  { id: "container", label: "Container", count: 1 },
  { id: "iac", label: "IaC", count: 2 },
];

const ScannersSection = ({ activeTab, setActiveTab }) => {
  const filteredScanners = useMemo(
    () =>
      activeTab === "all"
        ? scanners
        : scanners.filter((s) => s.category.toLowerCase() === activeTab),
    [activeTab]
  );

  return (
    <section
      id="scanners"
      className="py-32 bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950"
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
            <CommandLineIcon className="w-4 h-4 text-violet-400" />
            <span className="text-sm text-violet-400">Security Arsenal</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            <span className="text-violet-400">10</span> Security Scanners
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Open-source security tools integrated into one unified platform
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                activeTab === tab.id
                  ? "bg-violet-500/20 text-violet-400 border border-violet-500/30"
                  : "bg-gray-800/50 text-gray-400 border border-gray-700/50 hover:bg-gray-800 hover:text-white"
              }`}
            >
              {tab.label} <span className="ml-1 text-xs opacity-60">({tab.count})</span>
            </button>
          ))}
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredScanners.map((scanner) => (
            <div
              key={scanner.name}
              className="group p-6 rounded-2xl bg-gray-900/50 border border-gray-800/50 hover:border-violet-500/30 hover:bg-gray-800/50 transition-all hover:transform hover:-translate-y-1"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center text-3xl">
                  {scanner.icon}
                </div>
                <div>
                  <h4 className="font-bold text-white text-lg">{scanner.name}</h4>
                  <span className="text-xs text-violet-400 font-medium px-2 py-0.5 bg-violet-500/10 rounded-full">
                    {scanner.category}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-300 font-medium mb-2">{scanner.description}</p>
              <p className="text-sm text-gray-500 leading-relaxed">{scanner.what}</p>
            </div>
          ))}
        </div>

        {activeTab === "all" && (
          <div className="text-center mt-8">
            <span className="text-gray-500 text-sm">
              Showing all {filteredScanners.length} security scanners
            </span>
          </div>
        )}
      </div>
    </section>
  );
};

export default ScannersSection;
