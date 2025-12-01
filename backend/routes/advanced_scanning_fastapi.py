#!/usr/bin/env python3
"""
Advanced Scanning FastAPI Routes
Unified pipeline for ZAP, Nuclei, CodeQL, and Checkov integration
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import asyncio
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import shutil
import git
from urllib.parse import urlparse

from services.scanning.advanced_scanner_engine import (
    AdvancedScannerEngine, 
    ScanConfig, 
    Finding,
    ScanType,
    Severity
)
from database import db_manager

logger = logging.getLogger(__name__)

# FastAPI router
router = APIRouter(prefix="/api/advanced-scanning", tags=["Advanced Scanning"])

# Security
security = HTTPBearer()

# Request/Response models
class ComprehensiveScanRequest(BaseModel):
    repository_url: HttpUrl
    target_url: Optional[HttpUrl] = None
    config: Optional[Dict[str, Any]] = {}

class SASTScanRequest(BaseModel):
    repository_url: HttpUrl
    languages: Optional[List[str]] = []

class DASTScanRequest(BaseModel):
    target_url: HttpUrl

class IaCScanRequest(BaseModel):
    repository_url: HttpUrl
    frameworks: Optional[List[str]] = []

class SuppressionRuleRequest(BaseModel):
    name: str
    description: str
    repository_url: HttpUrl
    rule_ids: Optional[List[str]] = []
    file_patterns: Optional[List[str]] = []
    severities: Optional[List[str]] = []
    scanners: Optional[List[str]] = []

class ScanResponse(BaseModel):
    success: bool
    scan_id: str
    report_id: str
    summary: Dict[str, Any]
    duration: Optional[float] = None

# Global scanner engine instance
scanner_engine = None

def get_scanner_engine():
    """Get or create scanner engine instance"""
    global scanner_engine
    if scanner_engine is None:
        config = ScanConfig(
            max_concurrent_scans=3,
            scan_timeout=1800,  # 30 minutes
            dast_target_allowlist=get_allowed_targets(),
            dast_rate_limit=2.0,
            sast_languages=["python", "javascript", "java", "go", "csharp", "cpp"],
            iac_frameworks=["terraform", "cloudformation", "kubernetes", "docker"],
            suppression_file=".security-suppressions.yaml",
            allow_inline_suppressions=True
        )
        scanner_engine = AdvancedScannerEngine(config)
    return scanner_engine

def get_allowed_targets():
    """Get allowed DAST targets from configuration"""
    return [
        "localhost",
        "127.0.0.1",
        "example.com",
        "staging.example.com",
        "test.example.com"
    ]

async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token"""
    # This would typically validate JWT and return user info
    # For now, return a mock user
    return {"user_id": "user123", "username": "testuser"}

@router.post("/scan/comprehensive", response_model=ScanResponse)
async def comprehensive_scan(
    request: ComprehensiveScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start comprehensive security scan with all available scanners
    """
    try:
        user_id = current_user["user_id"]
        repository_url = str(request.repository_url)
        target_url = str(request.target_url) if request.target_url else None
        
        # Validate target URL if provided
        if target_url and not is_target_allowed(target_url):
            raise HTTPException(
                status_code=403,
                detail=f"Target URL {target_url} is not in allowlist"
            )
        
        # Start scan in background
        scan_task = start_comprehensive_scan_task(
            repository_url, target_url, request.config, user_id
        )
        background_tasks.add_task(scan_task)
        
        # Return immediate response with scan ID
        scan_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "estimated_duration": "15-30 minutes"},
            duration=0.0
        )
        
    except Exception as e:
        logger.error(f"Comprehensive scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

async def start_comprehensive_scan_task(
    repository_url: str, 
    target_url: Optional[str], 
    scan_config: Dict,
    user_id: str
):
    """Background task for comprehensive scanning"""
    temp_dir = None
    try:
        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp(prefix='advanced_scan_')
        logger.info(f"Cloning repository {repository_url} to {temp_dir}")
        repo = git.Repo.clone_from(repository_url, temp_dir)
        
        # Update scanner configuration if provided
        engine = get_scanner_engine()
        if scan_config:
            update_scanner_config(engine.config, scan_config)
        
        # Start comprehensive scan
        logger.info(f"Starting comprehensive scan for {repository_url}")
        scan_results = await engine.scan_repository(temp_dir, target_url)
        
        # Save results to database
        report_data = {
            'scan_id': scan_results['scan_id'],
            'user_id': user_id,
            'repository_url': repository_url,
            'target_url': target_url,
            'scan_type': 'comprehensive',
            'results': scan_results,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db_manager.save_scan_report(report_data)
        logger.info(f"Comprehensive scan {scan_results['scan_id']} completed")
        
    except Exception as e:
        logger.error(f"Background comprehensive scan failed: {e}")
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {e}")

@router.post("/scan/sast", response_model=ScanResponse)
async def sast_scan(
    request: SASTScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start SAST scan using CodeQL
    """
    try:
        user_id = current_user["user_id"]
        repository_url = str(request.repository_url)
        
        # Start scan in background
        scan_task = start_sast_scan_task(repository_url, request.languages, user_id)
        background_tasks.add_task(scan_task)
        
        scan_id = f"sast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "languages": request.languages},
            duration=0.0
        )
        
    except Exception as e:
        logger.error(f"SAST scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"SAST scan failed: {str(e)}")

async def start_sast_scan_task(
    repository_url: str,
    languages: List[str],
    user_id: str
):
    """Background task for SAST scanning"""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix='sast_scan_')
        repo = git.Repo.clone_from(repository_url, temp_dir)
        
        engine = get_scanner_engine()
        if languages:
            engine.config.sast_languages = languages
        
        scan_id = f"sast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        findings = await engine.codeql_scanner.scan(temp_dir, scan_id)
        
        # Apply suppressions
        for finding in findings:
            should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
            if should_suppress:
                finding.suppressed = True
                finding.suppression_reason = reason
        
        # Generate and save results
        results = {
            'scan_id': scan_id,
            'scan_type': 'sast',
            'repository_url': repository_url,
            'findings': [finding.__dict__ for finding in findings],
            'summary': generate_findings_summary(findings)
        }
        
        report_data = {
            'scan_id': scan_id,
            'user_id': user_id,
            'scan_type': 'sast',
            'results': results,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db_manager.save_scan_report(report_data)
        logger.info(f"SAST scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Background SAST scan failed: {e}")
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/scan/dast", response_model=ScanResponse)
async def dast_scan(
    request: DASTScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start DAST scan using ZAP and Nuclei
    """
    try:
        user_id = current_user["user_id"]
        target_url = str(request.target_url)
        
        # Validate target
        if not is_target_allowed(target_url):
            raise HTTPException(
                status_code=403,
                detail=f"Target URL {target_url} is not in allowlist"
            )
        
        # Start scan in background
        scan_task = start_dast_scan_task(target_url, user_id)
        background_tasks.add_task(scan_task)
        
        scan_id = f"dast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "target": target_url},
            duration=0.0
        )
        
    except Exception as e:
        logger.error(f"DAST scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"DAST scan failed: {str(e)}")

async def start_dast_scan_task(target_url: str, user_id: str):
    """Background task for DAST scanning"""
    try:
        engine = get_scanner_engine()
        scan_id = f"dast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Run both ZAP and Nuclei
        tasks = [
            engine.zap_scanner.scan(target_url, f"{scan_id}_zap"),
            engine.nuclei_scanner.scan(target_url, f"{scan_id}_nuclei")
        ]
        
        zap_findings, nuclei_findings = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_findings = []
        scanner_results = {}
        
        # Process results
        if isinstance(zap_findings, Exception):
            logger.error(f"ZAP scan failed: {zap_findings}")
            scanner_results['zap'] = {'error': str(zap_findings)}
        else:
            all_findings.extend(zap_findings)
            scanner_results['zap'] = {'findings_count': len(zap_findings)}
        
        if isinstance(nuclei_findings, Exception):
            logger.error(f"Nuclei scan failed: {nuclei_findings}")
            scanner_results['nuclei'] = {'error': str(nuclei_findings)}
        else:
            all_findings.extend(nuclei_findings)
            scanner_results['nuclei'] = {'findings_count': len(nuclei_findings)}
        
        # Generate and save results
        results = {
            'scan_id': scan_id,
            'scan_type': 'dast',
            'target_url': target_url,
            'findings': [finding.__dict__ for finding in all_findings],
            'summary': generate_findings_summary(all_findings),
            'scanners': scanner_results
        }
        
        report_data = {
            'scan_id': scan_id,
            'user_id': user_id,
            'scan_type': 'dast',
            'results': results,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db_manager.save_scan_report(report_data)
        logger.info(f"DAST scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Background DAST scan failed: {e}")

@router.post("/scan/iac", response_model=ScanResponse)
async def iac_scan(
    request: IaCScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start Infrastructure as Code scan using Checkov
    """
    try:
        user_id = current_user["user_id"]
        repository_url = str(request.repository_url)
        
        # Start scan in background
        scan_task = start_iac_scan_task(repository_url, request.frameworks, user_id)
        background_tasks.add_task(scan_task)
        
        scan_id = f"iac_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ScanResponse(
            success=True,
            scan_id=scan_id,
            report_id="pending",
            summary={"status": "started", "frameworks": request.frameworks},
            duration=0.0
        )
        
    except Exception as e:
        logger.error(f"IaC scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"IaC scan failed: {str(e)}")

async def start_iac_scan_task(
    repository_url: str,
    frameworks: List[str],
    user_id: str
):
    """Background task for IaC scanning"""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix='iac_scan_')
        repo = git.Repo.clone_from(repository_url, temp_dir)
        
        engine = get_scanner_engine()
        if frameworks:
            engine.config.iac_frameworks = frameworks
        
        scan_id = f"iac_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        findings = await engine.checkov_scanner.scan(temp_dir, scan_id)
        
        # Apply suppressions
        for finding in findings:
            should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
            if should_suppress:
                finding.suppressed = True
                finding.suppression_reason = reason
        
        # Generate and save results
        results = {
            'scan_id': scan_id,
            'scan_type': 'iac',
            'repository_url': repository_url,
            'findings': [finding.__dict__ for finding in findings],
            'summary': generate_findings_summary(findings)
        }
        
        report_data = {
            'scan_id': scan_id,
            'user_id': user_id,
            'scan_type': 'iac',
            'results': results,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db_manager.save_scan_report(report_data)
        logger.info(f"IaC scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Background IaC scan failed: {e}")
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/suppressions")
async def get_suppressions(
    repository_url: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get suppression rules for a repository
    """
    try:
        # Load suppression rules from database or repository
        suppressions = await db_manager.get_suppression_rules(repository_url)
        
        return {
            'success': True,
            'suppressions': suppressions
        }
    
    except Exception as e:
        logger.error(f"Failed to get suppressions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suppressions: {str(e)}")

@router.post("/suppressions")
async def create_suppression(
    request: SuppressionRuleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create new suppression rule
    """
    try:
        user_id = current_user["user_id"]
        
        suppression_rule = {
            'id': str(datetime.now().timestamp()),
            'name': request.name,
            'description': request.description,
            'repository_url': str(request.repository_url),
            'rule_ids': request.rule_ids,
            'file_patterns': request.file_patterns,
            'severities': request.severities,
            'scanners': request.scanners,
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc)
        }
        
        rule_id = await db_manager.save_suppression_rule(suppression_rule)
        
        return {
            'success': True,
            'suppression_id': rule_id,
            'message': 'Suppression rule created successfully'
        }
    
    except Exception as e:
        logger.error(f"Failed to create suppression: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create suppression: {str(e)}")

@router.get("/scan/{scan_id}/findings")
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = None,
    scanner: Optional[str] = None,
    scan_type: Optional[str] = None,
    suppressed: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get findings for a specific scan
    """
    try:
        report = await db_manager.get_scan_report(scan_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        findings = report['results']['findings']
        
        # Apply filters
        filtered_findings = []
        for finding in findings:
            # Skip suppressed findings unless explicitly requested
            if finding.get('suppressed', False) and not suppressed:
                continue
            
            # Apply filters
            if severity and finding.get('severity') != severity:
                continue
            if scanner and finding.get('source') != scanner:
                continue
            if scan_type and finding.get('scan_type') != scan_type:
                continue
            
            filtered_findings.append(finding)
        
        return {
            'success': True,
            'scan_id': scan_id,
            'findings': filtered_findings,
            'total_count': len(filtered_findings),
            'filters_applied': {
                'severity': severity,
                'scanner': scanner,
                'scan_type': scan_type,
                'include_suppressed': suppressed
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan findings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get findings: {str(e)}")

@router.get("/scan/{scan_id}/summary")
async def get_scan_summary(
    scan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get summary for a specific scan
    """
    try:
        report = await db_manager.get_scan_report(scan_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        results = report['results']
        
        return {
            'success': True,
            'scan_id': scan_id,
            'summary': results.get('summary', {}),
            'scanners': results.get('scanners', {}),
            'duration': results.get('duration', 0),
            'start_time': results.get('start_time'),
            'end_time': results.get('end_time')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/config")
async def get_scanner_config(current_user: dict = Depends(get_current_user)):
    """
    Get current scanner configuration
    """
    try:
        engine = get_scanner_engine()
        config = engine.config
        
        return {
            'success': True,
            'config': {
                'max_concurrent_scans': config.max_concurrent_scans,
                'scan_timeout': config.scan_timeout,
                'dast_target_allowlist': config.dast_target_allowlist,
                'dast_rate_limit': config.dast_rate_limit,
                'dast_max_depth': config.dast_max_depth,
                'sast_languages': config.sast_languages,
                'sast_exclude_patterns': config.sast_exclude_patterns,
                'iac_frameworks': config.iac_frameworks,
                'suppression_file': config.suppression_file,
                'allow_inline_suppressions': config.allow_inline_suppressions
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get scanner config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

# Helper functions

def is_target_allowed(target_url: str) -> bool:
    """Check if target URL is in allowlist"""
    try:
        parsed_url = urlparse(target_url)
        target_host = parsed_url.netloc.lower()
        
        allowed_targets = get_allowed_targets()
        
        for allowed in allowed_targets:
            if target_host == allowed.lower() or target_host.endswith(f".{allowed.lower()}"):
                return True
        
        return False
    except Exception:
        return False

def update_scanner_config(config: ScanConfig, updates: dict):
    """Update scanner configuration with provided values"""
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)

def generate_findings_summary(findings: list) -> dict:
    """Generate summary statistics for findings"""
    active_findings = [f for f in findings if not getattr(f, 'suppressed', False)]
    
    summary = {
        'total_findings': len(findings),
        'active_findings': len(active_findings),
        'suppressed_findings': len(findings) - len(active_findings),
        'by_severity': {},
        'by_scanner': {},
        'by_scan_type': {},
    }
    
    # Count by severity
    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = len([f for f in active_findings if getattr(f, 'severity', '') == severity])
        summary['by_severity'][severity] = count
    
    # Count by scanner
    scanners = set(getattr(f, 'source', '') for f in active_findings)
    for scanner in scanners:
        count = len([f for f in active_findings if getattr(f, 'source', '') == scanner])
        summary['by_scanner'][scanner] = count
    
    # Count by scan type
    scan_types = set(getattr(f, 'scan_type', '') for f in active_findings)
    for scan_type in scan_types:
        count = len([f for f in active_findings if getattr(f, 'scan_type', '') == scan_type])
        summary['by_scan_type'][scan_type] = count
    
    return summary
