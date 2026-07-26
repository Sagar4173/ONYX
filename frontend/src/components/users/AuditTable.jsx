import { motion } from "framer-motion";
import { ClockIcon, UserIcon, GlobeAltIcon, ChevronDownIcon, ChevronUpIcon } from "@heroicons/react/24/outline";
import { ShieldCheckIcon } from "@heroicons/react/24/solid";
import { EmptyState } from "../../layouts";
import { getSeverityColor, getSeverityIcon, formatTimestamp } from "./auditHelpers";
import AuditPagination from "./AuditPagination";

const AuditRow = ({ log, isExpanded, onToggle }) => (
  <>
    <motion.tr
      layout
      className="border-b border-gray-700/30 hover:bg-gray-800/30 transition-colors cursor-pointer"
      onClick={() => onToggle(log.id)}
    >
      <td className="px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-gray-300">
          <ClockIcon className="w-4 h-4 text-gray-500" />
          {formatTimestamp(log.timestamp)}
        </div>
      </td>
      <td className="px-6 py-4">
        <span className="inline-flex items-center gap-2 px-3 py-1 bg-cyan-500/20 text-cyan-300 rounded-lg text-sm font-medium">
          {log.event_type}
        </span>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-gray-300">
          <UserIcon className="w-4 h-4 text-gray-500" />
          {log.user_id || "System"}
        </div>
      </td>
      <td className="px-6 py-4 text-sm text-gray-300 max-w-xs truncate">{log.description}</td>
      <td className="px-6 py-4">
        <span
          className={`inline-flex items-center gap-1 px-3 py-1 border rounded-lg text-xs font-medium ${getSeverityColor(log.severity)}`}
        >
          {getSeverityIcon(log.severity)}
          {log.severity?.toUpperCase()}
        </span>
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <GlobeAltIcon className="w-4 h-4" />
          {log.ip_address || "N/A"}
        </div>
      </td>
      <td className="px-6 py-4">
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(log.id); }}
          className="text-cyan-400 hover:text-cyan-300 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
        >
          {isExpanded ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
        </button>
      </td>
    </motion.tr>
    {isExpanded && (
      <motion.tr
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        <td colSpan="7" className="px-6 py-4 bg-gray-800/30">
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-400 mb-1">Event ID</p>
                <p className="text-sm text-white font-mono">{log.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-400 mb-1">User Agent</p>
                <p className="text-sm text-white truncate">{log.user_agent || "N/A"}</p>
              </div>
              {log.metadata && (
                <div className="col-span-2">
                  <p className="text-sm font-medium text-gray-400 mb-1">Metadata</p>
                  <pre className="text-xs text-gray-300 bg-black/30 p-3 rounded-lg overflow-x-auto">
                    {JSON.stringify(log.metadata, null, 2)}
                  </pre>
                </div>
              )}
              {log.integrity_hash && (
                <div className="col-span-2">
                  <p className="text-sm font-medium text-gray-400 mb-1">Integrity Hash (SHA-256)</p>
                  <p className="text-xs text-gray-300 font-mono break-all">{log.integrity_hash}</p>
                </div>
              )}
            </div>
          </div>
        </td>
      </motion.tr>
    )}
  </>
);

const AuditTable = ({
  auditData,
  isLoading,
  expandedLog,
  setExpandedLog,
  limit,
  page,
  setPage,
}) => (
  <div className="bg-gray-800/40 backdrop-blur-sm border border-gray-700/50 rounded-xl overflow-hidden shadow-xl">
    {isLoading ? (
      <div className="p-12 text-center">
        <div className="relative w-12 h-12 mx-auto mb-4">
          <div className="absolute inset-0 rounded-full border-2 border-gray-700 border-t-cyan-500 animate-spin" />
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-b-violet-500 animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
        </div>
        <p className="text-gray-400">Loading audit logs...</p>
      </div>
    ) : !auditData?.logs?.length ? (
      <div className="p-12">
        <EmptyState
          icon={<ShieldCheckIcon className="h-12 w-12" />}
          title="No audit logs found"
          description="Try adjusting your filters"
        />
      </div>
    ) : (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700/50">
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Timestamp</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Event Type</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">User</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Description</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Severity</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">IP Address</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Details</th>
            </tr>
          </thead>
          <tbody>
            {auditData.logs.map((log) => (
              <AuditRow
                key={log.id}
                log={log}
                isExpanded={expandedLog === log.id}
                onToggle={setExpandedLog}
              />
            ))}
          </tbody>
        </table>
      </div>
    )}

    {auditData?.total > limit && (
      <AuditPagination page={page} setPage={setPage} limit={limit} total={auditData.total} />
    )}
  </div>
);

export default AuditTable;
