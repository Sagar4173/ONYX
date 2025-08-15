#!/usr/bin/env python3
"""
Advanced Scanning API Routes
Unified pipeline for ZAP, Nuclei, CodeQL, and Checkov integration
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import shutil
import git
from urllib.parse import urlparse

from services.advanced_scanner_engine import (
    AdvancedScannerEngine, 
    ScanConfig, 
    Finding,
    ScanType,
    Severity
)
from models.report import Report
from database import get_db

logger = logging.getLogger(__name__)

advanced_scanning_bp = Blueprint('advanced_scanning', __name__)

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
    # This would typically be loaded from database or config file
    return [
        "localhost",
        "127.0.0.1",
        "example.com",
        "staging.example.com"
    ]

@advanced_scanning_bp.route('/scan/comprehensive', methods=['POST'])
@jwt_required()
async def comprehensive_scan():
    """
    Start comprehensive security scan with all available scanners
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if 'repository_url' not in data:
            return jsonify({
                'error': 'repository_url is required'
            }), 400
        
        repository_url = data['repository_url']
        target_url = data.get('target_url')
        scan_config = data.get('config', {})
        
        # Validate target URL if provided
        if target_url:
            if not is_target_allowed(target_url):
                return jsonify({
                    'error': f'Target URL {target_url} is not in allowlist'
                }), 403
        
        # Clone repository to temporary directory
        temp_dir = tempfile.mkdtemp(prefix='advanced_scan_')
        try:
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
            
            db = get_db()
            report_id = db.reports.insert_one(report_data).inserted_id
            
            return jsonify({
                'success': True,
                'scan_id': scan_results['scan_id'],
                'report_id': str(report_id),
                'summary': scan_results['summary'],
                'scanners': scan_results['scanners'],
                'duration': scan_results['duration']
            })
            
        finally:
            # Cleanup temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {e}")
    
    except Exception as e:
        logger.error(f"Comprehensive scan failed: {e}")
        return jsonify({
            'error': 'Scan failed',
            'details': str(e)
        }), 500

@advanced_scanning_bp.route('/scan/sast', methods=['POST'])
@jwt_required()
async def sast_scan():
    """
    Start SAST scan using CodeQL
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'repository_url' not in data:
            return jsonify({'error': 'repository_url is required'}), 400
        
        repository_url = data['repository_url']
        languages = data.get('languages', [])
        
        # Clone repository
        temp_dir = tempfile.mkdtemp(prefix='sast_scan_')
        try:
            repo = git.Repo.clone_from(repository_url, temp_dir)
            
            # Configure SAST-only scan
            engine = get_scanner_engine()
            if languages:
                engine.config.sast_languages = languages
            
            # Run CodeQL scanner only
            scan_id = f"sast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            findings = await engine.codeql_scanner.scan(temp_dir, scan_id)
            
            # Apply suppressions
            for finding in findings:
                should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
                if should_suppress:
                    finding.suppressed = True
                    finding.suppression_reason = reason
            
            # Generate results
            results = {
                'scan_id': scan_id,
                'scan_type': 'sast',
                'repository_url': repository_url,
                'findings': [finding.__dict__ for finding in findings],
                'summary': generate_findings_summary(findings)
            }
            
            # Save to database
            db = get_db()
            report_id = db.reports.insert_one({
                'scan_id': scan_id,
                'user_id': user_id,
                'scan_type': 'sast',
                'results': results,
                'created_at': datetime.now(timezone.utc)
            }).inserted_id
            
            return jsonify({
                'success': True,
                'scan_id': scan_id,
                'report_id': str(report_id),
                'findings_count': len([f for f in findings if not f.suppressed]),
                'suppressed_count': len([f for f in findings if f.suppressed]),
                'summary': results['summary']
            })
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        logger.error(f"SAST scan failed: {e}")
        return jsonify({'error': 'SAST scan failed', 'details': str(e)}), 500

@advanced_scanning_bp.route('/scan/dast', methods=['POST'])
@jwt_required()
async def dast_scan():
    """
    Start DAST scan using ZAP and Nuclei
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'target_url' not in data:
            return jsonify({'error': 'target_url is required'}), 400
        
        target_url = data['target_url']
        
        # Validate target
        if not is_target_allowed(target_url):
            return jsonify({
                'error': f'Target URL {target_url} is not in allowlist'
            }), 403
        
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
        
        # Process ZAP results
        if isinstance(zap_findings, Exception):
            logger.error(f"ZAP scan failed: {zap_findings}")
            scanner_results['zap'] = {'error': str(zap_findings)}
        else:
            all_findings.extend(zap_findings)
            scanner_results['zap'] = {'findings_count': len(zap_findings)}
        
        # Process Nuclei results
        if isinstance(nuclei_findings, Exception):
            logger.error(f"Nuclei scan failed: {nuclei_findings}")
            scanner_results['nuclei'] = {'error': str(nuclei_findings)}
        else:
            all_findings.extend(nuclei_findings)
            scanner_results['nuclei'] = {'findings_count': len(nuclei_findings)}
        
        # Generate results
        results = {
            'scan_id': scan_id,
            'scan_type': 'dast',
            'target_url': target_url,
            'findings': [finding.__dict__ for finding in all_findings],
            'summary': generate_findings_summary(all_findings),
            'scanners': scanner_results
        }
        
        # Save to database
        db = get_db()
        report_id = db.reports.insert_one({
            'scan_id': scan_id,
            'user_id': user_id,
            'scan_type': 'dast',
            'results': results,
            'created_at': datetime.now(timezone.utc)
        }).inserted_id
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'report_id': str(report_id),
            'findings_count': len(all_findings),
            'summary': results['summary'],
            'scanners': scanner_results
        })
    
    except Exception as e:
        logger.error(f"DAST scan failed: {e}")
        return jsonify({'error': 'DAST scan failed', 'details': str(e)}), 500

@advanced_scanning_bp.route('/scan/iac', methods=['POST'])
@jwt_required()
async def iac_scan():
    """
    Start Infrastructure as Code scan using Checkov
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'repository_url' not in data:
            return jsonify({'error': 'repository_url is required'}), 400
        
        repository_url = data['repository_url']
        frameworks = data.get('frameworks', [])
        
        # Clone repository
        temp_dir = tempfile.mkdtemp(prefix='iac_scan_')
        try:
            repo = git.Repo.clone_from(repository_url, temp_dir)
            
            engine = get_scanner_engine()
            if frameworks:
                engine.config.iac_frameworks = frameworks
            
            # Run Checkov scanner
            scan_id = f"iac_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            findings = await engine.checkov_scanner.scan(temp_dir, scan_id)
            
            # Apply suppressions
            for finding in findings:
                should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
                if should_suppress:
                    finding.suppressed = True
                    finding.suppression_reason = reason
            
            # Generate results
            results = {
                'scan_id': scan_id,
                'scan_type': 'iac',
                'repository_url': repository_url,
                'findings': [finding.__dict__ for finding in findings],
                'summary': generate_findings_summary(findings)
            }
            
            # Save to database
            db = get_db()
            report_id = db.reports.insert_one({
                'scan_id': scan_id,
                'user_id': user_id,
                'scan_type': 'iac',
                'results': results,
                'created_at': datetime.now(timezone.utc)
            }).inserted_id
            
            return jsonify({
                'success': True,
                'scan_id': scan_id,
                'report_id': str(report_id),
                'findings_count': len([f for f in findings if not f.suppressed]),
                'suppressed_count': len([f for f in findings if f.suppressed]),
                'summary': results['summary']
            })
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        logger.error(f"IaC scan failed: {e}")
        return jsonify({'error': 'IaC scan failed', 'details': str(e)}), 500

@advanced_scanning_bp.route('/suppressions', methods=['GET'])
@jwt_required()
def get_suppressions():
    """
    Get suppression rules for a repository
    """
    try:
        repository_url = request.args.get('repository_url')
        if not repository_url:
            return jsonify({'error': 'repository_url parameter is required'}), 400
        
        # This would typically fetch from database or Git repository
        # For now, return example suppression rules
        example_suppressions = {
            "version": "1.0",
            "rules": {
                "test-files": {
                    "description": "Suppress security findings in test files",
                    "file_patterns": ["**/test/**", "**/tests/**", "**/*_test.py"],
                    "severities": ["low", "medium"]
                },
                "known-false-positives": {
                    "description": "Known false positive rules",
                    "rule_ids": ["CWE-79", "CWE-89"],
                    "file_patterns": ["**/legacy/**"]
                },
                "third-party-code": {
                    "description": "Third party dependencies",
                    "file_patterns": ["**/node_modules/**", "**/vendor/**"],
                    "scanners": ["codeql", "checkov"]
                }
            }
        }
        
        return jsonify({
            'success': True,
            'suppressions': example_suppressions
        })
    
    except Exception as e:
        logger.error(f"Failed to get suppressions: {e}")
        return jsonify({'error': 'Failed to get suppressions', 'details': str(e)}), 500

@advanced_scanning_bp.route('/suppressions', methods=['POST'])
@jwt_required()
def create_suppression():
    """
    Create new suppression rule
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['name', 'description', 'repository_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        suppression_rule = {
            'id': str(datetime.now().timestamp()),
            'name': data['name'],
            'description': data['description'],
            'repository_url': data['repository_url'],
            'rule_ids': data.get('rule_ids', []),
            'file_patterns': data.get('file_patterns', []),
            'severities': data.get('severities', []),
            'scanners': data.get('scanners', []),
            'created_by': user_id,
            'created_at': datetime.now(timezone.utc)
        }
        
        # Save to database
        db = get_db()
        rule_id = db.suppressions.insert_one(suppression_rule).inserted_id
        
        return jsonify({
            'success': True,
            'suppression_id': str(rule_id),
            'message': 'Suppression rule created successfully'
        })
    
    except Exception as e:
        logger.error(f"Failed to create suppression: {e}")
        return jsonify({'error': 'Failed to create suppression', 'details': str(e)}), 500

@advanced_scanning_bp.route('/scan/<scan_id>/findings', methods=['GET'])
@jwt_required()
def get_scan_findings():
    """
    Get findings for a specific scan
    """
    try:
        scan_id = request.view_args['scan_id']
        
        # Filter parameters
        severity = request.args.get('severity')
        scanner = request.args.get('scanner')
        scan_type = request.args.get('scan_type')
        suppressed = request.args.get('suppressed', 'false').lower() == 'true'
        
        db = get_db()
        report = db.reports.find_one({'results.scan_id': scan_id})
        
        if not report:
            return jsonify({'error': 'Scan not found'}), 404
        
        findings = report['results']['findings']
        
        # Apply filters
        filtered_findings = []
        for finding in findings:
            # Skip suppressed findings unless explicitly requested
            if finding.get('suppressed', False) and not suppressed:
                continue
            
            # Apply severity filter
            if severity and finding.get('severity') != severity:
                continue
            
            # Apply scanner filter
            if scanner and finding.get('source') != scanner:
                continue
            
            # Apply scan type filter
            if scan_type and finding.get('scan_type') != scan_type:
                continue
            
            filtered_findings.append(finding)
        
        return jsonify({
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
        })
    
    except Exception as e:
        logger.error(f"Failed to get scan findings: {e}")
        return jsonify({'error': 'Failed to get findings', 'details': str(e)}), 500

@advanced_scanning_bp.route('/scan/<scan_id>/summary', methods=['GET'])
@jwt_required()
def get_scan_summary():
    """
    Get summary for a specific scan
    """
    try:
        scan_id = request.view_args['scan_id']
        
        db = get_db()
        report = db.reports.find_one({'results.scan_id': scan_id})
        
        if not report:
            return jsonify({'error': 'Scan not found'}), 404
        
        results = report['results']
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'summary': results.get('summary', {}),
            'scanners': results.get('scanners', {}),
            'duration': results.get('duration', 0),
            'start_time': results.get('start_time'),
            'end_time': results.get('end_time')
        })
    
    except Exception as e:
        logger.error(f"Failed to get scan summary: {e}")
        return jsonify({'error': 'Failed to get summary', 'details': str(e)}), 500

@advanced_scanning_bp.route('/config', methods=['GET'])
@jwt_required()
def get_scanner_config():
    """
    Get current scanner configuration
    """
    try:
        engine = get_scanner_engine()
        config = engine.config
        
        return jsonify({
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
        })
    
    except Exception as e:
        logger.error(f"Failed to get scanner config: {e}")
        return jsonify({'error': 'Failed to get config', 'details': str(e)}), 500

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
