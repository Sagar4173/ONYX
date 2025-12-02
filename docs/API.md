# 📚 API Documentation

## Overview

ONYX - Security Intelligence Platform provides a comprehensive REST API for managing security scans, accessing reports, and integrating with external systems. The API is built with FastAPI and provides automatic OpenAPI documentation.

**Base URLs**:

- **Production**: `https://onyx-backend-dt4o.onrender.com`
- **Development**: `http://localhost:8000`

**API Documentation**:

- **Live Demo**: [https://onyx-backend-dt4o.onrender.com/docs](https://onyx-backend-dt4o.onrender.com/docs)
- **Local Development**: Visit `/docs` for interactive Swagger UI documentation

---

## 🔐 Authentication

### JWT Token Authentication

All API endpoints (except health checks and webhook endpoints) require JWT authentication.

#### **Obtain Access Token**

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### **Using the Token**

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### **Refresh Token**

```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

---

## 🔍 Scan Management API

### Submit Manual Scan

Start a security scan for a repository.

```http
POST /webhook/scan
Content-Type: application/json
Authorization: Bearer <token>

{
  "repository_url": "https://github.com/user/repo.git",
  "branch": "main",
  "scan_types": ["sast", "secrets", "container", "infrastructure"]
}
```

**Parameters:**

- `repository_url` (string, required): Git repository URL
- `branch` (string, optional): Branch to scan (default: "main")
- `scan_types` (array, optional): Types of scans to run

**Response:**

```json
{
  "message": "Scan submitted successfully",
  "scan_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "project_name": "repo",
  "repository_url": "https://github.com/user/repo.git",
  "branch": "main",
  "scan_types": ["sast", "secrets", "container", "infrastructure"]
}
```

**Status Codes:**

- `202`: Scan submitted successfully
- `400`: Invalid request parameters
- `401`: Authentication required
- `500`: Internal server error

### Get Scan Status

Check the status of a running scan.

```http
GET /api/scans/{scan_id}/status
Authorization: Bearer <token>
```

**Response:**

```json
{
  "scan_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 65,
  "current_step": "Running SAST analysis",
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

**Scan Statuses:**

- `pending`: Scan queued for processing
- `running`: Scan in progress
- `completed`: Scan finished successfully
- `failed`: Scan failed with errors
- `cancelled`: Scan was cancelled

---

## � User Management API

### Get Current User Profile

Get the profile information for the currently authenticated user.

```http
GET /api/users/me
Authorization: Bearer <token>
```

**Response:**

```json
{
  "id": "user_123",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "developer",
  "status": "active",
  "organization": "Acme Corp",
  "timezone": "UTC",
  "is_email_verified": true,
  "last_login": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "notification_preferences": {
    "email_notifications": true,
    "security_alerts": true,
    "scan_completion": true,
    "weekly_reports": true
  }
}
```

### Update Current User Profile

Update the profile information for the currently authenticated user.

```http
PUT /api/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Smith",
  "organization": "New Company",
  "timezone": "America/New_York",
  "notification_preferences": {
    "email_notifications": false,
    "security_alerts": true,
    "scan_completion": true,
    "weekly_reports": false
  }
}
```

### Change Password

Change the password for the currently authenticated user.

```http
POST /api/users/me/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "NewSecurePassword!123"
}
```

### List All Users (Admin Only)

Retrieve a list of all users with filtering and pagination. Requires Admin role.

```http
GET /api/users?role=developer&status=active&search=john&page=1&limit=20
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "users": [
    {
      "id": "user_123",
      "email": "user@example.com",
      "username": "johndoe",
      "full_name": "John Doe",
      "role": "developer",
      "status": "active",
      "organization": "Acme Corp",
      "last_login": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### Update User Role (Admin Only)

Update a user's role. Requires Admin role.

```http
PUT /api/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

"security_manager"
```

### Update User Status (Admin Only)

Update a user's status. Requires Admin role.

```http
PUT /api/users/{user_id}/status
Authorization: Bearer <admin_token>
Content-Type: application/json

"suspended"
```

### Get User Sessions

Get active sessions for the current user or a specific user (Admin only).

```http
GET /api/users/me/sessions
Authorization: Bearer <token>
```

**Response:**

```json
{
  "sessions": [
    {
      "session_id": "session_123",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "device_info": {
        "browser": "Chrome",
        "os": "Windows 10"
      },
      "created_at": "2025-01-15T10:00:00Z",
      "last_activity": "2025-01-15T10:30:00Z",
      "expires_at": "2025-01-15T18:00:00Z"
    }
  ]
}
```

### Revoke Session

Revoke a specific session for the current user.

```http
DELETE /api/users/me/sessions/{session_id}
Authorization: Bearer <token>
```

### Get API Tokens

Get API tokens for the current user.

```http
GET /api/users/me/api-tokens
Authorization: Bearer <token>
```

### Create API Token

Create a new API token for the current user.

```http
POST /api/users/me/api-tokens
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "CI/CD Integration",
  "scopes": ["read:reports", "write:scans"],
  "expires_in_days": 90,
  "allowed_ips": ["192.168.1.0/24"]
}
```

**Response:**

```json
{
  "token_id": "token_123",
  "name": "CI/CD Integration",
  "token": "sdt_1234567890abcdef...",
  "prefix": "sdt_1234",
  "scopes": ["read:reports", "write:scans"],
  "expires_at": "2025-04-15T00:00:00Z",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Get User Statistics (Admin Only)

Get user statistics for the admin dashboard.

```http
GET /api/users/statistics
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "total_users": 150,
  "active_users": 142,
  "pending_users": 5,
  "suspended_users": 3,
  "role_distribution": {
    "admin": 2,
    "security_manager": 8,
    "developer": 95,
    "viewer": 45
  },
  "recent_registrations": 12,
  "active_sessions": 89
}
```

---

## 🛡️ Admin Dashboard API

Admin-only endpoints for comprehensive system management and oversight.

### Get System Statistics

Get comprehensive system-wide statistics for the admin dashboard.

```http
GET /api/admin/dashboard/stats
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "users": {
    "total": 150,
    "by_role": {
      "admin": 2,
      "security_manager": 8,
      "developer": 95,
      "viewer": 45
    },
    "by_status": {
      "active": 142,
      "pending": 5,
      "suspended": 3
    },
    "recent_registrations": 12
  },
  "projects": {
    "total": 85,
    "by_status": {
      "active": 70,
      "archived": 10,
      "pending": 5
    }
  },
  "scans": {
    "total": 1250,
    "by_status": {
      "completed": 1180,
      "running": 15,
      "failed": 55
    },
    "total_findings": 8450,
    "critical_findings": 125
  }
}
```

### Get All Users (Admin View)

Retrieve all users with advanced filtering for admin management.

```http
GET /api/admin/users/all?search=john&role=developer&status=active&skip=0&limit=50
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "users": [
    {
      "id": "user_123",
      "username": "john_doe",
      "email": "john@example.com",
      "role": "developer",
      "status": "active",
      "organization": "Acme Corp",
      "created_at": "2025-01-01T00:00:00Z",
      "last_login": "2025-01-15T10:00:00Z",
      "project_count": 5,
      "scan_count": 45
    }
  ],
  "pagination": {
    "total": 150,
    "skip": 0,
    "limit": 50,
    "has_more": true
  }
}
```

### Get All Projects (Admin View)

Retrieve all projects across all users for admin oversight.

```http
GET /api/admin/projects/all?search=webapp&skip=0&limit=50
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "projects": [
    {
      "id": "project_123",
      "name": "Web Application",
      "description": "Main web app",
      "status": "active",
      "repository_url": "https://github.com/user/repo",
      "owner": {
        "id": "user_123",
        "username": "john_doe",
        "email": "john@example.com"
      },
      "total_scans": 25,
      "total_findings": 150,
      "critical_findings": 5,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 85,
    "skip": 0,
    "limit": 50,
    "has_more": true
  }
}
```

### Get Recent Activity

Get recent system-wide activity for monitoring.

```http
GET /api/admin/activity/recent?limit=50
Authorization: Bearer <admin_token>
```

**Response:**

```json
{
  "activities": [
    {
      "type": "user_registration",
      "icon": "user",
      "title": "New user registered: jane_doe",
      "description": "jane@example.com (developer)",
      "timestamp": "2025-01-15T10:30:00Z",
      "entity_id": "user_456",
      "entity_type": "user"
    },
    {
      "type": "scan_completed",
      "icon": "check",
      "title": "Scan completed: My Project",
      "description": "45 findings",
      "timestamp": "2025-01-15T10:00:00Z",
      "entity_id": "scan_789",
      "entity_type": "scan"
    }
  ],
  "total": 150
}
```

### Get User Activity

Get activity history for a specific user.

```http
GET /api/admin/users/{user_id}/activity?limit=50
Authorization: Bearer <admin_token>
```

### Update User Role (Admin)

```http
PUT /api/admin/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "security_manager"
}
```

### Update User Status (Admin)

```http
PUT /api/admin/users/{user_id}/status
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "status": "suspended"
}
```

### Delete User (Admin)

```http
DELETE /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

### Delete Project (Admin)

```http
DELETE /api/admin/projects/{project_id}
Authorization: Bearer <admin_token>
```

---

## 📊 Projects API

### Get All Projects

Retrieve a list of projects accessible to the current user.

```http
GET /api/projects?category=web&status=active&page=1&limit=20
Authorization: Bearer <token>
```

**Response:**

```json
{
  "projects": [
    {
      "id": "project_123",
      "name": "My Web App",
      "description": "A secure web application",
      "category": "web",
      "repository_url": "https://github.com/user/repo",
      "repository_branch": "main",
      "scan_tools": ["semgrep", "trivy"],
      "created_at": "2025-01-01T00:00:00Z",
      "last_scan": "2025-01-15T10:00:00Z",
      "team_members": [
        {
          "user_id": "user_123",
          "role": "owner",
          "permissions": ["read", "write", "admin"]
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "total_pages": 1
}
```

### Create Project

Create a new project.

```http
POST /api/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Security Project",
  "description": "Project for security testing",
  "category": "web",
  "repository_url": "https://github.com/user/new-repo",
  "repository_branch": "main",
  "scan_tools": ["semgrep", "trivy", "gitleaks"],
  "team_members": [
    {
      "user_id": "user_456",
      "role": "developer"
    }
  ]
}
```

### Update Project

Update an existing project.

```http
PUT /api/projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description",
  "scan_tools": ["semgrep", "trivy", "gitleaks", "bandit"]
}
```

### Add Team Member

Add a team member to a project.

```http
POST /api/projects/{project_id}/team
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user_789",
  "role": "developer"
}
```

### Get Project Statistics

Get statistics for a specific project.

```http
GET /api/projects/{project_id}/statistics
Authorization: Bearer <token>
```

**Response:**

```json
{
  "total_scans": 25,
  "last_scan_date": "2025-01-15T10:00:00Z",
  "vulnerabilities": {
    "critical": 2,
    "high": 8,
    "medium": 15,
    "low": 30
  },
  "scan_tools_used": ["semgrep", "trivy", "gitleaks"],
  "team_size": 4,
  "project_health": "good"
}
```

---

## �📊 Reports API

### Get All Scan Reports

Retrieve a list of all scan reports with filtering and pagination.

```http
GET /api/reports?project_name=myproject&status=completed&page=1&size=20
Authorization: Bearer <token>
```

**Query Parameters:**

- `project_name` (string, optional): Filter by project name
- `status` (string, optional): Filter by scan status
- `severity` (string, optional): Filter by minimum severity level
- `page` (integer, optional): Page number (default: 1)
- `size` (integer, optional): Items per page (default: 20)
- `sort_by` (string, optional): Sort field (default: "created_at")
- `sort_order` (string, optional): Sort order ("asc" or "desc", default: "desc")

**Response:**

```json
{
  "reports": [
    {
      "scan_id": "123e4567-e89b-12d3-a456-426614174000",
      "project_name": "my-project",
      "status": "completed",
      "total_findings": 15,
      "findings_by_severity": {
        "critical": 2,
        "high": 5,
        "medium": 6,
        "low": 2,
        "info": 0
      },
      "created_at": "2024-01-15T09:00:00Z",
      "completed_at": "2024-01-15T09:15:00Z",
      "duration_seconds": 900,
      "git_metadata": {
        "repository_url": "https://github.com/user/repo.git",
        "branch": "main",
        "commit_hash": "abc123def456",
        "commit_message": "Fix security vulnerability",
        "commit_author": "developer@example.com"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 45,
    "pages": 3
  }
}
```

### Get Specific Scan Report

Retrieve detailed information about a specific scan.

```http
GET /api/reports/{scan_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "scan_id": "123e4567-e89b-12d3-a456-426614174000",
  "project_name": "my-project",
  "status": "completed",
  "created_at": "2024-01-15T09:00:00Z",
  "completed_at": "2024-01-15T09:15:00Z",
  "duration_seconds": 900,
  "total_findings": 15,
  "findings_by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 6,
    "low": 2,
    "info": 0
  },
  "git_metadata": {
    "repository_url": "https://github.com/user/repo.git",
    "branch": "main",
    "commit_hash": "abc123def456",
    "commit_message": "Fix security vulnerability",
    "commit_author": "developer@example.com",
    "commit_timestamp": "2024-01-15T08:45:00Z"
  },
  "scan_results": [
    {
      "scanner": "semgrep",
      "status": "completed",
      "findings": [
        {
          "rule_id": "javascript.lang.security.audit.xss.react-dangerouslysetinnerhtml",
          "title": "Dangerous use of dangerouslySetInnerHTML",
          "description": "User input used in dangerouslySetInnerHTML can lead to XSS",
          "severity": "high",
          "file_path": "src/components/UserProfile.jsx",
          "line_number": 42,
          "column_number": 12,
          "cwe_id": "CWE-79",
          "owasp_category": "A03:2021 – Injection",
          "confidence": "high",
          "code_snippet": "<div dangerouslySetInnerHTML={{__html: userInput}} />"
        }
      ]
    }
  ],
  "ai_analysis": {
    "model_used": "gpt-4",
    "generated_at": "2025-11-30T09:16:00Z",
    "executive_summary": "The scan identified 15 security vulnerabilities...",
    "risk_assessment": "HIGH - Multiple critical vulnerabilities found...",
    "risk_score": 72,
    "security_score": 58,
    "threat_categories": [
      "Injection Attacks",
      "Authentication Issues",
      "Data Exposure",
      "Security Misconfiguration"
    ],
    "attack_vectors": [
      "SQL injection through user input fields",
      "XSS via unsanitized profile data",
      "Credential theft through exposed API keys"
    ],
    "priority_findings": [
      "SQL injection vulnerability in user authentication",
      "Cross-site scripting (XSS) in user profile component",
      "Exposed API keys in configuration files"
    ],
    "recommendations": [
      "Implement parameterized queries for database operations",
      "Sanitize user input before rendering in React components",
      "Move sensitive configuration to environment variables"
    ],
    "remediation_roadmap": [
      {
        "priority": "immediate",
        "action": "Fix SQL injection vulnerabilities",
        "effort": "4-8 hours",
        "impact": "Prevents database compromise"
      },
      {
        "priority": "short_term",
        "action": "Implement input sanitization",
        "effort": "1-2 days",
        "impact": "Eliminates XSS attack surface"
      },
      {
        "priority": "medium_term",
        "action": "Rotate exposed credentials",
        "effort": "2-4 hours",
        "impact": "Secures API access"
      }
    ],
    "secure_code_examples": {
      "sql-injection": "// Vulnerable code\nconst query = `SELECT * FROM users WHERE id = ${userId}`;\n\n// Secure code\nconst query = 'SELECT * FROM users WHERE id = ?';\ndb.query(query, [userId]);"
    },
    "compliance_impact": {
      "OWASP": "A03:2021 Injection - High impact",
      "NIST": "PR.DS-1, DE.CM-4 - Data security controls affected",
      "ISO27001": "A.14.2.5 - Secure development principles violated",
      "PCI_DSS": "Requirement 6.5 - Application security issues"
    },
    "estimated_fix_time": "2.5 days (20 hours)"
  }
}
```

### Export Scan Report

Export scan report in various formats.

```http
GET /api/reports/{scan_id}/export?format=pdf
Authorization: Bearer <token>
```

**Query Parameters:**

- `format` (string, required): Export format ("pdf", "json", "csv")
- `include_ai_analysis` (boolean, optional): Include AI analysis (default: true)
- `include_code_snippets` (boolean, optional): Include vulnerable code snippets (default: false)

**Response:**

- PDF: Binary PDF file
- JSON: Structured JSON data
- CSV: Comma-separated values

### Delete Scan Report

Delete a scan report (requires appropriate permissions).

```http
DELETE /api/reports/{scan_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "message": "Scan report deleted successfully",
  "scan_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

## 🔔 Webhooks API

### Receive Git Webhooks

Endpoint for receiving webhooks from Git providers.

```http
POST /webhook/
Content-Type: application/json
X-GitHub-Event: push
X-Hub-Signature-256: sha256=...

{
  "ref": "refs/heads/main",
  "repository": {
    "name": "my-repo",
    "full_name": "user/my-repo",
    "clone_url": "https://github.com/user/my-repo.git"
  },
  "head_commit": {
    "id": "abc123def456",
    "message": "Fix security issue",
    "author": {
      "name": "Developer",
      "email": "dev@example.com"
    },
    "timestamp": "2024-01-15T08:45:00Z"
  }
}
```

**Supported Git Providers:**

- GitHub (push, pull_request events)
- GitLab (push, merge_request events)
- Bitbucket (push events)
- Azure DevOps (push events)

**Response:**

```json
{
  "status": "accepted",
  "event_id": "webhook-456def789ghi",
  "message": "Webhook received and processing started",
  "scan_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Get Webhook Events

Retrieve webhook event history.

```http
GET /api/webhook/events?provider=github&status=processed
Authorization: Bearer <token>
```

**Query Parameters:**

- `provider` (string, optional): Filter by Git provider
- `status` (string, optional): Filter by processing status
- `repository` (string, optional): Filter by repository name
- `event_type` (string, optional): Filter by event type

**Response:**

```json
{
  "events": [
    {
      "event_id": "webhook-456def789ghi",
      "provider": "github",
      "event_type": "push",
      "repository": "user/my-repo",
      "status": "processed",
      "received_at": "2024-01-15T08:45:00Z",
      "processed_at": "2024-01-15T08:45:30Z",
      "scan_id": "123e4567-e89b-12d3-a456-426614174000"
    }
  ]
}
```

---

## 📈 Analytics API

### Get Security Metrics

Retrieve security metrics and trends.

```http
GET /api/analytics/metrics?timeframe=30d&project=my-project
Authorization: Bearer <token>
```

**Query Parameters:**

- `timeframe` (string, optional): Time period ("7d", "30d", "90d", "1y")
- `project` (string, optional): Filter by project name
- `metric_type` (string, optional): Specific metric type

**Response:**

```json
{
  "timeframe": "30d",
  "total_scans": 145,
  "total_findings": 1250,
  "findings_by_severity": {
    "critical": 45,
    "high": 180,
    "medium": 520,
    "low": 505,
    "info": 0
  },
  "trend_data": [
    {
      "date": "2024-01-01",
      "scans": 5,
      "findings": 42
    },
    {
      "date": "2024-01-02",
      "scans": 3,
      "findings": 28
    }
  ],
  "top_vulnerabilities": [
    {
      "type": "SQL Injection",
      "count": 25,
      "trend": "decreasing"
    },
    {
      "type": "Cross-Site Scripting",
      "count": 18,
      "trend": "stable"
    }
  ]
}
```

### Get Security Trends

Analyze security trends over time.

```http
GET /api/analytics/trends?metric=vulnerability_count&period=daily
Authorization: Bearer <token>
```

**Response:**

```json
{
  "metric": "vulnerability_count",
  "period": "daily",
  "data_points": [
    {
      "timestamp": "2024-01-15T00:00:00Z",
      "value": 42,
      "change_percentage": -12.5
    }
  ],
  "summary": {
    "average": 38.5,
    "trend": "improving",
    "change_from_previous_period": -15.2
  }
}
```

---

## ⚙️ Configuration API

### Get System Configuration

Retrieve current system configuration.

```http
GET /api/config
Authorization: Bearer <token>
```

**Response:**

```json
{
  "scanners": {
    "semgrep": {
      "enabled": true,
      "version": "1.45.0",
      "rules": "auto"
    },
    "trivy": {
      "enabled": true,
      "version": "0.48.0",
      "database_updated": "2024-01-15T06:00:00Z"
    }
  },
  "ai_analysis": {
    "enabled": true,
    "model": "gpt-4",
    "max_tokens": 2000
  },
  "notifications": {
    "slack": {
      "enabled": true,
      "webhook_configured": true
    },
    "email": {
      "enabled": false,
      "smtp_configured": false
    }
  }
}
```

### Update Configuration

Update system configuration (admin required).

```http
PUT /api/config
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "ai_analysis": {
    "model": "gpt-4",
    "max_tokens": 4000
  },
  "notifications": {
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/..."
    }
  }
}
```

---

## 🏥 Health & Status API

### System Health Check

Check the health of all system components.

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T09:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "semgrep": "healthy",
    "trivy": "healthy",
    "gitleaks": "healthy",
    "lynis": "healthy",
    "ai_processor": "healthy",
    "notification_service": "healthy"
  },
  "metrics": {
    "active_scans": 3,
    "queued_scans": 7,
    "database_connections": 15,
    "memory_usage_mb": 512,
    "cpu_usage_percent": 25.5
  }
}
```

### Scanner Health

Check the status of individual security scanners.

```http
GET /health/scanners
Authorization: Bearer <token>
```

**Response:**

```json
{
  "scanners": {
    "semgrep": {
      "status": "healthy",
      "version": "1.45.0",
      "last_check": "2024-01-15T09:25:00Z",
      "rules_updated": "2024-01-15T06:00:00Z"
    },
    "trivy": {
      "status": "healthy",
      "version": "0.48.0",
      "last_check": "2024-01-15T09:25:00Z",
      "database_version": "2024-01-15"
    }
  }
}
```

---

## 🔧 Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "repository_url",
      "issue": "Invalid URL format"
    },
    "timestamp": "2024-01-15T09:30:00Z",
    "request_id": "req-123abc456def"
  }
}
```

### Common Error Codes

| HTTP Status | Error Code                 | Description                                     |
| ----------- | -------------------------- | ----------------------------------------------- |
| 400         | `VALIDATION_ERROR`         | Invalid request parameters                      |
| 401         | `AUTHENTICATION_REQUIRED`  | Valid authentication token required             |
| 403         | `INSUFFICIENT_PERMISSIONS` | User lacks required permissions                 |
| 404         | `RESOURCE_NOT_FOUND`       | Requested resource does not exist               |
| 409         | `RESOURCE_CONFLICT`        | Resource already exists or conflict             |
| 422         | `UNPROCESSABLE_ENTITY`     | Request format valid but semantically incorrect |
| 429         | `RATE_LIMIT_EXCEEDED`      | Too many requests in time window                |
| 500         | `INTERNAL_SERVER_ERROR`    | Unexpected server error                         |
| 502         | `SCANNER_UNAVAILABLE`      | Security scanner service unavailable            |
| 503         | `SERVICE_UNAVAILABLE`      | Service temporarily unavailable                 |

---

## 📚 SDK Examples

### Python SDK

```python
import requests
from typing import Dict, List, Optional

class ONYXClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

    def submit_scan(
        self,
        repository_url: str,
        branch: str = 'main',
        scan_types: Optional[List[str]] = None
    ) -> Dict:
        """Submit a new security scan"""
        payload = {
            'repository_url': repository_url,
            'branch': branch,
            'scan_types': scan_types or ['sast', 'secrets', 'container']
        }

        response = requests.post(
            f'{self.base_url}/webhook/scan',
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_scan_report(self, scan_id: str) -> Dict:
        """Get detailed scan report"""
        response = requests.get(
            f'{self.base_url}/api/reports/{scan_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def wait_for_scan_completion(self, scan_id: str, timeout: int = 600) -> Dict:
        """Wait for scan to complete"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            report = self.get_scan_report(scan_id)
            if report['status'] in ['completed', 'failed']:
                return report
            time.sleep(10)

        raise TimeoutError(f'Scan {scan_id} did not complete within {timeout} seconds')

# Usage example
client = ONYXClient('http://localhost:8000', 'your-api-token')

# Submit scan
scan_result = client.submit_scan('https://github.com/user/repo.git')
scan_id = scan_result['scan_id']

# Wait for completion and get results
report = client.wait_for_scan_completion(scan_id)
print(f"Scan completed with {report['total_findings']} findings")
```

### JavaScript/Node.js SDK

```javascript
class ONYXClient {
  constructor(baseUrl, apiToken) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.headers = {
      Authorization: `Bearer ${apiToken}`,
      "Content-Type": "application/json",
    };
  }

  async submitScan(
    repositoryUrl,
    branch = "main",
    scanTypes = ["sast", "secrets", "container"]
  ) {
    const response = await fetch(`${this.baseUrl}/webhook/scan`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({
        repository_url: repositoryUrl,
        branch: branch,
        scan_types: scanTypes,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async getScanReport(scanId) {
    const response = await fetch(`${this.baseUrl}/api/reports/${scanId}`, {
      headers: this.headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  async waitForScanCompletion(scanId, timeoutMs = 600000) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeoutMs) {
      const report = await this.getScanReport(scanId);

      if (["completed", "failed"].includes(report.status)) {
        return report;
      }

      await new Promise((resolve) => setTimeout(resolve, 10000));
    }

    throw new Error(`Scan ${scanId} did not complete within ${timeoutMs}ms`);
  }
}

// Usage example
const client = new ONYXClient("http://localhost:8000", "your-api-token");

async function runScan() {
  try {
    // Submit scan
    const scanResult = await client.submitScan(
      "https://github.com/user/repo.git"
    );
    console.log(`Scan submitted: ${scanResult.scan_id}`);

    // Wait for completion
    const report = await client.waitForScanCompletion(scanResult.scan_id);
    console.log(`Scan completed with ${report.total_findings} findings`);

    return report;
  } catch (error) {
    console.error("Scan failed:", error);
    throw error;
  }
}
```

---

## 🔄 Rate Limiting

API endpoints are rate limited to ensure fair usage and system stability.

### Rate Limits

| Endpoint Category   | Limit         | Window   |
| ------------------- | ------------- | -------- |
| **Authentication**  | 10 requests   | 1 minute |
| **Scan Submission** | 5 requests    | 1 minute |
| **Report Access**   | 100 requests  | 1 minute |
| **Analytics**       | 50 requests   | 1 minute |
| **Webhooks**        | 1000 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642246800
X-RateLimit-Window: 60
```

### Rate Limit Error

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "retry_after": 30,
    "timestamp": "2024-01-15T09:30:00Z"
  }
}
```

---

## 🔒 Security Considerations

### API Security Best Practices

1. **Always use HTTPS** in production
2. **Store API tokens securely** (environment variables, key vaults)
3. **Rotate tokens regularly** (every 90 days recommended)
4. **Use least privilege access** (minimal required permissions)
5. **Monitor API usage** for unusual patterns
6. **Validate all inputs** on client side before sending
7. **Handle errors gracefully** without exposing sensitive information

### Token Security

```python
# Good: Secure token storage
import os
api_token = os.getenv('ONYX_API_TOKEN')

# Bad: Hardcoded token
# api_token = 'sk-abc123...'  # Never do this!
```

---

For more detailed API documentation and interactive testing, visit the **Swagger UI** at `/docs` when running the platform locally.

---

## 🏢 Enterprise Security API

### OSV/NVD Vulnerability Integration

#### Get CVE Details

Retrieve detailed vulnerability information from NIST NVD.

```http
GET /api/enterprise/vulnerabilities/cve/{cve_id}
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "cve_id": "CVE-2024-1234",
    "description": "SQL Injection vulnerability in...",
    "cvss_v3": {
      "score": 9.8,
      "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "severity": "critical"
    },
    "cvss_v2": {
      "score": 10.0,
      "severity": "high"
    },
    "epss": {
      "score": 0.85,
      "percentile": 97.2
    },
    "references": [...],
    "affected_products": [...]
  }
}
```

#### Check Package Vulnerabilities

Check multiple packages for known vulnerabilities using Google OSV.

```http
POST /api/enterprise/vulnerabilities/packages
Content-Type: application/json
Authorization: Bearer <token>

{
  "packages": [
    {"name": "django", "version": "3.2.0", "ecosystem": "pypi"},
    {"name": "lodash", "version": "4.17.20", "ecosystem": "npm"}
  ]
}
```

**Response:**

```json
{
  "success": true,
  "total_packages": 2,
  "vulnerable_packages": 1,
  "results": [
    {
      "package": "django",
      "version": "3.2.0",
      "ecosystem": "pypi",
      "vulnerabilities": [...],
      "vulnerable": true
    }
  ]
}
```

### SBOM Generation

#### Generate SBOM

Generate Software Bill of Materials in SPDX or CycloneDX format.

```http
POST /api/enterprise/sbom/generate
Content-Type: application/json
Authorization: Bearer <token>

{
  "repository_path": "/path/to/repository",
  "format": "spdx",
  "include_dev_deps": false,
  "enrich_vulnerabilities": true
}
```

**Response:**

```json
{
  "success": true,
  "format": "spdx",
  "sbom": {
    "spdxVersion": "SPDX-2.3",
    "name": "my-project-sbom",
    "packages": [...],
    "relationships": [...]
  }
}
```

#### Get Supported Formats

```http
GET /api/enterprise/sbom/formats
```

**Response:**

```json
{
  "formats": [
    {
      "id": "spdx",
      "name": "SPDX 2.3",
      "description": "Software Package Data Exchange - Linux Foundation standard",
      "output_types": ["json", "xml"],
      "compliance": ["NTIA", "Executive Order 14028"]
    },
    {
      "id": "cyclonedx",
      "name": "CycloneDX 1.5",
      "description": "OWASP lightweight SBOM standard",
      "output_types": ["json", "xml"],
      "compliance": ["OWASP", "FDA", "NTIA"]
    }
  ],
  "supported_languages": [
    "Python",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
    "Java",
    "Ruby",
    ".NET/C#"
  ]
}
```

### Security Trends

#### Get Dashboard Data

Retrieve complete security trends dashboard data in a single call.

```http
GET /api/enterprise/trends/dashboard?project_id=<optional>
Authorization: Bearer <token>
```

**Response:**

```json
{
  "success": true,
  "data": {
    "current": {
      "security_score": 78.5,
      "risk_score": 32.1,
      "severity_counts": {"critical": 2, "high": 8, "medium": 15, "low": 25, "total": 50},
      "open_findings": 50,
      "fixed_7d": 12,
      "fixed_30d": 45,
      "mttr_hours": 72.5,
      "compliance_rate": 0.85
    },
    "trends": {
      "direction": "improving",
      "improvement_pct": 15.3,
      "projected_score_30d": 82.1,
      "time_to_target": 45,
      "fix_rate": 1.2
    },
    "charts": {
      "weekly": [...],
      "daily": [...],
      "by_scanner": {...}
    },
    "comparison": {...},
    "notable_changes": [...]
  }
}
```

#### Get Severity Trends

```http
GET /api/enterprise/trends/severity?period=weekly&limit=12
Authorization: Bearer <token>
```

#### Get Current Metrics

```http
GET /api/enterprise/trends/metrics
Authorization: Bearer <token>
```

### Scan Comparison

#### Compare Two Scans

```http
POST /api/enterprise/scans/compare
Content-Type: application/json
Authorization: Bearer <token>

{
  "base_scan_id": "scan-001",
  "compare_scan_id": "scan-002",
  "include_unchanged": false
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "summary": {
      "fixed": 15,
      "new": 3,
      "reintroduced": 1,
      "modified": 2,
      "net_change": -11,
      "improvement_score": 45.2
    },
    "details": {
      "fixed": [...],
      "new": [...],
      "reintroduced": [...],
      "modified": [...]
    },
    "analysis": {
      "summary": "15 vulnerabilities fixed. 3 new vulnerabilities introduced...",
      "highlights": ["🎉 5 critical vulnerabilities fixed!"],
      "recommendations": ["Prioritize fixing 2 critical/high severity issues"]
    }
  }
}
```

#### Compare Branches

```http
GET /api/enterprise/scans/{project_id}/branches/compare?base_branch=main&compare_branch=feature
Authorization: Bearer <token>
```

#### Get Remediation Progress

```http
GET /api/enterprise/scans/{project_id}/remediation-progress?days=30
Authorization: Bearer <token>
```

#### Get Fix Velocity

```http
GET /api/enterprise/scans/{project_id}/fix-velocity?severity=high
Authorization: Bearer <token>
```

---

## 📞 Support

- **API Issues**: [GitHub Issues](https://github.com/Sagar4173/ONYXAI-Platform/issues)
- **Integration Help**: [GitHub Discussions](https://github.com/Sagar4173/ONYXAI-Platform/discussions)
- **Enterprise Support**: enterprise@ONYX.ai
