# Scheduled Scans — Implementation Plan

## Objective
Add cron-based automatic security scanning to ONYX with APScheduler, full REST API, and frontend management UI.

## Files Created

### Backend
- `backend/models/schedule.py` — ScanSchedule Beanie Document + ScheduleCreate/ScheduleUpdate/ScheduleResponse Pydantic models
- `backend/services/scheduling/__init__.py` — package init
- `backend/services/scheduling/scheduler_service.py` — ScanSchedulerService wrapping AsyncIOScheduler + MongoDBJobStore
- `backend/routes/schedules.py` — full CRUD API endpoints under `/api/schedules`
- `backend/tests/test_scheduler_service.py` — 17 service tests
- `backend/tests/test_schedule_routes.py` — 13 route tests

### Frontend
- `frontend/src/components/schedules/index.js` — barrel exports
- `frontend/src/components/schedules/ScheduledScansPage.jsx` — main page with list, filter, empty state
- `frontend/src/components/schedules/ScheduleCard.jsx` — card with status, controls, embedded history
- `frontend/src/components/schedules/ScheduleForm.jsx` — modal form with cron presets, timezone, scan type grid

## Files Modified

### Backend
- `backend/requirements.txt` — added `apscheduler>=3.10.4`
- `backend/app.py` — import + register schedules router; start scheduler in lifespan
- `backend/services/service_registry.py` — register ScanSchedulerService (initialize/get/shutdown)
- `backend/database.py` — add ScanSchedule to Beanie document_models

### Frontend
- `frontend/src/services/api.js` — added `schedulesAPI` with full CRUD + history methods
- `frontend/src/layouts/MainLayout.jsx` — lazy import + route for `/scheduled-scans`
- `frontend/src/layouts/Sidebar.jsx` — nav item with ClockIcon, amber gradient

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/schedules?project_id= | List schedules |
| POST | /api/schedules | Create schedule |
| GET | /api/schedules/{id} | Get schedule |
| PUT | /api/schedules/{id} | Update schedule |
| DELETE | /api/schedules/{id} | Delete schedule |
| POST | /api/schedules/{id}/run | Trigger immediately |
| PATCH | /api/schedules/{id}/toggle | Enable/disable |
| GET | /api/schedules/{id}/history | Run history |

## Key Architecture Decisions
- Singleton scheduler via ServiceRegistry (avoids duplicate instances)
- Auth: non-admin users see only their own schedules; admins see all
- Schedules survive restarts via MongoDBJobStore
- WebSocket notifications on scheduled scan lifecycle events
- Scan metadata tagged with `schedule_id`/`schedule_name` for history tracking
