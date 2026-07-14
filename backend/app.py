"""
ONYX Security Intelligence Platform - Main FastAPI Application
Production-ready application with MongoDB Atlas integration and realistic security scanning
"""
import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import shutil

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    try:
        print(f"📄 Loaded environment variables from: {env_path}")
    except UnicodeEncodeError:
        print(f"[OK] Loaded environment variables from: {env_path}")
else:
    try:
        print(f"⚠️ No .env file found at: {env_path}")
    except UnicodeEncodeError:
        print(f"[WARN] No .env file found at: {env_path}")

# Import database manager
from database import db_manager, init_database, close_database

# Import WebSocket manager for real-time notifications
from services.notifications.websocket_manager import ws_manager

# Import route modules
from routes.reports import router as reports_router
from routes.webhook import router as webhook_router
from routes.auth import router as auth_router
from routes.projects import router as projects_router
from routes.users import router as users_router
from routes.compliance import router as compliance_router
from routes.security import router as security_router
from routes.advanced_security import router as advanced_security_router  # Consolidated security routes
from routes.advanced_scanning_fastapi import router as advanced_scanning_router
from routes.enterprise import router as enterprise_router
from routes.enterprise_security import router as enterprise_security_router
from routes.admin import router as admin_router

# Import centralized service registry
from services.service_registry import ServiceRegistry

# Import configuration
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    
    # Startup
    logger.info("🚀 Starting ONYX Security Intelligence Platform...")
    db_result = await init_database()
    if not db_result:
        logger.error("⚠️ Database/Beanie initialization failed - auth endpoints will return 503")
    
    # Initialize all services via centralized registry (replaces duplicate initializations)
    try:
        service_status = ServiceRegistry.initialize()
        active_count = sum(1 for v in service_status.values() if v)
        total_count = len(service_status)
        logger.info(f"🛡️ Service Registry: {active_count}/{total_count} services initialized")
    except Exception as e:
        logger.warning(f"⚠️ Service Registry initialization error: {e}")
    
    # Start threat intelligence engine background tasks
    threat_intel = ServiceRegistry.get_threat_intelligence()
    if threat_intel and hasattr(threat_intel, 'start'):
        try:
            await threat_intel.start()
            logger.info("🛡️ Threat Intelligence Engine background tasks started")
        except Exception as e:
            logger.warning(f"⚠️ Threat Intelligence Engine failed to start: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ONYX Security Intelligence Platform...")
    
    # Shutdown all services via registry
    try:
        await ServiceRegistry.shutdown()
    except Exception as e:
        logger.warning(f"⚠️ Error during service shutdown: {e}")
    
    await close_database()

# Create FastAPI app with lifespan
app = FastAPI(
    title="ONYX - Security Intelligence Platform",
    description="AI-Powered Security Analysis & Vulnerability Detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiting to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS settings from environment variables
allowed_origins = settings.cors_origins_list

# Also check ALLOWED_ORIGINS for backward compatibility
if settings.allowed_origins:
    additional_origins = [origin.strip() for origin in settings.allowed_origins.split(',') if origin.strip()]
    allowed_origins.extend(additional_origins)

# Remove duplicates
allowed_origins = list(set(allowed_origins))

logger.info(f"🌐 CORS allowed origins: {allowed_origins}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Handle OPTIONS requests explicitly
@app.options("/{full_path:path}")
async def options_handler():
    return {"message": "OK"}

# Include API routers with consistent /api/v1/ versioning
# Core routes
app.include_router(auth_router, prefix="/api")
app.include_router(reports_router, prefix="/api/reports")
app.include_router(projects_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")
app.include_router(admin_router, prefix="/api")  # Admin dashboard and management

# Security routes (consolidated)
app.include_router(security_router)  # Core security: /api/security/*
app.include_router(advanced_security_router)  # Advanced security: /api/v1/security/*
app.include_router(advanced_scanning_router)  # Scanning: /api/advanced-scanning/*

# Compliance and Enterprise routes
app.include_router(compliance_router, prefix="/api/compliance")
app.include_router(enterprise_router)  # Enterprise features: /api/enterprise/*
app.include_router(enterprise_security_router)  # Enterprise security: /api/v1/enterprise-security/*

# Add trailing slash redirect middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import Request, Response
from fastapi.responses import RedirectResponse

@app.middleware("http")
async def redirect_trailing_slash(request: Request, call_next):
    """Handle trailing slash redirects properly"""
    url = str(request.url)
    path = request.url.path
    
    # Don't redirect API calls - let FastAPI handle them
    if "/api/" in path or "/ws" in path or "/health" in path:
        response = await call_next(request)
        return response
    
    # Handle other redirects
    if url.endswith("/") and len(url) > 1:
        url = url[:-1]
        return RedirectResponse(url=url, status_code=301)
    
    response = await call_next(request)
    return response

# Request body size limit middleware (10MB max)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    """Limit request body size to prevent DoS attacks"""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large. Maximum size is 10MB."}
                )
        except ValueError:
            pass  # Invalid content-length header, let FastAPI handle it
    
    return await call_next(request)

@app.get("/api/analytics/overview")
async def get_analytics_overview(days_back: int = 30):
    """Get analytics overview from database - fetches real scan data"""
    try:
        from database import db_manager
        from datetime import timedelta
        from models.report import ScanReport, ScanStatus
        
        if db_manager.db is None:
            raise Exception("Database not connected")
        
        # Calculate cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Fetch reports from scan_reports collection using Beanie
        reports = await ScanReport.find(
            ScanReport.created_at >= cutoff_date
        ).to_list()
        
        # Calculate analytics
        total_scans = len(reports)
        completed_scans = len([r for r in reports if r.status == ScanStatus.COMPLETED])
        failed_scans = len([r for r in reports if r.status == ScanStatus.FAILED])
        
        # Aggregate findings by severity
        vulnerability_summary = {
            "critical": sum(r.findings_by_severity.get("critical", 0) for r in reports),
            "high": sum(r.findings_by_severity.get("high", 0) for r in reports),
            "medium": sum(r.findings_by_severity.get("medium", 0) for r in reports),
            "low": sum(r.findings_by_severity.get("low", 0) for r in reports),
            "info": sum(r.findings_by_severity.get("info", 0) for r in reports)
        }
        
        # Scanner performance
        scanner_performance = {}
        for report in reports:
            for scan_result in report.scan_results:
                scanner = scan_result.scanner.value if hasattr(scan_result.scanner, 'value') else str(scan_result.scanner)
                if scanner not in scanner_performance:
                    scanner_performance[scanner] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "total_findings": 0,
                        "avg_duration": 0,
                        "total_duration": 0
                    }
                
                scanner_performance[scanner]["total_runs"] += 1
                if scan_result.status == ScanStatus.COMPLETED:
                    scanner_performance[scanner]["successful_runs"] += 1
                    scanner_performance[scanner]["total_findings"] += len(scan_result.findings)
                    if scan_result.duration_seconds:
                        scanner_performance[scanner]["total_duration"] += scan_result.duration_seconds
        
        # Calculate average durations
        for scanner, stats in scanner_performance.items():
            if stats["successful_runs"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["successful_runs"]
            del stats["total_duration"]  # Remove temporary field
        
        # Top projects by findings
        project_findings = {}
        for report in reports:
            project = report.project_name
            if project not in project_findings:
                project_findings[project] = {
                    "project_name": project,
                    "total_findings": 0,
                    "scans_count": 0,
                    "critical_findings": 0,
                    "high_findings": 0
                }
            
            project_findings[project]["total_findings"] += report.total_findings
            project_findings[project]["scans_count"] += 1
            project_findings[project]["critical_findings"] += report.findings_by_severity.get("critical", 0)
            project_findings[project]["high_findings"] += report.findings_by_severity.get("high", 0)
        
        # Sort top projects by total findings
        top_projects = sorted(
            project_findings.values(),
            key=lambda x: x["total_findings"],
            reverse=True
        )[:10]
        
        return {
            "period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat()
            },
            "scan_summary": {
                "total_scans": total_scans,
                "completed_scans": completed_scans,
                "failed_scans": failed_scans,
                "success_rate": (completed_scans / total_scans * 100) if total_scans > 0 else 0
            },
            "vulnerability_summary": vulnerability_summary,
            "scanner_performance": scanner_performance,
            "top_projects": top_projects
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        logger.error(f"Analytics error traceback: {traceback.format_exc()}")
        # Return empty analytics on error
        return {
            "period": {"days_back": days_back},
            "scan_summary": {
                "total_scans": 0,
                "completed_scans": 0,
                "failed_scans": 0,
                "success_rate": 0
            },
            "vulnerability_summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "scanner_performance": {},
            "top_projects": []
        }

# Pydantic models
class ScanRequest(BaseModel):
    repository_url: str
    branch: str = "main"
    scan_types: List[str] = ["sast", "container", "secrets", "infrastructure"]
    access_token: str = None  # Optional access token for private repositories

class ScanStatus(BaseModel):
    scan_id: str
    status: str
    progress: int
    message: str

class FindingModel(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: int
    scanner: str

class ReportModel(BaseModel):
    id: str
    project_name: str
    repository_url: str
    branch: str
    status: str
    findings_count: int
    created_at: str
    findings: List[FindingModel]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ONYX Security Intelligence Platform - Local Development", "status": "running"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint - Returns truthful status of all services.
    
    Status levels:
    - healthy: All critical services operational
    - degraded: API running but some services (like DB) are unavailable
    - unhealthy: Critical failure (API shouldn't reach this if truly down)
    """
    # Track issues for accurate status reporting
    issues = []
    warnings = []
    
    health_data = {
        "status": "healthy",  # Will be updated based on checks
        "version": "1.0.0",
        "build_date": "2025-12-25",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "services": {
            "api": "running",
            "database": "unknown",
            "scanners": "available",
            "ai": "unknown"
        },
        "database": {
            "connected": False,
            "latency_ms": None
        },
        "ai": {
            "provider": settings.ai_provider,
            "configured": False,
            "message": ""
        },
        "scanners": {
            "active": 0,
            "total": 6,
            "available": []
        },
        "issues": [],
        "warnings": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Check database connection
    try:
        import time
        start_time = time.time()
        db_status = await db_manager.test_connection()
        latency_ms = (time.time() - start_time) * 1000
        
        health_data["services"]["database"] = db_status
        health_data["database"]["connected"] = db_status == "connected"
        health_data["database"]["latency_ms"] = round(latency_ms, 2)
        
        if db_status != "connected":
            issues.append(f"Database not connected: status={db_status}")
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_data["services"]["database"] = "error"
        health_data["database"]["connected"] = False
        issues.append(f"Database connection failed: {str(e)}")
    
    # Check AI configuration
    try:
        ai_valid, ai_message = settings.validate_ai_config()
        health_data["ai"]["configured"] = ai_valid
        health_data["ai"]["message"] = ai_message
        health_data["services"]["ai"] = "configured" if ai_valid else "not_configured"
        
        if not ai_valid:
            warnings.append(f"AI not configured: {ai_message}")
    except Exception as e:
        health_data["ai"]["configured"] = False
        health_data["ai"]["message"] = str(e)
        health_data["services"]["ai"] = "error"
        warnings.append(f"AI configuration check failed: {str(e)}")
    
    # Check scanner availability
    available_scanners = []
    scanner_checks = [
        ("bandit", "bandit"),
        ("safety", "safety"),
        ("semgrep", "semgrep"),
        ("trivy", "trivy"),
        ("gitleaks", "gitleaks"),
        ("lynis", "lynis")
    ]
    
    for scanner_name, _ in scanner_checks:
        # Verify scanner is both enabled AND actually installed on the system
        if settings.__dict__.get(f"enable_{scanner_name}", True):
            scanner_path = getattr(settings, f"{scanner_name}_path", scanner_name)
            if shutil.which(scanner_path):
                available_scanners.append(scanner_name)
            else:
                warnings.append(f"Scanner '{scanner_name}' is enabled but not found in PATH")
    
    health_data["scanners"]["available"] = available_scanners
    health_data["scanners"]["active"] = len(available_scanners) if health_data["database"]["connected"] else 0
    
    # Determine overall status
    health_data["issues"] = issues
    health_data["warnings"] = warnings
    
    if issues:
        # Has critical issues - degraded but API is running
        health_data["status"] = "degraded"
    elif warnings:
        # Has warnings but functional
        health_data["status"] = "healthy"
    else:
        health_data["status"] = "healthy"
    
    return health_data


@app.get("/api/stats/public")
async def get_public_stats():
    """Get public statistics for landing page - no auth required"""
    try:
        from models.report import ScanReport
        from models.user import User
        
        if db_manager.db is None:
            return {
                "total_scans": 0,
                "total_vulnerabilities": 0,
                "total_users": 0,
                "uptime_percentage": None
            }
        
        # Get real counts from database
        total_scans = await ScanReport.count()
        total_users = await User.count()
        
        # Calculate total vulnerabilities from all reports
        reports = await ScanReport.find_all().to_list()
        total_vulnerabilities = sum(
            r.total_findings for r in reports if r.total_findings
        )
        
        return {
            "total_scans": total_scans,
            "total_vulnerabilities": total_vulnerabilities,
            "total_users": total_users,
            "uptime_percentage": None  # Requires external monitoring (e.g., UptimeRobot, Betterstack)
        }
        
    except Exception as e:
        logger.error(f"Error getting public stats: {e}")
        return {
            "total_scans": 0,
            "total_vulnerabilities": 0,
            "total_users": 0,
            "uptime_percentage": None
        }


async def _check_scanner_availability(scanner_name: str, command: List[str]) -> Dict[str, Any]:
    """Check if a scanner is available and get its version."""
    import asyncio
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
        
        if process.returncode == 0:
            version = stdout.decode().strip().split('\n')[0] if stdout else "unknown"
            # Extract version number from output
            import re
            version_match = re.search(r'[\d]+\.[\d]+\.[\d]+', version)
            version = version_match.group(0) if version_match else version[:50]
            return {"status": "available", "version": version}
        else:
            return {"status": "unavailable", "version": "N/A", "error": "Command failed"}
    except asyncio.TimeoutError:
        return {"status": "unavailable", "version": "N/A", "error": "Timeout"}
    except FileNotFoundError:
        return {"status": "not_installed", "version": "N/A", "error": "Scanner not found in PATH"}
    except Exception as e:
        return {"status": "error", "version": "N/A", "error": str(e)}


@app.get("/api/scanners/health")
async def get_scanners_health():
    """Get actual scanner health status by checking each scanner's availability."""
    import asyncio
    
    # Define scanner check commands
    scanner_checks = {
        "semgrep": ["semgrep", "--version"],
        "trivy": ["trivy", "--version"],
        "gitleaks": ["gitleaks", "version"],
        "bandit": ["bandit", "--version"],
        "safety": ["safety", "--version"],
    }
    
    # Check all scanners in parallel
    results = {}
    tasks = []
    scanner_names = []
    
    for name, command in scanner_checks.items():
        tasks.append(_check_scanner_availability(name, command))
        scanner_names.append(name)
    
    check_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    available_count = 0
    for name, result in zip(scanner_names, check_results):
        if isinstance(result, Exception):
            results[name] = {"status": "error", "version": "N/A", "error": str(result)}
        else:
            results[name] = result
            if result.get("status") == "available":
                available_count += 1
    
    # Determine overall status
    total_scanners = len(scanner_checks)
    if available_count == total_scanners:
        overall_status = "healthy"
    elif available_count >= total_scanners // 2:
        overall_status = "degraded"
    elif available_count > 0:
        overall_status = "limited"
    else:
        overall_status = "unavailable"
    
    return {
        "scanners": results,
        "overall_status": overall_status,
        "available_count": available_count,
        "total_count": total_scanners,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    """
    WebSocket endpoint for real-time updates.
    Supports optional authentication via token query parameter.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_host}")
    
    # Extract user_id from token if provided
    user_id = None
    if token:
        try:
            from services.auth.auth_service import auth_service
            payload = auth_service.verify_token(token, "access")
            if payload:
                user_id = payload.get("sub")
                logger.info(f"WebSocket authenticated for user: {user_id}")
        except Exception as auth_error:
            logger.warning(f"WebSocket token verification failed: {auth_error}")
    
    try:
        # Connect using the WebSocket manager
        await ws_manager.connect(websocket, user_id)
        
        # Send periodic heartbeat and listen for messages
        heartbeat_count = 0
        while True:
            try:
                # Wait for messages with timeout for heartbeat
                try:
                    # Try to receive message with 30 second timeout
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=30.0
                    )
                    # Handle incoming messages (e.g., ping/pong, subscription requests)
                    try:
                        message = json.loads(data)
                        if message.get("type") == "ping":
                            await websocket.send_json({
                                "type": "pong",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                        elif message.get("type") == "subscribe":
                            # Handle subscription requests (future feature)
                            pass
                    except json.JSONDecodeError:
                        pass
                except asyncio.TimeoutError:
                    # No message received, send heartbeat
                    heartbeat_count += 1
                    await websocket.send_json({
                        "type": "heartbeat",
                        "data": {
                            "count": heartbeat_count,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "status": "active",
                            "connections": ws_manager.get_connection_count()
                        }
                    })
                
            except ConnectionResetError:
                logger.info(f"WebSocket connection reset by client {client_host}")
                break
            except Exception as send_error:
                logger.warning(f"Error in WebSocket loop for {client_host}: {send_error}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_host} disconnected normally")
    except ConnectionResetError:
        logger.info(f"WebSocket connection reset by client {client_host}")
    except Exception as e:
        logger.error(f"WebSocket error with client {client_host}: {e}")
    finally:
        await ws_manager.disconnect(websocket)
        logger.info(f"WebSocket connection with {client_host} closed")

if __name__ == "__main__":
    print("[ONYX] Starting ONYX Security Intelligence Platform - Production Server")
    print(f"[DOCS] API Documentation: {settings.backend_url or f'http://{settings.host}:{settings.port}'}/docs")
    print(f"[HEALTH] Health Check: {settings.backend_url or f'http://{settings.host}:{settings.port}'}/health")
    print(f"[FRONTEND] Frontend should run on: {settings.frontend_url or 'Frontend URL not configured'}")
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
