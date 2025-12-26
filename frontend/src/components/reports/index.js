/**
 * Reports Components - Security reports and analysis
 *
 * Note: ComplianceReport has been deprecated and merged into EnhancedReportDetails
 * All /compliance/:reportId routes now redirect to /report/:reportId
 */
export { default as ReportDetails } from "./ReportDetails";
export { default as EnhancedReportDetails } from "./EnhancedReportDetails";
// ComplianceReport deprecated - use EnhancedReportDetails instead
