import {
  ArrowDownTrayIcon,
  PrinterIcon,
  DocumentTextIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import toast from "react-hot-toast";

// eslint-disable-next-line react-refresh/only-export-components
export const downloadReport = async (format = "json", reportId) => {
  try {
    toast.loading("Preparing download...", { id: "download" });

    const token = localStorage.getItem("access_token");
    const API_BASE_URL = import.meta.env.DEV
      ? "http://127.0.0.1:8000/api"
      : import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "/api";

    const response = await fetch(`${API_BASE_URL}/reports/${reportId}/download?format=${format}`, {
      headers: {
        Authorization: token ? `Bearer ${token}` : "",
      },
    });

    if (!response.ok) {
      if (response.status === 401) throw new Error("Authentication required. Please log in again.");
      if (response.status === 403) throw new Error("Access denied to this report.");
      throw new Error("Download failed");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const extension = format === "csv" ? "csv" : "json";
    a.download = `security-report-${reportId}.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success("Download completed!", { id: "download" });
  } catch (error) {
    toast.error(error.message || "Failed to download report. Please try again.", {
      id: "download",
    });
    console.error("Download error:", error);
  }
};

// eslint-disable-next-line react-refresh/only-export-components
export const printReport = () => {
  window.print();
};

export const ExportDropdown = ({ reportId, onGeneratePDF, isGenerating }) => {
  return (
    <div className="relative group" role="menu" aria-label="Export options">
      <button
        aria-haspopup="true"
        aria-expanded="false"
        className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm flex items-center gap-2 transition-all border border-gray-700/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      >
        <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
        Export
        <ChevronDownIcon className="h-3 w-3" aria-hidden="true" />
      </button>
      <div className="absolute right-0 mt-2 w-48 bg-gray-900 border border-gray-700/50 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible transition-all duration-200 z-10">
        <div className="p-2">
          <button
            onClick={onGeneratePDF}
            disabled={isGenerating}
            role="menuitem"
            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:opacity-50"
          >
            <DocumentTextIcon className="h-4 w-4" aria-hidden="true" />{" "}
            {isGenerating ? "Generating..." : "PDF Report"}
          </button>
          <button
            onClick={() => downloadReport("json", reportId)}
            role="menuitem"
            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            <DocumentTextIcon className="h-4 w-4" aria-hidden="true" /> JSON Data
          </button>
          <button
            onClick={() => downloadReport("csv", reportId)}
            role="menuitem"
            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            <DocumentTextIcon className="h-4 w-4" aria-hidden="true" /> CSV Spreadsheet
          </button>
          <button
            onClick={printReport}
            role="menuitem"
            className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-gray-800/50 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
          >
            <PrinterIcon className="h-4 w-4" aria-hidden="true" /> Print Report
          </button>
        </div>
      </div>
    </div>
  );
};
