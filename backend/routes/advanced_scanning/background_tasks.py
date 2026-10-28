import asyncio
import logging
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional

import git

from database import db_manager
from utils.repo_clone import validate_repo_url
from utils.scrub import scrub_text
from utils.url_redaction import strip_url_credentials

logger = logging.getLogger(__name__)


async def start_comprehensive_scan_task(
    repository_url: str,
    target_url: Optional[str],
    scan_config: Dict,
    user_id: str
):
    temp_dir = None
    safe_repository_url = strip_url_credentials(repository_url)
    try:
        temp_dir = tempfile.mkdtemp(prefix='advanced_scan_')
        logger.info(
            "Cloning repository %s to %s",
            scrub_text(repository_url, limit=500),
            temp_dir,
        )
        validate_repo_url(repository_url)
        _repo = git.Repo.clone_from(repository_url, temp_dir)

        from .engine import get_scanner_engine
        engine = get_scanner_engine()
        if scan_config:
            from .engine import update_scanner_config
            update_scanner_config(engine.config, scan_config)

        logger.info(
            "Starting comprehensive scan for %s",
            scrub_text(repository_url, limit=500),
        )
        scan_results = await engine.scan_repository(temp_dir, target_url)

        report_data = {
            'scan_id': scan_results['scan_id'],
            'user_id': user_id,
            'repository_url': safe_repository_url,
            'target_url': target_url,
            'scan_type': 'comprehensive',
            'results': scan_results,
            'created_at': datetime.now(timezone.utc)
        }

        await db_manager.save_scan_report(report_data)
        logger.info(f"Comprehensive scan {scan_results['scan_id']} completed")

    except Exception as e:
        logger.error(
            "Background comprehensive scan failed: %s",
            scrub_text(str(e), limit=500),
        )
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {e}")


async def start_sast_scan_task(
    repository_url: str,
    languages: List[str],
    user_id: str
):
    temp_dir = None
    safe_repository_url = strip_url_credentials(repository_url)
    try:
        temp_dir = tempfile.mkdtemp(prefix='sast_scan_')
        validate_repo_url(repository_url)
        _repo = git.Repo.clone_from(repository_url, temp_dir)

        from .engine import generate_findings_summary, get_scanner_engine
        engine = get_scanner_engine()
        if languages:
            engine.config.sast_languages = languages

        scan_id = f"sast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        findings = await engine.codeql_scanner.scan(temp_dir, scan_id)

        for finding in findings:
            should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
            if should_suppress:
                finding.suppressed = True
                finding.suppression_reason = reason

        results = {
            'scan_id': scan_id,
            'scan_type': 'sast',
            'repository_url': safe_repository_url,
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
        logger.error(
            "Background SAST scan failed: %s",
            scrub_text(str(e), limit=500),
        )
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


async def start_dast_scan_task(target_url: str, user_id: str):
    try:
        from .engine import generate_findings_summary, get_scanner_engine
        engine = get_scanner_engine()
        scan_id = f"dast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        tasks = [
            engine.zap_scanner.scan(target_url, f"{scan_id}_zap"),
            engine.nuclei_scanner.scan(target_url, f"{scan_id}_nuclei")
        ]

        zap_findings, nuclei_findings = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings = []
        scanner_results = {}

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


async def start_iac_scan_task(
    repository_url: str,
    frameworks: List[str],
    user_id: str
):
    temp_dir = None
    safe_repository_url = strip_url_credentials(repository_url)
    try:
        temp_dir = tempfile.mkdtemp(prefix='iac_scan_')
        validate_repo_url(repository_url)
        _repo = git.Repo.clone_from(repository_url, temp_dir)

        from .engine import generate_findings_summary, get_scanner_engine
        engine = get_scanner_engine()
        if frameworks:
            engine.config.iac_frameworks = frameworks

        scan_id = f"iac_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        findings = await engine.checkov_scanner.scan(temp_dir, scan_id)

        for finding in findings:
            should_suppress, reason = engine.suppression_engine.should_suppress(finding, temp_dir)
            if should_suppress:
                finding.suppressed = True
                finding.suppression_reason = reason

        results = {
            'scan_id': scan_id,
            'scan_type': 'iac',
            'repository_url': safe_repository_url,
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
        logger.error(
            "Background IaC scan failed: %s",
            scrub_text(str(e), limit=500),
        )
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
