import { useState, useEffect } from "react";

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
          setSystemInfo((prev) => ({
            ...prev,
            version: "1.0.0",
            build: new Date().toISOString().split("T")[0],
            environment: import.meta.env.DEV ? "Development" : "Production",
            database: { status: "error", message: "Error checking" },
          }));
        }
      } catch {
        if (!cancelled) {
          setSystemInfo((prev) => ({
            ...prev,
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

  const getStatusColor = (status) => {
    switch (status) {
      case "connected":
        return "text-green-400";
      case "disconnected":
      case "error":
        return "text-red-400";
      case "checking":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="mt-3 space-y-2 text-sm">
      <div className="flex justify-between">
        <span className="text-gray-400">Version:</span>
        <span className="text-white">{systemInfo.version}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Build:</span>
        <span className="text-white">{systemInfo.build}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Environment:</span>
        <span className="text-white">{systemInfo.environment}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Database:</span>
        <span className={getStatusColor(systemInfo.database.status)}>
          {systemInfo.database.message}
        </span>
      </div>
      <div className="flex justify-between">
        <span className="text-gray-400">Scanners:</span>
        <span className={systemInfo.scanners.active > 0 ? "text-green-400" : "text-yellow-400"}>
          {systemInfo.scanners.active} Active / {systemInfo.scanners.total} Total
        </span>
      </div>
    </div>
  );
};

export default SystemInfo;
