const AuditPagination = ({ page, setPage, limit, total }) => (
  <div className="px-6 py-4 border-t border-gray-700/50 flex items-center justify-between">
    <p className="text-sm text-gray-400">
      Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} logs
    </p>
    <div className="flex gap-2">
      <button
        onClick={() => setPage(page - 1)}
        disabled={page === 1}
        className="px-4 py-2 bg-gray-800/30 hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700/50 rounded-lg text-white transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        Previous
      </button>
      <button
        onClick={() => setPage(page + 1)}
        disabled={page * limit >= total}
        className="px-4 py-2 bg-gray-800/30 hover:bg-gray-700/50 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700/50 rounded-lg text-white transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
      >
        Next
      </button>
    </div>
  </div>
);

export default AuditPagination;
