"""
DateTime Utilities for ONYX Platform
Provides timezone-aware datetime functions to replace deprecated datetime.utcnow()
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.
    
    This replaces the deprecated datetime.utcnow() which returns naive datetime.
    Python 3.12+ deprecates utcnow() in favor of timezone-aware alternatives.
    
    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def utc_timestamp() -> float:
    """
    Get current UTC timestamp.
    
    Returns:
        float: Unix timestamp in seconds
    """
    return datetime.now(timezone.utc).timestamp()


def utc_from_timestamp(ts: float) -> datetime:
    """
    Convert Unix timestamp to timezone-aware UTC datetime.
    
    Args:
        ts: Unix timestamp in seconds
        
    Returns:
        datetime: Timezone-aware UTC datetime
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def utc_isoformat() -> str:
    """
    Get current UTC time as ISO format string.
    
    Returns:
        str: ISO 8601 formatted datetime string
    """
    return datetime.now(timezone.utc).isoformat()


def add_timedelta(delta: timedelta, base: Optional[datetime] = None) -> datetime:
    """
    Add timedelta to a datetime (defaults to current UTC time).
    
    Args:
        delta: Time delta to add
        base: Base datetime (defaults to current UTC time)
        
    Returns:
        datetime: Resulting timezone-aware datetime
    """
    if base is None:
        base = utc_now()
    return base + delta


def subtract_timedelta(delta: timedelta, base: Optional[datetime] = None) -> datetime:
    """
    Subtract timedelta from a datetime (defaults to current UTC time).
    
    Args:
        delta: Time delta to subtract
        base: Base datetime (defaults to current UTC time)
        
    Returns:
        datetime: Resulting timezone-aware datetime
    """
    if base is None:
        base = utc_now()
    return base - delta
