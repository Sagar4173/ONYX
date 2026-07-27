import { motion } from "framer-motion";
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "@heroicons/react/24/outline";
import { GlassCard } from "../../layouts";
import { eventTypes, severityLevels } from "./auditHelpers.jsx";

const sectionAnim = {
  hidden: { opacity: 0 },
  show: { transition: { staggerChildren: 0.05 } },
};
const filterItem = { hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } };

const AuditFilters = ({ filters, setFilters, showFilters, setShowFilters, usersData }) => (
  <GlassCard className="mb-6">
    <div className="flex flex-col lg:flex-row gap-3 lg:gap-4">
      <div className="flex-1 relative">
        <MagnifyingGlassIcon className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 lg:w-5 lg:h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search logs..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="w-full pl-10 lg:pl-12 pr-4 py-2.5 lg:py-3 bg-gray-800/40 border border-gray-600/50 rounded-xl text-sm lg:text-base text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
        />
      </div>

      <button
        onClick={() => setShowFilters(!showFilters)}
        className="flex items-center justify-center gap-2 px-4 lg:px-6 py-2.5 lg:py-3 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/30 rounded-xl text-cyan-300 transition-all text-sm lg:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        <FunnelIcon className="w-4 h-4 lg:w-5 lg:h-5" />
        <span>Filters</span>
        {showFilters ? (
          <ChevronUpIcon className="w-3.5 h-3.5 lg:w-4 lg:h-4" />
        ) : (
          <ChevronDownIcon className="w-3.5 h-3.5 lg:w-4 lg:h-4" />
        )}
      </button>
    </div>

    {showFilters && (
      <motion.div
        variants={sectionAnim}
        initial="hidden"
        animate="show"
        className="mt-4 pt-4 border-t border-gray-700/50 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <motion.div variants={filterItem}>
          <label className="block text-xs lg:text-sm font-medium text-gray-300 mb-2">
            Event Types
          </label>
          <select
            multiple
            value={filters.event_types}
            onChange={(e) =>
              setFilters({
                ...filters,
                event_types: Array.from(e.target.selectedOptions, (option) => option.value),
              })
            }
            className="w-full px-3 lg:px-4 py-2 bg-gray-800 border border-gray-600/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
            size="5"
          >
            {eventTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </motion.div>

        <motion.div variants={filterItem}>
          <label className="block text-sm font-medium text-gray-300 mb-2">Users</label>
          <select
            multiple
            value={filters.users}
            onChange={(e) =>
              setFilters({
                ...filters,
                users: Array.from(e.target.selectedOptions, (option) => option.value),
              })
            }
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
            size="5"
          >
            {usersData?.users?.map((user) => (
              <option key={user} value={user}>
                {user}
              </option>
            ))}
          </select>
        </motion.div>

        <motion.div variants={filterItem}>
          <label className="block text-sm font-medium text-gray-300 mb-2">Start Date</label>
          <input
            type="datetime-local"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="w-full px-4 py-2 bg-gray-800/40 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <label className="block text-sm font-medium text-gray-300 mb-2 mt-2">End Date</label>
          <input
            type="datetime-local"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="w-full px-4 py-2 bg-gray-800/40 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </motion.div>

        <motion.div variants={filterItem}>
          <label className="block text-sm font-medium text-gray-300 mb-2">Severity</label>
          <select
            value={filters.severity}
            onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="">All Severities</option>
            {severityLevels.map((level) => (
              <option key={level} value={level}>
                {level.toUpperCase()}
              </option>
            ))}
          </select>
        </motion.div>
      </motion.div>
    )}
  </GlassCard>
);

export default AuditFilters;
