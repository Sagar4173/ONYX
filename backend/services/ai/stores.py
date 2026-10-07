"""Budget and cache stores for the LLM gateway.

Mongo-backed when a DB connection is available, in-memory otherwise.
All persistence failures degrade silently - these stores never raise.
"""
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from pymongo.errors import DuplicateKeyError

from config import settings

logger = logging.getLogger(__name__)


class _LazyStore:
    def __init__(self, db: Optional[Any] = None):
        self._db = db
        self._mem: dict = {}
        # Tests set this to force memory-only mode while a real DB may be connected.
        self._db_disabled: bool = False

    def _resolve_db(self) -> Optional[Any]:
        if self._db_disabled:
            return None
        if self._db is not None:
            return self._db
        try:
            from database import db_manager

            return db_manager.db
        except Exception:
            return None


class QuotaLedger(_LazyStore):
    """Daily per-provider request budget ($inc upserts in ai_quota_ledgers)."""

    def _key(self, provider: str) -> str:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{provider}:{day}"

    async def try_consume(self, provider: str) -> bool:
        key = self._key(provider)
        limit = settings.ai_rate_limit_rpd
        if self._mem.get(key, 0) >= limit:
            return False
        db = self._resolve_db()
        if db is not None:
            try:
                from pymongo import ReturnDocument

                doc = await db.ai_quota_ledgers.find_one_and_update(
                    {"_id": key, "count": {"$lt": limit}},
                    {"$inc": {"count": 1}, "$set": {"provider": provider}},
                    upsert=False,
                    return_document=ReturnDocument.AFTER,
                )
                if doc is not None:
                    # Filter guarantees count < limit before the increment,
                    # so the incremented count is within budget.
                    self._mem[key] = int(doc.get("count", 1))
                    return True
            except Exception as e:
                logger.debug("QuotaLedger mongo unavailable (%s); using memory", e)
            else:
                # Filter matched nothing: the doc is missing, or already at
                # the limit. Distinguish via insert (duplicate _id == at limit).
                try:
                    await db.ai_quota_ledgers.insert_one(
                        {"_id": key, "count": 1, "provider": provider}
                    )
                    self._mem[key] = self._mem.get(key, 0) + 1
                    return True
                except DuplicateKeyError:
                    self._mem[key] = max(self._mem.get(key, 0), limit)
                    return False
                except Exception as e:
                    logger.debug("QuotaLedger mongo insert failed (%s); using memory", e)
        self._mem[key] = self._mem.get(key, 0) + 1
        return self._mem[key] <= limit

    def remaining(self, provider: str) -> int:
        return max(0, settings.ai_rate_limit_rpd - self._mem.get(self._key(provider), 0))


class ResponseCache(_LazyStore):
    """SHA-256(prompt+settings) response cache with TTL (ai_response_cache)."""

    @staticmethod
    def make_key(
        *,
        purpose: str,
        messages: list,
        temperature: float,
        schema_name: str,
        chain: str,
        models: str = "",
        max_tokens: int = 0,
    ) -> str:
        payload = json.dumps(
            {
                "p": purpose,
                "m": messages,
                "t": temperature,
                "s": schema_name,
                "c": chain,
                "mm": models,
                "mt": max_tokens,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    async def get(self, key: str) -> Optional[dict]:
        now = time.time()
        mem = self._mem.get(key)
        if mem is not None:
            if mem["expires_at"] > now:
                return mem["value"]
            self._mem.pop(key, None)
        db = self._resolve_db()
        if db is not None:
            try:
                doc = await db.ai_response_cache.find_one(
                    {"_id": key, "expires_at": {"$gt": datetime.fromtimestamp(now, tz=timezone.utc)}}
                )
                if doc and doc.get("value") is not None:
                    expires = doc["expires_at"]
                    if getattr(expires, "tzinfo", None) is None:
                        # PyMongo returns naive datetimes unless tz_aware=True;
                        # interpret them as UTC so memory expiry matches Mongo.
                        expires = expires.replace(tzinfo=timezone.utc)
                    self._mem[key] = {
                        "value": doc["value"],
                        "expires_at": expires.timestamp() if hasattr(expires, "timestamp") else now + 60,
                    }
                    return doc["value"]
            except Exception as e:
                logger.debug("ResponseCache mongo unavailable (%s)", e)
        return None

    async def set(self, key: str, value: dict, ttl_days: Optional[int] = None) -> None:
        ttl = settings.ai_cache_ttl_days if ttl_days is None else ttl_days
        expires = time.time() + max(0, ttl) * 86400
        self._mem[key] = {"value": value, "expires_at": expires}
        db = self._resolve_db()
        if db is not None:
            try:
                await db.ai_response_cache.update_one(
                    {"_id": key},
                    {
                        "$set": {
                            "value": value,
                            "expires_at": datetime.fromtimestamp(expires, tz=timezone.utc),
                        }
                    },
                    upsert=True,
                )
            except Exception as e:
                logger.debug("ResponseCache mongo write failed (%s)", e)
