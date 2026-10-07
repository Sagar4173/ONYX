"""Invocation tracing for every LLM gateway call."""
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InvocationTracer:
    """Records gateway invocations to an in-memory ring and ai_invocations."""

    def __init__(self, db: Optional[Any] = None, maxlen: int = 500):
        self._db = db
        self._ring: deque = deque(maxlen=maxlen)
        self._db_disabled = False

    def _resolve_db(self) -> Optional[Any]:
        if self._db_disabled or self._db is not None:
            return None if self._db_disabled else self._db
        try:
            from database import db_manager

            return db_manager.db
        except Exception:
            return None

    async def record(self, **entry) -> None:
        entry["ts"] = datetime.now(timezone.utc).isoformat()
        self._ring.append(entry)
        db = self._resolve_db()
        if db is not None:
            try:
                await db.ai_invocations.insert_one(dict(entry))
            except Exception as e:
                logger.debug("InvocationTracer insert failed (%s)", e)

    def recent(self) -> list:
        return list(self._ring)
