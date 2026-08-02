"""
DateTime Utilities for ONYX Platform
Provides timezone-aware datetime functions to replace deprecated datetime.utcnow()
"""
from datetime import datetime, timedelta, timezone
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


def ensure_utc(dt: datetime) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.

    MongoDB strips tzinfo on BSON round-trips, so datetimes loaded from the
    database come back naive. Attach UTC to naive values so mixed arithmetic
    (e.g. duration computation) never raises "can't subtract offset-naive and
    offset-aware datetimes".

    Args:
        dt: Datetime, possibly naive

    Returns:
        datetime: Timezone-aware UTC datetime
    """
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def elapsed_seconds(start: Optional[datetime], end: Optional[datetime]) -> Optional[float]:
    """
    Seconds between two datetimes, safe against naive/aware mixing and None.

    Args:
        start: Start datetime (possibly naive, possibly None)
        end: End datetime (possibly naive, possibly None)

    Returns:
        float: Elapsed seconds, or None when either side is missing
    """
    if start is None or end is None:
        return None
    return (ensure_utc(end) - ensure_utc(start)).total_seconds()


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
