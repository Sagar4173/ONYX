/**
 * SBOM Viewer Component
 * Display and manage Software Bill of Materials
 * Features: SPDX/CycloneDX support, vulnerability enrichment, export options
 */
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { FixedSizeList as List } from "react-window";
import {
  CubeIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ArrowTopRightOnSquareIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ClipboardIcon,
  InformationCircleIcon,
  LockClosedIcon,
} from "@heroicons/react/24/outline";

import { Card } from "@styles";

// API Configuration - Production ready with environment variable support
const API_BASE_URL = import.meta.env.DEV
  ? "http://127.0.0.1:8000"
  : import.meta.env.VITE_API_URL || "/api";

// License badge
const LicenseBadge = ({ license }) => {
  const openSourceLicenses = ["MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0", "ISC"];
  const isOpenSource = openSourceLicenses.some((l) => license?.includes(l));

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full ${
        isOpenSource ? "bg-green-900/30 text-green-400" : "bg-gray-700/30 text-gray-300"
      }`}
    >
      {license || "Unknown"}
    </span>
  );
};

// Vulnerability indicator
const VulnIndicator = ({ count, severity }) => {
  if (!count || count === 0) {
    return (
      <span className="text-green-400 text-sm flex items-center gap-1">
        <CheckCircleIcon className="w-4 h-4" />
        No known vulns
      </span>
    );
  }

  const colors = {
    critical: "text-red-400 bg-red-900/30",
    high: "text-orange-400 bg-orange-900/30",
    medium: "text-yellow-400 bg-yellow-900/30",
    low: "text-cyan-400 bg-cyan-900/30",
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full flex items-center gap-1 ${
        colors[severity] || colors.medium
      }`}
    >
      <ExclamationTriangleIcon className="w-3 h-3" />
      {count} {severity || "vulnerability"}
    </span>
  );
};

// Package row component
const PackageRow = ({ pkg, onViewVulns: _onViewVulns, isExpanded, onToggle }) => {
  return (
    <div className="border-b border-gray-700/50 last:border-0">
      <div
        className="flex items-center justify-between p-3 hover:bg-gray-800/30 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {isExpanded ? (
            <ChevronDownIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
          )}
          <CubeIcon className="w-4 h-4 text-cyan-500 flex-shrink-0" />
          <span className="font-medium text-white">{pkg.name}</span>
          <span className="text-gray-400 text-sm">@{pkg.version}</span>
        </div>
        <div className="flex items-center gap-3">
          <LicenseBadge license={pkg.license} />
          <VulnIndicator
            count={pkg.vulnerabilities?.length}
            severity={pkg.vulnerabilities?.[0]?.severity}
          />
        </div>
      </div>

      {isExpanded && (
        <div className="px-10 pb-4 bg-gray-800/30 space-y-3">
          {pkg.description && <p className="text-sm text-gray-400">{pkg.description}</p>}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Ecosystem:</span>
              <span className="ml-2 capitalize">{pkg.ecosystem || "unknown"}</span>
            </div>
            <div>
              <span className="text-gray-400">PURL:</span>
              <span className="ml-2 font-mono text-xs truncate">{pkg.purl || "N/A"}</span>
            </div>
            {pkg.supplier && (
              <div>
                <span className="text-gray-400">Supplier:</span>
                <span className="ml-2">{pkg.supplier}</span>
              </div>
            )}
            {pkg.hash && (
              <div>
                <span className="text-gray-400">Hash:</span>
                <span className="ml-2 font-mono text-xs">{pkg.hash.substring(0, 16)}...</span>
              </div>
            )}
          </div>

          {pkg.vulnerabilities && pkg.vulnerabilities.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-700/50">
              <h5 className="text-sm font-medium text-gray-200 mb-2">Known Vulnerabilities</h5>
              <div className="space-y-2">
                {pkg.vulnerabilities.map((vuln, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 bg-gray-800/30 rounded-lg border border-gray-700/50"
                  >
                    <div className="flex items-center gap-2">
                      <ExclamationTriangleIcon
                        className={`w-4 h-4 ${
                          vuln.severity === "critical"
                            ? "text-red-500"
                            : vuln.severity === "high"
                              ? "text-orange-500"
                              : "text-yellow-500"
                        }`}
                      />
                      <span className="font-mono text-sm">{vuln.id}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">CVSS: {vuln.cvss || "N/A"}</span>
                      <a
                        href={`https://nvd.nist.gov/vuln/detail/${vuln.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300"
                      >
                        <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {pkg.externalRefs && pkg.externalRefs.length > 0 && (
            <div className="flex gap-2 mt-2">
              {pkg.externalRefs.map((ref, i) => (
                <a
                  key={i}
                  href={ref.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-cyan-400 hover:underline flex items-center gap-1"
                >
                  {ref.type} <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main component
const SBOMViewer = ({ repositoryPath = null, sbomData = null, onGenerate: _onGenerate }) => {
  const [format, setFormat] = useState("spdx");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterVuln, setFilterVuln] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [expandedPkg, setExpandedPkg] = useState(null);

  // Generate SBOM mutation
  const generateMutation = useMutation({
    mutationFn: async (params) => {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/api/enterprise/sbom/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify(params),
      });
      if (!response.ok) throw new Error("Failed to generate SBOM");
      return response.json();
    },
  });

  // Fetch SBOM formats info
  const { data: formatsData } = useQuery({
    queryKey: ["sbom-formats"],
    queryFn: async () => {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE_URL}/api/enterprise/sbom/formats`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
      });
      if (!response.ok) throw new Error("Failed to fetch formats");
      return response.json();
    },
  });

  const handleGenerate = () => {
    if (!repositoryPath) return;

    generateMutation.mutate({
      repository_path: repositoryPath,
      format: format,
      include_dev_deps: false,
      enrich_vulnerabilities: true,
    });
  };

  const handleDownload = (outputType = "json") => {
    const data = generateMutation.data?.sbom || sbomData;
    if (!data) return;

    const content = JSON.stringify(data, null, 2);
    const blob = new Blob([content], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `sbom-${format}.${outputType}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    const data = generateMutation.data?.sbom || sbomData;
    if (!data) return;

    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
  };

  const currentSBOM = generateMutation.data?.sbom || sbomData;
  const packages = currentSBOM?.packages || currentSBOM?.components || [];

  // Filter packages
  const filteredPackages = packages.filter((pkg) => {
    const matchesSearch =
      !searchTerm ||
      pkg.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pkg.version?.includes(searchTerm);

    const matchesVuln = !filterVuln || (pkg.vulnerabilities && pkg.vulnerabilities.length > 0);

    return matchesSearch && matchesVuln;
  });

  // Count stats
  const totalPackages = packages.length;
  const vulnPackages = packages.filter((p) => p.vulnerabilities?.length > 0).length;
  const licenses = [...new Set(packages.map((p) => p.license).filter(Boolean))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Software Bill of Materials</h2>
          <p className="text-gray-400">Generate and view SBOM for your project</p>
        </div>
        <div className="flex items-center gap-2">
          {currentSBOM && (
            <>
              <button
                onClick={() => setShowRaw(!showRaw)}
                className="px-3 py-2 border border-gray-700/50 rounded-lg text-sm hover:bg-gray-800/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <CodeBracketIcon className="w-4 h-4 inline mr-1" />
                {showRaw ? "View Parsed" : "View Raw"}
              </button>
              <button
                onClick={copyToClipboard}
                className="px-3 py-2 border border-gray-700/50 rounded-lg text-sm hover:bg-gray-800/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <ClipboardIcon className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDownload("json")}
                className="px-3 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold text-sm hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
              >
                <ArrowDownTrayIcon className="w-4 h-4 inline mr-1" />
                Download
              </button>
            </>
          )}
        </div>
      </div>

      {/* Generate Form */}
      {repositoryPath && (
        <Card padding="lg">
          <h3 className="font-medium text-white mb-4">Generate SBOM</h3>
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Repository Path
              </label>
              <input
                type="text"
                value={repositoryPath}
                disabled
                className="w-full px-3 py-2 border border-gray-700/50 rounded-lg bg-gray-800/30"
              />
            </div>
            <div className="w-48">
              <label className="block text-sm font-medium text-gray-200 mb-2">Format</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full px-3 py-2 border border-gray-700/50 rounded-lg"
              >
                <option value="spdx">SPDX 2.3</option>
                <option value="cyclonedx">CycloneDX 1.5</option>
              </select>
            </div>
            <button
              onClick={handleGenerate}
              disabled={generateMutation.isPending}
              className="px-4 py-2 rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold hover:from-cyan-300 hover:via-violet-400 hover:to-cyan-300 shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-all duration-200 disabled:opacity-50 flex items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
            >
              {generateMutation.isPending ? (
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
              ) : (
                <DocumentTextIcon className="w-4 h-4" />
              )}
              Generate
            </button>
          </div>
        </Card>
      )}

      {/* Format Info */}
      {formatsData?.formats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {formatsData.formats.map((fmt) => (
            <div
              key={fmt.id}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                format === fmt.id
                  ? "border-cyan-500 bg-cyan-900/30"
                  : "border-gray-700/50 hover:border-gray-600"
              }`}
              onClick={() => setFormat(fmt.id)}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-white">{fmt.name}</h4>
                  <p className="text-sm text-gray-400 mt-1">{fmt.description}</p>
                </div>
                <LockClosedIcon className="w-4 h-4 text-gray-400" />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {fmt.compliance?.map((c, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 text-xs bg-gray-700/50 text-gray-400 rounded"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {generateMutation.isError && (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 text-red-400">
          <ExclamationTriangleIcon className="w-5 h-5 inline mr-2" />
          Error generating SBOM: {generateMutation.error?.message}
        </div>
      )}

      {currentSBOM && (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Packages</p>
                  <p className="text-2xl font-bold text-white">{totalPackages}</p>
                </div>
                <CubeIcon className="w-8 h-8 text-cyan-500 opacity-50" />
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Vulnerable</p>
                  <p
                    className={`text-2xl font-bold ${
                      vulnPackages > 0 ? "text-red-400" : "text-green-400"
                    }`}
                  >
                    {vulnPackages}
                  </p>
                </div>
                <ExclamationTriangleIcon
                  className={`w-8 h-8 opacity-50 ${
                    vulnPackages > 0 ? "text-red-500" : "text-green-500"
                  }`}
                />
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Unique Licenses</p>
                  <p className="text-2xl font-bold text-white">{licenses.length}</p>
                </div>
                <ShieldCheckIcon className="w-8 h-8 text-purple-500 opacity-50" />
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Format</p>
                  <p className="text-2xl font-bold text-white uppercase">{format}</p>
                </div>
                <CodeBracketIcon className="w-8 h-8 text-indigo-500 opacity-50" />
              </div>
            </Card>
          </div>

          {/* Raw View */}
          {showRaw ? (
            <div className="bg-gray-900 rounded-xl p-4 overflow-auto max-h-[600px]">
              <pre className="text-green-400 text-sm font-mono">
                {JSON.stringify(currentSBOM, null, 2)}
              </pre>
            </div>
          ) : (
            <>
              {/* Search and Filter */}
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search packages..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-700/50 rounded-lg"
                  />
                </div>
                <button
                  onClick={() => setFilterVuln(!filterVuln)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900 ${
                    filterVuln
                      ? "bg-red-900/30 text-red-400 border border-red-700/50"
                      : "border border-gray-700/50 text-gray-200 hover:bg-gray-800/30"
                  }`}
                >
                  <ExclamationTriangleIcon className="w-4 h-4" />
                  Vulnerable Only
                </button>
              </div>

              {/* Package List */}
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl">
                <div className="p-4 border-b border-gray-700/50 flex items-center justify-between">
                  <h3 className="font-medium text-white">
                    Dependencies ({filteredPackages.length})
                  </h3>
                  <span className="text-sm text-gray-400">
                    {vulnPackages > 0 && (
                      <span className="text-red-400">{vulnPackages} with vulnerabilities</span>
                    )}
                  </span>
                </div>

                <div style={{ height: 500 }}>
                  {filteredPackages.length === 0 ? (
                    <div className="text-center text-gray-400 py-12">
                      {searchTerm || filterVuln
                        ? "No packages match the current filters"
                        : "No packages found"}
                    </div>
                  ) : (
                    <List
                      height={500}
                      width="100%"
                      itemCount={filteredPackages.length}
                      itemSize={52}
                      itemData={{
                        packages: filteredPackages,
                        expandedPkg,
                        onToggle: (index) => setExpandedPkg(expandedPkg === index ? null : index),
                      }}
                    >
                      {({ index, style, data }) => (
                        <div style={{ ...style, overflow: "visible" }}>
                          <PackageRow
                            pkg={data.packages[index]}
                            isExpanded={data.expandedPkg === index}
                            onToggle={() => data.onToggle(index)}
                          />
                        </div>
                      )}
                    </List>
                  )}
                </div>
              </div>
            </>
          )}

          {/* SBOM Metadata */}
          <div className="bg-gray-800/30 rounded-xl p-4 text-sm">
            <h4 className="font-medium text-gray-200 mb-2 flex items-center gap-2">
              <InformationCircleIcon className="w-4 h-4" />
              SBOM Metadata
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-gray-400">
              <div>
                <span className="text-gray-400">Created:</span>
                <span className="ml-2">
                  {currentSBOM.creationInfo?.created || currentSBOM.metadata?.timestamp || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Version:</span>
                <span className="ml-2">
                  {currentSBOM.spdxVersion || currentSBOM.specVersion || "N/A"}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Tool:</span>
                <span className="ml-2">
                  {currentSBOM.creationInfo?.creators?.[0] ||
                    currentSBOM.metadata?.tools?.[0]?.name ||
                    "ONYX"}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Name:</span>
                <span className="ml-2">
                  {currentSBOM.name || currentSBOM.metadata?.component?.name || "N/A"}
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {!currentSBOM && !generateMutation.isPending && (
        <div className="text-center py-12 bg-gray-800/30 rounded-xl">
          <DocumentTextIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-400">No SBOM generated yet</p>
          {repositoryPath && (
            <p className="text-sm text-gray-400 mt-2">Click "Generate" to create an SBOM</p>
          )}
        </div>
      )}
    </div>
  );
};

export default SBOMViewer;
