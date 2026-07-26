import {
  DocumentTextIcon,
  ShieldCheckIcon,
  FolderIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArchiveBoxIcon,
} from "@heroicons/react/24/outline";

export const policyTypes = [
  { value: "scan_results", label: "Scan Results", icon: DocumentTextIcon },
  { value: "audit_logs", label: "Audit Logs", icon: ShieldCheckIcon },
  { value: "user_data", label: "User Data", icon: "👤" },
  { value: "reports", label: "Reports", icon: FolderIcon },
  { value: "vulnerability_data", label: "Vulnerability Data", icon: ExclamationTriangleIcon },
  { value: "compliance_records", label: "Compliance Records", icon: CheckCircleIcon },
  { value: "backup_data", label: "Backup Data", icon: ArchiveBoxIcon },
];

export const retentionActions = [
  {
    value: "delete",
    label: "Delete",
    color: "text-red-400",
    description: "Permanently delete data",
  },
  {
    value: "archive",
    label: "Archive",
    color: "text-cyan-400",
    description: "Move to archive storage",
  },
  {
    value: "compress",
    label: "Compress",
    color: "text-green-400",
    description: "Compress and store",
  },
  {
    value: "anonymize",
    label: "Anonymize",
    color: "text-yellow-400",
    description: "Remove PII and retain",
  },
];

export const getActionColor = (action) => {
  const actionConfig = retentionActions.find((a) => a.value === action);
  return actionConfig?.color || "text-gray-400";
};

export const formatDate = (dateString) => new Date(dateString).toLocaleString();
