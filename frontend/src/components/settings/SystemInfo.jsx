import { useState, useEffect } from "react";

const statusDot = {
  connected: "bg-green-500 shadow-lg shadow-green-500/30",
  disconnected: "bg-red-500 shadow-lg shadow-red-500/30",
  error: "bg-red-500 shadow-lg shadow-red-500/30",
  checking: "bg-yellow-500 shadow-lg shadow-yellow-500/30",
  offline: "bg-gray-500 shadow-lg shadow-gray-500/30",
};

const statusLabel = {
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Error",
  checking: "Checking...",
  offline: "Offline",
};

const SystemInfo = () => {
  const [systemInfo, setSystemInfo] = useState({
    version: "Loading...",
    build: "Loading...",
    environment: "Loading...",
    database: { status: "checking", message: "Checking..." },
    scanners: { active: 0, total: 0 },
  });

  useEffect(() => {
    let cancelled = false;
    const fetchSystemInfo = async () => {
      try {
        const API_URL = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";
        const healthResponse = await fetch(`${API_URL}/api/health`);

        if (healthResponse.ok) {
          const healthData = await healthResponse.json();
          if (!cancelled) {
            setSystemInfo({
              version: healthData.version || "1.0.0",
              build: healthData.build_date || new Date().toISOString().split("T")[0],
              environment: import.meta.env.DEV ? "Development" : "Production",
              database: {
                status: healthData.database?.connected ? "connected" : "disconnected",
                message: healthData.database?.connected ? "Connected" : "Disconnected",
              },
              scanners: {
                active: healthData.scanners?.active || 0,
                total: healthData.scanners?.total || 4,
              },
            });
          }
        } else if (!cancelled) {
          setSystemInfo((p) => ({
            ...p,
            database: { status: "error", message: "Error checking" },
          }));
        }
      } catch {
        if (!cancelled) {
          setSystemInfo((p) => ({
            ...p,
            version: "1.0.0",
            build: new Date().toISOString().split("T")[0],
            environment: import.meta.env.DEV ? "Development" : "Production",
            database: { status: "offline", message: "Offline" },
            scanners: { active: 0, total: 4 },
          }));
        }
      }
    };

    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const dbDot = statusDot[systemInfo.database.status] || statusDot.offline;
  const dbLabel = statusLabel[systemInfo.database.status] || "Unknown";

  return (
    <div className="mt-3 space-y-2 text-sm">
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Version</span>
        <span className="text-white font-mono text-xs">{systemInfo.version}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Build</span>
        <span className="text-white font-mono text-xs">{systemInfo.build}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Environment</span>
        <span className="text-white">{systemInfo.environment}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Database</span>
        <span className="flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${dbDot}`} />
          <span className="text-gray-300">{dbLabel}</span>
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Scanners</span>
        <span className="flex items-center gap-2">
          <div className="h-1.5 w-16 bg-gray-700/50 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all"
              style={{
                width: `${
                  systemInfo.scanners.total > 0
                    ? (systemInfo.scanners.active / systemInfo.scanners.total) * 100
                    : 0
                }%`,
              }}
            />
          </div>
          <span
            className={
              systemInfo.scanners.active > 0 ? "text-green-400" : "text-yellow-400"
            }
          >
            {systemInfo.scanners.active}/{systemInfo.scanners.total}
          </span>
        </span>
      </div>
    </div>
  );
};

export default SystemInfo;
