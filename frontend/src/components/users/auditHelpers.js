import {
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

export const eventTypes = [
  { value: "user.login", label: "User Login", category: "User Management" },
  { value: "user.logout", label: "User Logout", category: "User Management" },
  { value: "user.created", label: "User Created", category: "User Management" },
  { value: "user.updated", label: "User Updated", category: "User Management" },
  { value: "user.deleted", label: "User Deleted", category: "User Management" },
  { value: "scan.started", label: "Scan Started", category: "Security" },
  { value: "scan.completed", label: "Scan Completed", category: "Security" },
  { value: "scan.failed", label: "Scan Failed", category: "Security" },
  { value: "vulnerability.detected", label: "Vulnerability Detected", category: "Security" },
  { value: "vulnerability.fixed", label: "Vulnerability Fixed", category: "Security" },
  { value: "compliance.assessment", label: "Compliance Assessment", category: "Compliance" },
  { value: "policy.created", label: "Policy Created", category: "Policy" },
  { value: "policy.updated", label: "Policy Updated", category: "Policy" },
  { value: "policy.deleted", label: "Policy Deleted", category: "Policy" },
  { value: "settings.changed", label: "Settings Changed", category: "Configuration" },
  { value: "api.key.created", label: "API Key Created", category: "Security" },
  { value: "api.key.revoked", label: "API Key Revoked", category: "Security" },
  { value: "auth.failed", label: "Auth Failed", category: "Security" },
  { value: "suspicious.activity", label: "Suspicious Activity", category: "Security" },
];

export const severityLevels = ["info", "warning", "error", "critical"];

export const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case "critical":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    case "error":
      return "bg-orange-500/20 text-orange-400 border-orange-500/30";
    case "warning":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "info":
    default:
      return "bg-cyan-500/20 text-cyan-400 border-cyan-500/30";
  }
};

export const getSeverityIcon = (severity) => {
  switch (severity?.toLowerCase()) {
    case "critical":
    case "error":
      return <XCircleIcon className="w-4 h-4" />;
    case "warning":
      return <ExclamationTriangleIcon className="w-4 h-4" />;
    case "info":
    default:
      return <InformationCircleIcon className="w-4 h-4" />;
  }
};

export const formatTimestamp = (timestamp) => new Date(timestamp).toLocaleString();
