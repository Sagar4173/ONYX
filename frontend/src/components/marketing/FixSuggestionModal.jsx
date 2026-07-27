import { motion, AnimatePresence } from "framer-motion";
import { ExclamationTriangleIcon, LockClosedIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useNavigate } from "react-router-dom";
import { fixSuggestions } from "./landingPageData";

const FixSuggestionModal = ({ type, onClose }) => {
  const navigate = useNavigate();
  const suggestion = fixSuggestions[type];
  const isSql = type === "sql";

  return (
    <AnimatePresence>
      {suggestion && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="bg-gray-900 border border-gray-700 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${isSql ? "bg-red-500/20" : "bg-amber-500/20"}`}>
                {isSql ? (
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-400" />
                ) : (
                  <LockClosedIcon className="w-6 h-6 text-amber-400" />
                )}
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">{suggestion.title}</h3>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${isSql ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"}`}
                >
                  {suggestion.severity}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>
        <div className="p-6 space-y-6">
          <div>
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Problem
            </h4>
            <p className="text-gray-300">{suggestion.problem}</p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Fix
            </h4>
            <pre className="bg-gray-950 border border-gray-800 rounded-xl p-4 overflow-x-auto">
              <code className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                {suggestion.fix}
              </code>
            </pre>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
              Explanation
            </h4>
            <p className="text-gray-300">{suggestion.explanation}</p>
          </div>
        </div>
        <div className="p-6 border-t border-gray-800 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 transition-all"
          >
            Close
          </button>
          <button
            onClick={() => {
              navigate("/register");
              onClose();
            }}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
          >
            Start Free Trial
          </button>
        </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default FixSuggestionModal;
