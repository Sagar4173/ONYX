// MongoDB Initialization Script for SecureDevOps AI Platform
// This script runs when the MongoDB container starts for the first time

print("Starting MongoDB initialization for SecureDevOps AI Platform...");

// Switch to the application database
db = db.getSiblingDB("securedevops");

// Create application user with appropriate permissions
db.createUser({
  user: "securedevops_app",
  pwd: "securedevops_app_password",
  roles: [
    {
      role: "readWrite",
      db: "securedevops",
    },
  ],
});

print("Created application user: securedevops_app");

// Create collections and indexes for optimal performance

// Reports Collection
print("Creating reports collection and indexes...");
db.createCollection("reports");

// Indexes for reports collection
db.reports.createIndex({ project_name: 1, created_at: -1 });
db.reports.createIndex({ status: 1 });
db.reports.createIndex({ branch: 1 });
db.reports.createIndex({ commit_hash: 1 });
db.reports.createIndex({ created_at: -1 });
db.reports.createIndex({ "findings_by_severity.critical": -1 });
db.reports.createIndex({ "findings_by_severity.high": -1 });
db.reports.createIndex({ has_ai_analysis: 1 });

// Compound indexes for common queries
db.reports.createIndex({ project_name: 1, status: 1, created_at: -1 });
db.reports.createIndex({ status: 1, created_at: -1 });

// Findings Collection
print("Creating findings collection and indexes...");
db.createCollection("findings");

// Indexes for findings collection
db.findings.createIndex({ report_id: 1 });
db.findings.createIndex({ severity: 1 });
db.findings.createIndex({ scanner_type: 1 });
db.findings.createIndex({ file_path: 1 });
db.findings.createIndex({ cwe_id: 1 });
db.findings.createIndex({ rule_id: 1 });

// Compound indexes for findings
db.findings.createIndex({ report_id: 1, severity: 1 });
db.findings.createIndex({ severity: 1, scanner_type: 1 });

// Scan Jobs Collection
print("Creating scan_jobs collection and indexes...");
db.createCollection("scan_jobs");

// Indexes for scan jobs
db.scan_jobs.createIndex({ status: 1 });
db.scan_jobs.createIndex({ created_at: -1 });
db.scan_jobs.createIndex({ project_name: 1, created_at: -1 });
db.scan_jobs.createIndex({ repository_url: 1 });

// AI Analysis Collection
print("Creating ai_analysis collection and indexes...");
db.createCollection("ai_analysis");

// Indexes for AI analysis
db.ai_analysis.createIndex({ report_id: 1 }, { unique: true });
db.ai_analysis.createIndex({ created_at: -1 });

// Webhooks Collection
print("Creating webhooks collection and indexes...");
db.createCollection("webhooks");

// Indexes for webhooks
db.webhooks.createIndex({ event_type: 1 });
db.webhooks.createIndex({ processed_at: -1 });
db.webhooks.createIndex({ status: 1 });

// Users Collection (for future authentication features)
print("Creating users collection and indexes...");
db.createCollection("users");

// Indexes for users
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ is_active: 1 });

// API Keys Collection (for API authentication)
print("Creating api_keys collection and indexes...");
db.createCollection("api_keys");

// Indexes for API keys
db.api_keys.createIndex({ key_hash: 1 }, { unique: true });
db.api_keys.createIndex({ user_id: 1 });
db.api_keys.createIndex({ is_active: 1 });
db.api_keys.createIndex({ expires_at: 1 });

// Audit Logs Collection
print("Creating audit_logs collection and indexes...");
db.createCollection("audit_logs");

// Indexes for audit logs
db.audit_logs.createIndex({ timestamp: -1 });
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 });
db.audit_logs.createIndex({ action: 1 });
db.audit_logs.createIndex({ resource_type: 1, resource_id: 1 });

// TTL index for audit logs (auto-delete after 1 year)
db.audit_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 31536000 });

// Create capped collection for real-time notifications
print("Creating notifications collection...");
db.createCollection("notifications", {
  capped: true,
  size: 10485760, // 10MB
  max: 10000,
});

// System Configuration Collection
print("Creating system_config collection...");
db.createCollection("system_config");

// Insert default system configuration
db.system_config.insertOne({
  _id: "default",
  version: "1.0.0",
  initialized_at: new Date(),
  scanner_config: {
    semgrep: {
      enabled: true,
      rules: ["auto"],
      timeout: 900,
    },
    trivy: {
      enabled: true,
      timeout: 600,
      db_update_interval: 86400,
    },
    gitleaks: {
      enabled: true,
      timeout: 300,
    },
    lynis: {
      enabled: true,
      timeout: 1200,
    },
  },
  ai_config: {
    enabled: true,
    model: "gpt-4",
    max_tokens: 2000,
    temperature: 0.1,
  },
  notification_config: {
    slack: {
      enabled: false,
    },
    teams: {
      enabled: false,
    },
    email: {
      enabled: false,
    },
  },
  compliance_standards: ["OWASP", "NIST", "ISO27001", "PCI_DSS"],
  report_retention_days: 90,
  scan_timeout: 1800,
});

print("Inserted default system configuration");

// Create some sample data for testing (only if needed)
if (typeof CREATE_SAMPLE_DATA !== "undefined" && CREATE_SAMPLE_DATA) {
  print("Creating sample data for testing...");

  // Sample project report
  var sampleReport = {
    _id: ObjectId(),
    project_name: "sample-project",
    repository_url: "https://github.com/sample/project",
    branch: "main",
    commit_hash: "abc123def456",
    status: "completed",
    created_at: new Date(),
    updated_at: new Date(),
    duration_seconds: 120,
    total_findings: 5,
    findings_by_severity: {
      critical: 1,
      high: 2,
      medium: 1,
      low: 1,
      info: 0,
    },
    scanners_used: ["semgrep", "trivy", "gitleaks"],
    has_ai_analysis: true,
  };

  db.reports.insertOne(sampleReport);

  // Sample findings
  var sampleFindings = [
    {
      _id: ObjectId(),
      report_id: sampleReport._id,
      title: "SQL Injection Vulnerability",
      description: "Potential SQL injection in user input handling",
      severity: "critical",
      scanner_type: "semgrep",
      file_path: "src/database.py",
      line_number: 42,
      cwe_id: "89",
      rule_id: "python.sql-injection",
      confidence: "high",
    },
    {
      _id: ObjectId(),
      report_id: sampleReport._id,
      title: "Cross-Site Scripting (XSS)",
      description: "Unescaped user input in template",
      severity: "high",
      scanner_type: "semgrep",
      file_path: "src/templates/user.html",
      line_number: 15,
      cwe_id: "79",
      rule_id: "javascript.xss",
      confidence: "medium",
    },
  ];

  db.findings.insertMany(sampleFindings);

  print("Created sample project report with findings");
}

// Create database views for analytics
print("Creating database views for analytics...");

// Vulnerability summary view
db.createView("vulnerability_summary", "findings", [
  {
    $group: {
      _id: "$severity",
      count: { $sum: 1 },
      unique_files: { $addToSet: "$file_path" },
      scanners: { $addToSet: "$scanner_type" },
    },
  },
  {
    $project: {
      severity: "$_id",
      count: 1,
      unique_files_count: { $size: "$unique_files" },
      scanners: 1,
      _id: 0,
    },
  },
]);

// Project health view
db.createView("project_health", "reports", [
  {
    $group: {
      _id: "$project_name",
      total_scans: { $sum: 1 },
      latest_scan: { $max: "$created_at" },
      avg_critical: { $avg: "$findings_by_severity.critical" },
      avg_high: { $avg: "$findings_by_severity.high" },
      success_rate: {
        $avg: {
          $cond: [{ $eq: ["$status", "completed"] }, 1, 0],
        },
      },
    },
  },
  {
    $project: {
      project_name: "$_id",
      total_scans: 1,
      latest_scan: 1,
      avg_critical: { $round: ["$avg_critical", 2] },
      avg_high: { $round: ["$avg_high", 2] },
      success_rate: { $round: [{ $multiply: ["$success_rate", 100] }, 1] },
      _id: 0,
    },
  },
]);

print("Created analytics views");

// Set up database validation rules
print("Setting up collection validation rules...");

// Reports validation
db.runCommand({
  collMod: "reports",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "project_name",
        "repository_url",
        "branch",
        "commit_hash",
        "status",
        "created_at",
      ],
      properties: {
        project_name: {
          bsonType: "string",
          minLength: 1,
          maxLength: 200,
        },
        repository_url: {
          bsonType: "string",
          pattern: "^https?://",
        },
        branch: {
          bsonType: "string",
          minLength: 1,
          maxLength: 100,
        },
        commit_hash: {
          bsonType: "string",
          minLength: 7,
          maxLength: 40,
        },
        status: {
          bsonType: "string",
          enum: ["pending", "running", "completed", "failed", "cancelled"],
        },
      },
    },
  },
  validationLevel: "moderate",
  validationAction: "warn",
});

// Findings validation
db.runCommand({
  collMod: "findings",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["report_id", "title", "severity", "scanner_type"],
      properties: {
        severity: {
          bsonType: "string",
          enum: ["critical", "high", "medium", "low", "info"],
        },
        scanner_type: {
          bsonType: "string",
          enum: ["semgrep", "trivy", "gitleaks", "lynis", "custom"],
        },
        confidence: {
          bsonType: "string",
          enum: ["high", "medium", "low"],
        },
      },
    },
  },
  validationLevel: "moderate",
  validationAction: "warn",
});

print("Set up collection validation rules");

// Database statistics
print("Database initialization completed!");
print("Collections created:");
print("- reports: " + db.reports.countDocuments());
print("- findings: " + db.findings.countDocuments());
print("- scan_jobs: " + db.scan_jobs.countDocuments());
print("- ai_analysis: " + db.ai_analysis.countDocuments());
print("- webhooks: " + db.webhooks.countDocuments());
print("- users: " + db.users.countDocuments());
print("- api_keys: " + db.api_keys.countDocuments());
print("- audit_logs: " + db.audit_logs.countDocuments());
print("- notifications: " + db.notifications.countDocuments());
print("- system_config: " + db.system_config.countDocuments());

print("Indexes created:");
db.getCollectionNames().forEach(function (collection) {
  var indexes = db[collection].getIndexes();
  print("- " + collection + ": " + indexes.length + " indexes");
});

print(
  "SecureDevOps AI Platform database initialization completed successfully!"
);
print("Ready for application startup.");
