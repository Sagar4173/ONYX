import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDownIcon, CodeBracketIcon } from "@heroicons/react/24/outline";

const LEVEL_COLORS = {
  INFO: "text-cyan-400",
  WARN: "text-yellow-400",
  ERROR: "text-red-400",
  DEBUG: "text-gray-500",
  SCAN: "text-green-400",
};

const LiveConsole = ({ logLines = [], liveScanData, isExpanded: controlledExpanded, onToggle: controlledToggle }) => {
  const lines = logLines.length > 0 ? logLines : (liveScanData?.scanLog ?? []);
  const [localExpanded, setLocalExpanded] = useState(false);
  const bottomRef = useRef(null);

  const isExpanded = controlledExpanded ?? localExpanded;
  const onToggle = controlledToggle ?? (() => setLocalExpanded((v) => !v));

  useEffect(() => {
    if (liveScanData?.isScanActive && !localExpanded) {
      setLocalExpanded(true);
    }
  }, [liveScanData?.isScanActive, localExpanded]);

  useEffect(() => {
    if (isExpanded && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [lines.length, isExpanded]);

  return (
    <div className="mb-6 rounded-xl overflow-hidden border border-gray-700/50">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-900/80 hover:bg-gray-900 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500"
      >
        <div className="flex items-center space-x-2">
          <CodeBracketIcon className="h-4 w-4 text-cyan-400" />
          <span className="text-sm font-medium text-white">Scan Console</span>
          <span className="text-xs text-gray-500">({lines.length} lines)</span>
        </div>
        <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDownIcon className="h-4 w-4 text-gray-400" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <pre className="bg-gray-950 p-4 text-xs leading-6 font-mono overflow-auto max-h-64 custom-scrollbar">
              <code>
                {lines.length === 0 ? (
                  <span className="text-gray-600">Waiting for scan output...</span>
                ) : (
                  lines.map((line, i) => (
                    <div key={i} className="whitespace-pre-wrap break-all">
                      <span className="text-gray-600">[{line.timestamp}] </span>
                      <span className={LEVEL_COLORS[line.level] || "text-gray-300"}>
                        [{line.level}]
                      </span>
                      <span className="text-gray-300"> {line.message}</span>
                    </div>
                  ))
                )}
                <div ref={bottomRef} />
                {lines.length > 0 && (
                  <span className="inline-block w-2 h-4 bg-cyan-400 animate-pulse ml-1 align-middle" />
                )}
              </code>
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default LiveConsole;
