const SeverityBar = ({ data }) => {
  const total = (data?.critical || 0) + (data?.high || 0) + (data?.medium || 0) + (data?.low || 0);
  if (total === 0)
    return <p className="text-sm text-gray-500 text-center py-4">No vulnerabilities found</p>;

  const getWidth = (count) => `${(count / total) * 100}%`;

  return (
    <div className="space-y-3">
      <div className="flex h-3 rounded-full overflow-hidden bg-gray-800/50">
        {data?.critical > 0 && (
          <div
            className="bg-gradient-to-r from-red-500 to-rose-500 transition-all duration-500"
            style={{ width: getWidth(data.critical) }}
          />
        )}
        {data?.high > 0 && (
          <div
            className="bg-gradient-to-r from-orange-500 to-amber-500 transition-all duration-500"
            style={{ width: getWidth(data.high) }}
          />
        )}
        {data?.medium > 0 && (
          <div
            className="bg-gradient-to-r from-yellow-500 to-lime-500 transition-all duration-500"
            style={{ width: getWidth(data.medium) }}
          />
        )}
        {data?.low > 0 && (
          <div
            className="bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
            style={{ width: getWidth(data.low) }}
          />
        )}
      </div>
      <div className="flex flex-wrap gap-4 text-xs">
        {[
          { label: "Critical", count: data?.critical || 0, color: "from-red-500 to-rose-500" },
          { label: "High", count: data?.high || 0, color: "from-orange-500 to-amber-500" },
          { label: "Medium", count: data?.medium || 0, color: "from-yellow-500 to-lime-500" },
          { label: "Low", count: data?.low || 0, color: "from-blue-500 to-cyan-500" },
        ].map(({ label, count, color }) => (
          <div key={label} className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${color}`} />
            <span className="text-gray-400">
              {label}: <span className="text-white font-medium">{count}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SeverityBar;
