import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowDownTrayIcon,
  PrinterIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  DocumentArrowDownIcon,
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
  }
};

// eslint-disable-next-line react-refresh/only-export-components
export const printReport = () => {
  window.print();
};

const menuItems = [
  { label: "PDF Report", icon: DocumentArrowDownIcon, action: "pdf", shortcut: "⌘P" },
  { label: "JSON Data", icon: DocumentTextIcon, action: "json", shortcut: "⌘J" },
  { label: "CSV Spreadsheet", icon: DocumentTextIcon, action: "csv", shortcut: "⌘C" },
  { label: "Print Report", icon: PrinterIcon, action: "print", shortcut: "⌘↑" },
];

export const ExportDropdown = ({ reportId, onGeneratePDF, isGenerating }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleAction = (action) => {
    setIsOpen(false);
    if (action === "print") {
      printReport();
    } else if (action === "pdf") {
      onGeneratePDF();
    } else {
      downloadReport(action, reportId);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-400 via-violet-500 to-cyan-400 text-white font-semibold text-sm shadow-lg hover:shadow-xl hover:shadow-cyan-500/20 transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <ArrowDownTrayIcon className="h-4 w-4" />
        Export
        <motion.span animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDownIcon className="h-3 w-3" />
        </motion.span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 mt-2 w-52 overflow-hidden rounded-xl border border-gray-700/50 bg-gray-900/95 backdrop-blur-xl shadow-2xl z-50"
          >
            <motion.div
              initial="hidden"
              animate="visible"
              variants={{
                visible: { transition: { staggerChildren: 0.03 } },
              }}
              className="p-1.5"
            >
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isPDF = item.action === "pdf";
                return (
                  <motion.button
                    key={item.action}
                    variants={{
                      hidden: { opacity: 0, x: -8 },
                      visible: { opacity: 1, x: 0 },
                    }}
                    onClick={() => handleAction(item.action)}
                    disabled={isPDF && isGenerating}
                    role="menuitem"
                    className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-gradient-to-r hover:from-cyan-500/10 hover:via-violet-500/10 hover:to-cyan-500/10 rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <div className="p-1 rounded-md bg-gray-800/50">
                      <Icon className="h-4 w-4 text-cyan-400" />
                    </div>
                    <span className="flex-1 text-left">
                      {isPDF && isGenerating ? "Generating..." : item.label}
                    </span>
                    {item.shortcut && (
                      <span className="text-[10px] text-gray-600 font-mono">{item.shortcut}</span>
                    )}
                  </motion.button>
                );
              })}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
