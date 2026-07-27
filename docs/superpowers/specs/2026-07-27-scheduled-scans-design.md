# Scheduled Scans — Design Spec

## Overview
Cron-based automatic security scanning for ONYX. Users can create schedules that trigger scans at periodic intervals using cron expressions. Supports per-project and global (admin) schedules.

## Architecture

### ScanSchedule Model (Beanie Document)
Stored in MongoDB `scan_schedules` collection. Fields:
- `name`, `description` — human identifiers
- `project_id` (Optional) — null = global/admin schedule
- `target` — repository URL or target identifier
- `scan_types` — list of ScanType enums
- `cron_expression` — standard 5-field cron
- `timezone` — IANA timezone (default UTC)
- `enabled` — toggle without deleting
- `created_by` — user_id of creator
- `created_at`, `updated_at`, `last_run`, `last_status`, `next_run`
- `config` — extra scan options dict
- `misfire_grace_time`, `coalesce`, `max_instances` — APScheduler settings

### ScanSchedulerService
Registered in ServiceRegistry. Wraps APScheduler `AsyncIOScheduler` with `MongoDBJobStore`.

Lifecycle:
- `initialize()` — creates scheduler (no start)
- `start()` — loads enabled schedules from DB, adds cron jobs, starts scheduler
- `stop()` — shuts down scheduler gracefully
- CRUD methods: `create_schedule`, `update_schedule`, `delete_schedule`, `toggle_schedule`, `run_now` — each syncs APScheduler jobs with DB state

Job execution:
- Scheduled job calls `ScanOrchestrator.run_scan()` via `ServiceRegistry`
- Updates `last_run`, `last_status`, `next_run` on the ScanSchedule document
- Sends WebSocket notifications on start/complete/fail
- Error handling: wraps job in try/except, logs failures, marks schedule with failed status

### API Endpoints (`/api/schedules`)
- `GET /api/schedules` — list (filterable by project_id)
- `POST /api/schedules` — create
- `GET /api/schedules/{id}` — get
- `PUT /api/schedules/{id}` — update
- `DELETE /api/schedules/{id}` — delete
- `POST /api/schedules/{id}/run` — trigger immediately
- `PATCH /api/schedules/{id}/toggle` — enable/disable
- `GET /api/schedules/{id}/history` — run history (from scan reports)

### Frontend
- **ScheduledScansPage** — main page with schedule list, filter by project, create/edit modals
- **ScheduleCard** — card showing schedule info, status indicator, next run time
- **ScheduleForm** — create/edit form with cron builder (presets + custom), timezone picker, scan type selector
- **ScheduleHistory** — table of past runs for a schedule
- Nav item "Scheduled Scans" in sidebar with ClockIcon
- Route at `/scheduled-scans`

### Persistence
APScheduler uses MongoDBJobStore sharing the existing motor client. This ensures schedules survive app restarts.
