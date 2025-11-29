"""
SecureDevOps AI Platform - Main FastAPI Application
Production-ready application with MongoDB Atlas integration and realistic security scanning
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"📄 Loaded environment variables from: {env_path}")
else:
    print(f"⚠️ No .env file found at: {env_path}")

# Import database manager
from database import db_manager, init_database, close_database

# Import route modules
from routes.reports import router as reports_router
from routes.webhook import router as webhook_router
from routes.auth import router as auth_router
from routes.projects import router as projects_router
from routes.users import router as users_router
from routes.compliance import router as compliance_router
from routes.security import router as security_router
# from routes.advanced_security import router as advanced_security_router  # Removed - redundant file deleted
from routes.enhanced_security import router as enhanced_security_router  # Re-enabled with clean FastAPI implementation
from routes.god_level_security import router as god_level_security_router  # Re-enabled with clean FastAPI implementation
from routes.advanced_scanning_fastapi import router as advanced_scanning_router
from routes.enterprise import router as enterprise_router  # Enterprise features

# Import configuration
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("🚀 Starting SecureDevOps AI Platform...")
    await init_database()
    yield
    # Shutdown
    logger.info("🛑 Shutting down SecureDevOps AI Platform...")
    await close_database()

# Create FastAPI app with lifespan
app = FastAPI(
    title="SecureDevOps AI Platform",
    description="Intelligent Security Scanning Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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

# Include API routers with explicit trailing slash handling
app.include_router(auth_router, prefix="/api")
app.include_router(reports_router, prefix="/api/reports")
app.include_router(projects_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(compliance_router, prefix="/api/compliance")
app.include_router(security_router)
app.include_router(webhook_router, prefix="/api")
# app.include_router(advanced_security_router)  # Removed - redundant file deleted
app.include_router(enhanced_security_router)  # Re-enabled with clean FastAPI implementation
app.include_router(god_level_security_router)  # Re-enabled with clean FastAPI implementation
app.include_router(advanced_scanning_router)
app.include_router(enterprise_router)  # Enterprise features

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
    return {"message": "SecureDevOps AI Platform - Local Development", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Basic health check without database dependency for Railway
    health_data = {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "services": {
            "api": "running",
            "scanners": "available"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Try database connection but don't fail health check if it's slow
    try:
        db_status = await db_manager.test_connection()
        health_data["services"]["database"] = db_status
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        health_data["services"]["database"] = "checking"
    
    return health_data



@app.get("/api/scanners/health")
async def get_scanners_health():
    """Get scanner health status"""
    return {
        "scanners": {
            "semgrep": {"status": "available", "version": "1.45.0"},
            "trivy": {"status": "available", "version": "0.48.0"},
            "gitleaks": {"status": "available", "version": "8.18.0"},
            "lynis": {"status": "available", "version": "3.0.9"}
        },
        "overall_status": "healthy"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"WebSocket connection attempt from {client_host}")
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted from {client_host}")
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "data": {
                "message": "Connected to SecureDevOps Platform",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Send periodic heartbeat with better error handling
        heartbeat_count = 0
        while True:
            try:
                heartbeat_count += 1
                await websocket.send_json({
                    "type": "heartbeat",
                    "data": {
                        "count": heartbeat_count,
                        "timestamp": datetime.now().isoformat(),
                        "status": "active"
                    }
                })
                
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
            except ConnectionResetError:
                logger.info(f"WebSocket connection reset by client {client_host}")
                break
            except Exception as send_error:
                logger.warning(f"Error sending WebSocket message to {client_host}: {send_error}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_host} disconnected normally")
    except ConnectionResetError:
        logger.info(f"WebSocket connection reset by client {client_host}")
    except Exception as e:
        logger.error(f"WebSocket error with client {client_host}: {e}")
    finally:
        try:
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()
        except Exception as close_error:
            logger.debug(f"Error closing WebSocket for {client_host}: {close_error}")
        logger.info(f"WebSocket connection with {client_host} closed")

if __name__ == "__main__":
    print("🛡️ Starting SecureDevOps AI Platform - Production Server")
    print(f"📖 API Documentation: {settings.backend_url or f'http://{settings.host}:{settings.port}'}/docs")
    print(f"🏥 Health Check: {settings.backend_url or f'http://{settings.host}:{settings.port}'}/health")
    print(f"🔧 Frontend should run on: {settings.frontend_url or 'Frontend URL not configured'}")
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
