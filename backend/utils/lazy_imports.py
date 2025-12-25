"""
Lazy Imports for Heavy Dependencies
====================================
Installs and imports scipy and docker on-demand to save memory on free-tier hosting.
These packages are only loaded when specific features are requested by users.
"""

import subprocess
import logging
import asyncio
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Global state
_scipy_installed = False
_scipy_installing = False
_scipy_module: Optional[Any] = None

_docker_installed = False
_docker_installing = False
_docker_module: Optional[Any] = None


async def get_scipy():
    """
    Get scipy module, installing if necessary.
    Returns scipy module or None if installation fails.
    
    Usage:
        scipy = await get_scipy()
        if scipy:
            result = scipy.stats.zscore(data)
    """
    global _scipy_installed, _scipy_installing, _scipy_module
    
    # Already loaded
    if _scipy_module is not None:
        return _scipy_module
    
    # Try importing if already installed
    if not _scipy_installed:
        try:
            import scipy
            _scipy_module = scipy
            _scipy_installed = True
            logger.info("✅ scipy already available")
            return _scipy_module
        except ImportError:
            pass
    
    # Already being installed
    if _scipy_installing:
        for _ in range(60):  # Wait up to 60 seconds
            await asyncio.sleep(1)
            if _scipy_module is not None:
                return _scipy_module
        return None
    
    # Install scipy
    _scipy_installing = True
    logger.info("📦 Installing scipy on-demand for advanced ML features...")
    
    try:
        process = await asyncio.create_subprocess_exec(
            "pip", "install", "--no-cache-dir", "scipy>=1.11.4",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            import scipy
            _scipy_module = scipy
            _scipy_installed = True
            logger.info("✅ scipy installed successfully")
            return _scipy_module
        else:
            logger.error(f"❌ Failed to install scipy: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error installing scipy: {e}")
        return None
    finally:
        _scipy_installing = False


async def get_docker():
    """
    Get docker module, installing if necessary.
    Returns docker module or None if installation fails.
    
    Usage:
        docker = await get_docker()
        if docker:
            client = docker.from_env()
    """
    global _docker_installed, _docker_installing, _docker_module
    
    # Already loaded
    if _docker_module is not None:
        return _docker_module
    
    # Try importing if already installed
    if not _docker_installed:
        try:
            import docker
            _docker_module = docker
            _docker_installed = True
            logger.info("✅ docker SDK already available")
            return _docker_module
        except ImportError:
            pass
    
    # Already being installed
    if _docker_installing:
        for _ in range(60):  # Wait up to 60 seconds
            await asyncio.sleep(1)
            if _docker_module is not None:
                return _docker_module
        return None
    
    # Install docker
    _docker_installing = True
    logger.info("📦 Installing docker SDK on-demand for container scanning...")
    
    try:
        process = await asyncio.create_subprocess_exec(
            "pip", "install", "--no-cache-dir", "docker>=7.0.0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            import docker
            _docker_module = docker
            _docker_installed = True
            logger.info("✅ docker SDK installed successfully")
            return _docker_module
        else:
            logger.error(f"❌ Failed to install docker: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error installing docker: {e}")
        return None
    finally:
        _docker_installing = False


def get_availability_status():
    """Get status of lazy-loaded packages"""
    return {
        "scipy": {
            "installed": _scipy_installed,
            "installing": _scipy_installing,
            "available": _scipy_module is not None
        },
        "docker": {
            "installed": _docker_installed,
            "installing": _docker_installing,
            "available": _docker_module is not None
        }
    }


# Synchronous versions for non-async contexts
def try_import_scipy():
    """
    Try to import scipy without installing.
    Returns scipy module or None.
    """
    global _scipy_module, _scipy_installed
    
    if _scipy_module is not None:
        return _scipy_module
    
    try:
        import scipy
        _scipy_module = scipy
        _scipy_installed = True
        return scipy
    except ImportError:
        return None


def try_import_docker():
    """
    Try to import docker without installing.
    Returns docker module or None.
    """
    global _docker_module, _docker_installed
    
    if _docker_module is not None:
        return _docker_module
    
    try:
        import docker
        _docker_module = docker
        _docker_installed = True
        return docker
    except ImportError:
        return None
